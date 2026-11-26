"""Contratos de ciclo de vida, precisão monetária e consistência após interrupção."""
import json
import unittest
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path
from secrets import token_urlsafe
from tempfile import TemporaryDirectory
from threading import Barrier
from unittest.mock import patch

from controller.controller import Controller
from persistence import historico_json
from service.estacionamento_service import ErroDeInfraestrutura, EstacionamentoService
from web import create_app
from web.eventos import RelatorioSaidas, eventos_identificados


class QualidadeTests(unittest.TestCase):
    def setUp(self):
        self.pasta = Path(self.enterContext(TemporaryDirectory()))
        self.arquivo = self.pasta / 'historico.json'
        self.config = dict(TESTING=True, DADOS=self.pasta, HISTORICO=self.arquivo,
                           CONTAS=self.pasta / 'contas.json')

    def test_total_legado_concorda_com_as_saidas_individuais_do_relatorio(self):
        ctrl = Controller(self.arquivo)
        ctrl.cadastrar_veiculo('carro', 'QA1', 'Modelo')
        for horas in (0.01, 0.02):
            ctrl.estacionar_cadastrado('QA1', 1)
            ctrl.retirar_veiculo(1, horas)
        ctrl.salvar()
        servico = EstacionamentoService(self.arquivo)
        eventos = eventos_identificados(servico.consultar_historico())
        receita = RelatorioSaidas.do_periodo(eventos).receita
        self.assertEqual(receita, Decimal('0.30'))
        total = servico.consultar_faturamento()
        self.assertEqual(Decimal(total['reais']), receita)
        self.assertEqual(total['centavos'], 30)

    def test_geracao_da_sessao_muda_ao_alternar_e_termina_no_logout(self):
        app = create_app(self.config)
        self.addCleanup(app.extensions['escritor'].fechar)
        auth = app.extensions['autenticacao']
        chave = token_urlsafe()
        titular = app.extensions['estacionamento'].cadastrar_cliente('vip', 'Titular QA')
        adm = auth.provisionar('operador.qa', chave, 'gestao')
        pessoal = auth.provisionar('titular.qa', chave, 'cliente', titular['identificador'])
        app.config['VINCULOS_PORTAIS'] = {adm.id: pessoal.id}
        http = app.test_client()

        def token():
            with http.session_transaction() as sessao:
                return sessao['csrf']

        http.get('/entrar')
        self.assertEqual(http.post('/entrar', data=dict(usuario=adm.usuario, senha=chave,
                                                        csrf_token=token())).status_code, 303)
        sessoes = app.extensions['sessoes']
        inicial = token()
        self.assertTrue(sessoes.ativa(inicial))
        self.assertEqual(http.post('/ambiente', data=dict(ambiente='cliente', csrf_token=inicial)).status_code, 303)
        pessoal = token()
        self.assertFalse(sessoes.ativa(inicial))
        self.assertTrue(sessoes.ativa(pessoal))
        self.assertEqual(http.post('/sair', data=dict(csrf_token=pessoal)).status_code, 303)
        self.assertFalse(sessoes.ativa(pessoal))

    def test_retomada_simultanea_ativa_a_mesma_reserva_uma_unica_vez(self):
        app = create_app(self.config)
        auth = app.extensions['autenticacao']
        servico = app.extensions['estacionamento']
        senha = token_urlsafe()
        with patch.object(auth.contas, 'ativar', side_effect=ErroDeInfraestrutura()), self.assertRaises(ErroDeInfraestrutura):
            auth.cadastrar_pessoal('Cliente QA', 'qa', senha, senha)
        reserva = auth.contas.por_usuario('qa')
        self.assertIsNone(auth.autenticar('qa', 'incorreta'))
        original = servico.confirmar_cadastro_pessoal
        barreira = Barrier(2, timeout=10)

        def confirmar(cliente):
            barreira.wait()
            original(cliente)

        with patch.object(servico, 'confirmar_cadastro_pessoal', side_effect=confirmar), ThreadPoolExecutor(2) as grupo:
            resultados = list(grupo.map(lambda _: auth.autenticar('qa', senha), range(2)))
        self.assertEqual(resultados, [reserva.identidade] * 2)
        self.assertEqual(len(servico.listar_clientes()), 1)
        self.assertEqual(len(json.loads(self.config['CONTAS'].read_bytes())), 1)
        self.assertIsNone(auth.contas.por_usuario('qa').nome_pendente)

    def test_fsync_falha_preserva_versao_original_e_remove_temporario(self):
        original = historico_json.salvar(self.arquivo, [])
        with patch('persistence.historico_json.os.fsync', side_effect=OSError('falha de E/S')):
            with self.assertRaises(historico_json.FalhaAntesDaSubstituicao):
                historico_json.salvar(self.arquivo, [{'acao': 'cadastro'}], original)
        self.assertEqual(self.arquivo.read_bytes(), original)
        self.assertEqual(list(self.pasta.glob('*.tmp')), [])

    def test_geracoes_independentes_expiram_e_a_troca_tem_um_vencedor(self):
        from web.sessoes import SessoesAtivas
        arquivo = self.pasta / 'sessoes.json'
        registro = SessoesAtivas(arquivo)
        with patch('web.sessoes.time', return_value=100):
            registro.substituir(nova='um', expira=110)
            registro.substituir(nova='dois', expira=120)
            barreira = Barrier(2, timeout=10)

            def trocar(nova):
                barreira.wait()
                return SessoesAtivas(arquivo).substituir('um', nova, 110)

            with ThreadPoolExecutor(2) as grupo:
                resultados = list(grupo.map(trocar, ['tres', 'quatro']))
            self.assertCountEqual(resultados, [True, False])
            self.assertEqual(sum(registro.ativa(k) for k in ('um', 'tres', 'quatro')), 1)
            self.assertTrue(registro.ativa('dois'))
        with patch('web.sessoes.time', return_value=110):
            self.assertFalse(any(registro.ativa(k) for k in ('um', 'tres', 'quatro')))
            self.assertTrue(registro.ativa('dois'))
        arquivo.write_bytes(b'{')
        with self.assertRaises(ErroDeInfraestrutura):
            registro.substituir(nova='cinco', expira=200)
        self.assertEqual(arquivo.read_bytes(), b'{')

    def test_nove_combinacoes_com_oraculo_decimal_nas_fronteiras(self):
        from decimal import ROUND_HALF_UP, localcontext
        from model.caminhao import Caminhao
        from model.carro import Carro
        from model.cliente_comum import ClienteComum
        from model.cliente_mensalista import ClienteMensalista
        from model.cliente_vip import ClienteVIP
        from model.estadia import Estadia
        from model.moto import Moto
        from model.vaga import Vaga
        from view.formatacao import dinheiro
        with localcontext(prec=100):
            for tipo, taxa in [(Moto, 5), (Carro, 10), (Caminhao, 20)]:
                for cliente, fator in [(ClienteComum, 1), (ClienteVIP, Decimal('.5')), (ClienteMensalista, 0)]:
                    estadia = Estadia(8, tipo('QA', 'Modelo'), cliente('Cliente'), Vaga(1), '2026-01-01T00:00:00Z')
                    for texto in ('0', '0.00049', '0.0005', '0.00051', '0.001', '1.225', '2.50E+3',
                                  '123456789012345678901234567890.12345', '1e-80'):
                        with self.subTest(tipo=tipo.__name__, categoria=cliente.__name__, horas=texto):
                            horas = Decimal(texto)
                            base = taxa * horas
                            final = (base * fator).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
                            c = estadia.consultar_cobranca(horas)
                            self.assertEqual((c.tarifa_base, c.desconto, c.valor_centavos),
                                             (base, base * (1 - fator), int(final * 100)))
                            self.assertRegex(dinheiro(c.valor_devido), r',\d{2}$')

    def test_reserva_divergente_continua_pendente_sem_substituir_cliente(self):
        from model.cliente_comum import ClienteComum
        app = create_app(self.config)
        auth = app.extensions['autenticacao']
        srv = app.extensions['estacionamento']
        senha = token_urlsafe()
        with patch.object(srv, 'confirmar_cadastro_pessoal', side_effect=ErroDeInfraestrutura()), self.assertRaises(ErroDeInfraestrutura):
            auth.cadastrar_pessoal('Titular QA', 'reserva', senha, senha)
        reserva = auth.contas.por_usuario('reserva')
        outro = ClienteComum('Outro titular', identificador=reserva.identidade.cliente_id)
        srv.confirmar_cadastro_pessoal(outro)
        antes = self.arquivo.read_bytes()
        with self.assertRaises(ErroDeInfraestrutura):
            auth.autenticar('reserva', senha)
        self.assertEqual(self.arquivo.read_bytes(), antes)
        self.assertEqual(auth.contas.por_usuario('reserva'), reserva)
        self.assertIsNone(auth.contas.por_id(reserva.identidade.id))

    def test_termux_falha_do_abridor_mantem_url_manual(self):
        import subprocess
        from web.__main__ import abrir_navegador
        prefixo = self.pasta / 'usr'
        auxiliar = prefixo / 'bin' / 'termux-open-url'
        auxiliar.parent.mkdir(parents=True)
        auxiliar.touch()
        with patch('web.__main__.prefixo_termux', return_value=prefixo), patch('subprocess.run',
                return_value=subprocess.CompletedProcess([], 1)) as invocar, patch('builtins.print') as aviso:
            abrir_navegador('http://127.0.0.1:5051/entrar')
        self.assertEqual(invocar.call_count, 1)
        self.assertIn('Android', aviso.call_args.args[0])
