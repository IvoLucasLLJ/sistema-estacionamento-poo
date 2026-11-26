import json
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier, Event
from unittest.mock import patch

from controller.controller import Controller
from service.estacionamento_service import (
    ConflitoDeHistorico, ErroDeInfraestrutura, ErroDeNegocio,
    EstacionamentoService, ResultadoIncerto,
)


class AmbienteTemporario(unittest.TestCase):
    def setUp(self):
        self.pasta = Path(self.enterContext(TemporaryDirectory()))
        self.arquivo = self.pasta / 'historico.json'
        self.servico = self.reabrir()

    def reabrir(self):
        return EstacionamentoService(self.arquivo)

    def vincular(self, placa='CAR1', categoria='vip'):
        cliente = self.servico.cadastrar_cliente(categoria, 'Pessoa fictícia')
        self.servico.cadastrar_veiculo('carro', placa, 'Modelo')
        self.servico.vincular_veiculo(placa, cliente['identificador'])
        return cliente['identificador']

    def entrar(self, categoria='vip'):
        cliente_id = self.vincular(categoria=categoria)
        return self.servico.iniciar_estadia('CAR1', 1, cliente_id)

    def pagar(self, consulta):
        return self.servico.confirmar_pagamento('CAR1', consulta['horas'], consulta, confirmado=True)


class ServiceTests(AmbienteTemporario):
    def test_cada_escrita_recuperavel_e_consultas_sem_gravar(self):
        s = self.servico
        self.assertEqual(s.consultar_ocupacao(), {'total': 200, 'livres': 200, 'ocupadas': 0})
        self.assertFalse(self.arquivo.exists())
        cliente = s.cadastrar_cliente('vip', ' Bia ')
        chave = cliente['identificador']
        self.assertEqual(self.reabrir().buscar_cliente(chave), cliente)
        carro = s.cadastrar_veiculo('carro', ' car-1 ', 'Modelo')
        self.assertEqual(self.reabrir().buscar_veiculo('car-1'), carro)
        self.assertEqual(self.reabrir().listar_veiculos(), [carro])
        self.assertIsNone(s.cliente_do_veiculo('CAR1'))
        s.vincular_veiculo('CAR1', chave)
        self.assertEqual(self.reabrir().veiculos_do_cliente(chave), [carro])
        self.assertEqual(s.cliente_do_veiculo('CAR1'), cliente)
        entrada = s.iniciar_estadia('car1', 10, chave)
        eid = entrada['estadia_id']
        self.assertEqual(self.reabrir().consultar_estadia(eid), entrada)
        self.assertEqual(s.listar_estadias_ativas(), [entrada])
        self.assertEqual(s.consultar_vagas()[9], dict(numero=10, ocupada=True, placa='CAR1', estado='ocupada',
                                                   setor=1, classificacao='comum', vip=False, carregador=None))
        self.assertEqual(len(s.consultar_vagas()), 200)
        antes = self.arquivo.read_bytes()
        c = s.consultar_cobranca('CAR1', '1.225')
        self.assertEqual(c['valor_centavos'], 613)
        self.assertEqual(Decimal(c['tarifa_base']), Decimal('12.25'))
        self.assertEqual(Decimal(c['desconto']), Decimal('6.125'))
        self.assertIsNone(s.consultar_pagamento('CAR1'))
        self.assertEqual(self.arquivo.read_bytes(), antes)
        self.assertEqual(self.pagar(c), c)
        self.assertEqual(self.reabrir().consultar_pagamento('CAR1'), c)
        self.assertEqual(s.listar_pagamentos_abertos(), [c])
        self.assertEqual(s.consultar_faturamento()['centavos'], 0)
        saida = s.concluir_saida('CAR1', '1.225', c)
        self.assertEqual(saida['situacao'], 'concluida')
        self.assertEqual(saida['pagamento'], 'confirmado')
        self.assertEqual(self.reabrir().consultar_estadia(eid), saida)
        self.assertEqual(s.listar_pagamentos_abertos(), [])
        self.assertEqual(s.listar_estadias_ativas(), [])
        self.assertEqual(s.consultar_faturamento(), {'reais': '6.13', 'centavos': 613})
        self.assertEqual(len(s.consultar_historico()), 6)

    def test_representacoes_sao_json_e_alteracoes_ficam_com_o_chamador(self):
        entrada = self.entrar()
        c = self.servico.consultar_cobranca('CAR1', '0.12345678901234567890123456789')
        self.pagar(c)
        antes = self.arquivo.read_bytes()
        s = self.servico
        for consultar in (s.listar_clientes, s.listar_veiculos, s.consultar_vagas,
                          s.listar_estadias_ativas, s.listar_pagamentos_abertos, s.consultar_historico):
            dados = consultar()
            copia = json.loads(json.dumps(dados, allow_nan=False))
            dados[0].clear()
            dados.clear()
            self.assertEqual(consultar(), copia)
        self.assertEqual(s.consultar_estadia(entrada['estadia_id'])['situacao'], 'ativa')
        self.assertEqual(c['tarifa_base'], '1.23456789012345678901234567890')
        self.assertEqual(self.arquivo.read_bytes(), antes)

    def test_rejeita_expectativa_adulterada_duracao_divergente_e_cancelamento(self):
        self.entrar()
        s = self.servico
        c = s.consultar_cobranca('CAR1', '1.225')
        antes = self.arquivo.read_bytes()
        for campo, dado in [('estadia_id', True), ('estadia_id', 95), ('placa', 'OUTRA'),
                            ('valor_centavos', 612), ('valor_centavos', 613.0),
                            ('horas', '1.2251'), ('tarifa_base', '1'), ('desconto', '12.25')]:
            with self.subTest(campo=campo, dado=dado), self.assertRaises(ErroDeNegocio):
                s.confirmar_pagamento('CAR1', '1.225', {**c, campo: dado}, confirmado=True)
        for horas in ('1.2251', 'invalido', None, True, 'NaN', '-1', 'Infinity'):
            with self.subTest(horas=horas), self.assertRaises(ErroDeNegocio):
                s.confirmar_pagamento('CAR1', horas, c, confirmado=True)
        with self.assertRaises(ErroDeNegocio):
            s.confirmar_pagamento('CAR1', '1.225', c, confirmado=False)
        with self.assertRaises(ErroDeNegocio):
            s.concluir_saida('CAR1', '1.225', c)
        self.assertEqual(self.arquivo.read_bytes(), antes)

    def test_cotacao_anterior_invalida_em_nova_estadia_da_mesma_placa(self):
        primeira = self.entrar()
        s = self.servico
        velha = s.consultar_cobranca('CAR1', 2)
        self.pagar(velha)
        s.concluir_saida('CAR1', 2, velha)
        segunda = s.iniciar_estadia('CAR1', 1, primeira['cliente_id'])
        self.assertNotEqual(segunda['estadia_id'], velha['estadia_id'])
        with self.assertRaises(ErroDeNegocio):
            self.pagar(velha)
        atual = s.consultar_cobranca('CAR1', 2)
        self.pagar(atual)
        with self.assertRaises(ErroDeNegocio):
            s.concluir_saida('CAR1', 2, velha)
        self.assertEqual(s.listar_pagamentos_abertos(), [atual])
        self.assertEqual(s.consultar_ocupacao()['ocupadas'], 1)

    def test_saida_isenta_recuperada_sem_pagamento(self):
        self.entrar('mensalista')
        c = self.servico.consultar_cobranca('CAR1', '2.5')
        with self.assertRaises(ErroDeNegocio):
            self.pagar(c)
        saida = self.servico.concluir_saida('CAR1', '2.5', c)
        self.assertEqual(saida['pagamento'], 'isento')
        self.assertEqual(self.reabrir().consultar_estadia(c['estadia_id']), saida)
        self.assertEqual(self.servico.consultar_faturamento()['centavos'], 0)
        self.assertNotIn('pagamento_confirmado', [e['acao'] for e in self.servico.consultar_historico()])

    def test_historico_legado_e_misto_com_fracao_de_centavo(self):
        inicio = '2026-01-01T10:00:00'
        entrada = dict(acao='entrada', tipo='moto', placa='LEG1', vaga=2, horario_entrada=inicio)
        saida = dict(entrada, acao='saida', horas=0.001, valor=0.005, horario_saida=inicio)
        eventos = [entrada, saida, entrada]
        self.arquivo.write_text(json.dumps(eventos))
        s = self.servico
        legado, = s.listar_estadias_ativas()
        self.assertEqual((legado['estadia_id'], legado['cliente_id'], legado['horario_entrada']),
                         (None, None, inicio))
        self.assertEqual(s.consultar_faturamento(), {'centavos': None, 'reais': '0.005'})
        self.entrar()
        c = s.consultar_cobranca('CAR1', 2)
        self.pagar(c)
        s.concluir_saida('CAR1', 2, c)
        self.assertEqual(self.reabrir().consultar_faturamento(), {'centavos': None, 'reais': '10.005'})
        self.assertEqual(s.consultar_historico()[1]['valor'], '0.005')
        self.assertEqual(json.loads(self.arquivo.read_bytes())[:3], eventos)

    def test_historico_invalido_separado_de_rejeicao_de_negocio(self):
        for original in (b'{', b'[{"acao":"inexistente"}]'):
            with self.subTest(original=original):
                self.arquivo.write_bytes(original)
                with self.assertRaises(ErroDeInfraestrutura):
                    self.servico.cadastrar_cliente('vip', 'Fictício')
                self.assertEqual(self.arquivo.read_bytes(), original)
        self.arquivo.unlink()
        with self.assertRaises(ErroDeNegocio):
            self.servico.cadastrar_cliente('inexistente', 'Fictício')
        self.assertFalse(self.arquivo.exists())

    def test_metadados_extras_legados_nao_identificam_estadia_nem_cliente(self):
        evento = dict(acao='entrada', tipo='moto', placa='LEG1', vaga=2,
                      horario_entrada='2026-01-01T10:00:00', cliente_id='antigo',
                      categoria='vip', estadia_id=1)
        self.arquivo.write_text(json.dumps([evento]))
        legado, = self.servico.listar_estadias_ativas()
        for chave in ('cliente_id', 'categoria', 'estadia_id'):
            self.assertIsNone(legado[chave])
        with self.assertRaises(ErroDeNegocio):
            self.servico.consultar_estadia(1)
        self.assertEqual(self.servico.consultar_historico(), [evento])

    def test_falha_anterior_ao_replace_preserva_bytes_e_permite_nova_operacao(self):
        self.entrar()
        s = self.servico
        c = s.consultar_cobranca('CAR1', 2)
        antes = self.arquivo.read_bytes()
        with patch('os.fsync', side_effect=OSError('disco cheio')):
            with self.assertRaises(ErroDeInfraestrutura) as falha:
                self.pagar(c)
        self.assertNotIsInstance(falha.exception, ResultadoIncerto)
        self.assertEqual(self.arquivo.read_bytes(), antes)
        self.assertEqual(list(self.pasta.iterdir()), [self.arquivo])
        self.assertIsNone(self.reabrir().consultar_pagamento('CAR1'))
        self.assertEqual(self.pagar(c), c)

    def test_conflito_externo_preserva_os_bytes_do_outro_escritor(self):
        s = self.servico
        s.cadastrar_cliente('vip', 'Bia')
        externo = self.arquivo.read_bytes() + b'\n'
        salvar = Controller.salvar

        def alterar_antes_de_salvar(ctrl):
            self.arquivo.write_bytes(externo)
            salvar(ctrl)

        with patch.object(Controller, 'salvar', alterar_antes_de_salvar):
            with self.assertRaises(ConflitoDeHistorico):
                s.cadastrar_veiculo('moto', 'M1', 'M')
        self.assertEqual(self.arquivo.read_bytes(), externo)
        self.assertEqual(s.listar_veiculos(), [])
        s.cadastrar_veiculo('moto', 'M1', 'M')

    def test_falha_no_temporario_tem_resultado_conhecido_mesmo_sem_releitura(self):
        self.entrar()
        c = self.servico.consultar_cobranca('CAR1', 2)
        antes = self.arquivo.read_bytes()

        def falhar_antes_do_replace(fd):
            # O volume fica indisponível para as leituras seguintes à falha de fsync.
            self.enterContext(patch('persistence.historico_json.abrir_leitura', side_effect=OSError('volume indisponível')))
            raise OSError('falha ao sincronizar o temporário')

        with patch('os.fsync', falhar_antes_do_replace), patch('os.replace') as substituir:
            with self.assertRaises(ErroDeInfraestrutura) as falha:
                self.pagar(c)
        self.assertNotIsInstance(falha.exception, ResultadoIncerto)
        substituir.assert_not_called()
        with self.arquivo.open('rb') as arquivo:
            self.assertEqual(arquivo.read(), antes)

    def test_releitura_invalida_ou_divergente_nao_autoriza_repeticao(self):
        self.entrar()
        c = self.servico.consultar_cobranca('CAR1', 2)
        antes = self.arquivo.read_bytes()
        for conteudo, situacao in ((b'{', 'releitura_indisponivel'), (b'[]', 'historico_divergente')):
            def falhar(ctrl):
                self.arquivo.write_bytes(conteudo)
                raise OSError('falha durante a tentativa de gravação')

            with self.subTest(situacao=situacao), patch.object(Controller, 'salvar', autospec=True,
                                                               side_effect=falhar) as salvar:
                with self.assertRaises(ResultadoIncerto) as falha:
                    self.pagar(c)
                salvar.assert_called_once()
                self.assertEqual(falha.exception.verificacao, situacao)
                self.assertEqual(self.arquivo.read_bytes(), conteudo)
            self.arquivo.write_bytes(antes)

    def test_falha_de_confirmacao_apos_replace_reconsulta_sem_repetir(self):
        self.entrar()
        c = self.servico.consultar_cobranca('CAR1', 2)
        substituir = os.replace

        def substituir_e_falhar(origem, destino):
            substituir(origem, destino)
            raise OSError('resposta perdida')

        with patch('os.replace', side_effect=substituir_e_falhar) as tentativas:
            with self.assertRaises(ResultadoIncerto) as falha:
                self.pagar(c)
        self.assertEqual(falha.exception.verificacao, 'operacao_presente')
        self.assertEqual(tentativas.call_count, 1)
        self.assertEqual(self.reabrir().listar_pagamentos_abertos(), [c])
        self.assertEqual(self.servico.consultar_faturamento()['centavos'], 0)
        self.servico.concluir_saida('CAR1', 2, c)
        self.assertEqual(self.servico.consultar_faturamento()['centavos'], 1000)

    def test_falha_ao_devolver_saida_ja_salva_preserva_faturamento_unico(self):
        self.entrar()
        c = self.servico.consultar_cobranca('CAR1', 2)
        self.pagar(c)
        salvar = Controller.salvar

        def perder_confirmacao(ctrl):
            salvar(ctrl)
            raise RuntimeError('perda da confirmação depois de retornar do Repository')

        with patch.object(Controller, 'salvar', perder_confirmacao), self.assertRaises(ResultadoIncerto) as falha:
            self.servico.concluir_saida('CAR1', 2, c)
        self.assertEqual(falha.exception.verificacao, 'operacao_presente')
        outro = self.reabrir()
        self.assertEqual(outro.consultar_estadia(c['estadia_id'])['situacao'], 'concluida')
        with self.assertRaises(ErroDeNegocio):
            outro.concluir_saida('CAR1', 2, c)
        self.assertEqual(outro.consultar_faturamento()['centavos'], 1000)


class ConcorrenciaTests(AmbienteTemporario):
    def disputar(self, *operacoes):
        # Cada participante abre seu próprio serviço. Os dois caminhos denotam o mesmo JSON.
        inicio = Barrier(len(operacoes), timeout=5)
        alias = self.pasta / 'alias.json'
        if os.name == 'nt':
            subpasta = self.pasta / 'subpasta'
            subpasta.mkdir(exist_ok=True)
            alias = subpasta / '..' / self.arquivo.name
        elif not alias.is_symlink():
            alias.symlink_to(self.arquivo)

        def executar(indice, operacao):
            s = EstacionamentoService(alias if indice % 2 else self.arquivo)
            inicio.wait()
            try:
                return operacao(s)
            except ErroDeNegocio:
                return None

        with ThreadPoolExecutor(len(operacoes)) as grupo:
            futuros = [grupo.submit(executar, i, op) for i, op in enumerate(operacoes)]
            return [f.result(timeout=10) for f in futuros]

    def test_entradas_disputam_mesma_vaga(self):
        a, b = self.vincular('A'), self.vincular('B')
        resultados = self.disputar(lambda s: s.iniciar_estadia('A', 1, a),
                                   lambda s: s.iniciar_estadia('B', 1, b))
        self.assertEqual(resultados.count(None), 1)
        self.assertEqual(self.reabrir().consultar_ocupacao()['ocupadas'], 1)

    def test_mesma_placa_em_vagas_distintas(self):
        a = self.vincular('A')
        resultados = self.disputar(lambda s: s.iniciar_estadia('A', 1, a),
                                   lambda s: s.iniciar_estadia(' a ', 2, a))
        self.assertEqual(resultados.count(None), 1)
        self.assertEqual(len(self.servico.listar_estadias_ativas()), 1)

    def test_cadastros_e_vinculos_simultaneos(self):
        def cadastrar(s):
            cliente = s.cadastrar_cliente('comum', 'Homônimo')
            placa = cliente['identificador'].replace('-', '')
            s.cadastrar_veiculo('moto', placa, 'Modelo')
            s.vincular_veiculo(placa, cliente['identificador'])
            return cliente['identificador']

        ids = self.disputar(*([cadastrar] * 6))
        self.assertEqual(len(set(ids)), 6)
        self.assertEqual(set(ids), {c['identificador'] for c in self.servico.listar_clientes()})
        self.assertEqual(len(self.servico.listar_veiculos()), 6)
        for chave in ids:
            self.assertEqual(len(self.servico.veiculos_do_cliente(chave)), 1)

    def test_entradas_em_vagas_distintas_preservadas(self):
        a, b = self.vincular('A'), self.vincular('B')
        resultados = self.disputar(lambda s: s.iniciar_estadia('A', 1, a),
                                   lambda s: s.iniciar_estadia('B', 2, b))
        self.assertNotIn(None, resultados)
        self.assertEqual(self.reabrir().listar_estadias_ativas(), resultados)

    def test_pagamentos_e_saidas_disputados_uma_vez(self):
        self.entrar()
        c = self.servico.consultar_cobranca('CAR1', 2)

        def pagar(s):
            return s.confirmar_pagamento('CAR1', 2, c, confirmado=True)

        def sair(s):
            return s.concluir_saida('CAR1', 2, c)

        self.assertEqual(self.disputar(pagar, pagar).count(None), 1)
        self.assertEqual(self.servico.listar_pagamentos_abertos(), [c])
        self.assertEqual(self.disputar(sair, sair).count(None), 1)
        self.assertEqual(self.reabrir().consultar_faturamento()['centavos'], 1000)
        acoes = [e['acao'] for e in self.servico.consultar_historico()]
        self.assertEqual((acoes.count('pagamento_confirmado'), acoes.count('saida_cliente')), (1, 1))

    def test_consulta_iniciada_durante_gravacao_le_o_estado_confirmado(self):
        a = self.vincular('A')
        no_salvamento, leitor_no_bloqueio = Event(), Event()
        salvar = Controller.salvar
        leitor = self.reabrir()
        bloqueio = leitor._bloqueio

        class BloqueioObservado:
            def __enter__(self):
                leitor_no_bloqueio.set()
                return bloqueio.__enter__()

            def __exit__(self, *erro):
                return bloqueio.__exit__(*erro)

        def salvar_com_leitor(ctrl):
            no_salvamento.set()
            self.assertTrue(leitor_no_bloqueio.wait(5))
            salvar(ctrl)

        def ler():
            self.assertTrue(no_salvamento.wait(5))
            return leitor.consultar_ocupacao()

        with (patch.object(leitor, '_bloqueio', BloqueioObservado()),
              patch.object(Controller, 'salvar', salvar_com_leitor), ThreadPoolExecutor(2) as grupo):
            escritor = grupo.submit(self.servico.iniciar_estadia, 'A', 1, a)
            consulta = grupo.submit(ler)
            escritor.result(timeout=10)
            self.assertEqual(consulta.result(timeout=10)['ocupadas'], 1)

    def test_arquivos_distintos_podem_gravar_em_paralelo(self):
        juntos_na_gravacao = Barrier(2, timeout=5)
        salvar = Controller.salvar

        def salvar_em_paralelo(ctrl):
            juntos_na_gravacao.wait()
            salvar(ctrl)

        outro = EstacionamentoService(self.pasta / 'segundo.json')
        with patch.object(Controller, 'salvar', salvar_em_paralelo), ThreadPoolExecutor(2) as grupo:
            a = grupo.submit(self.servico.cadastrar_cliente, 'vip', 'A')
            b = grupo.submit(outro.cadastrar_cliente, 'comum', 'B')
            self.assertEqual(a.result(timeout=10)['nome'], 'A')
            self.assertEqual(b.result(timeout=10)['nome'], 'B')
        self.assertEqual([c['nome'] for c in self.servico.listar_clientes()], ['A'])
        self.assertEqual([c['nome'] for c in outro.listar_clientes()], ['B'])
