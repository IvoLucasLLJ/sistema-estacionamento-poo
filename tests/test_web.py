import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier
from unittest import TestCase
from unittest.mock import patch
from uuid import uuid4

from service.estacionamento_service import ConflitoDeHistorico, ErroDeInfraestrutura, ResultadoIncerto
from web import create_app
from web.contas import PapelAcesso
from web.apresentacao import OcupacaoViewModel, centavos, dinheiro, horario


class WebTests(TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.pasta = Path(tmp.name)
        self.cfg = dict(TESTING=True, DADOS=self.pasta, HISTORICO=self.pasta / 'historico.json',
                        CONTAS=self.pasta / 'contas.json', SECRET_KEY=None, SESSION_COOKIE_SECURE=False)
        self.app = create_app(self.cfg)
        self.addCleanup(self.app.extensions['escritor'].fechar)
        self.http = self.app.test_client()
        self.auth = self.app.extensions['autenticacao']
        self.srv = self.app.extensions['estacionamento']
        self.titular = self.srv.cadastrar_cliente('vip', 'Lia <Vale>')
        self.outro = self.srv.cadastrar_cliente('mensalista', 'Outro Titular')
        self.senha = uuid4().hex
        self.admin = self.auth.provisionar('operador', self.senha, PapelAcesso.GESTAO)
        self.pessoal = self.auth.provisionar('lia', self.senha, PapelAcesso.CLIENTE,
                                             self.titular['identificador'])

    def token(self, caminho='/entrar'):
        pag = self.http.get(caminho)
        return re.search(rb'name="csrf_token" value="([^"]+)"', pag.data)[1].decode()

    def login(self, nome='lia', senha=None, **extra):
        token = self.token()
        return self.http.post('/entrar', data=dict(usuario=nome, senha=senha or self.senha,
                                                   csrf_token=token, **extra))

    def test_contas_atomicamente_separadas_e_recuperaveis(self):
        contas = self.pasta / 'contas.json'
        gravado = contas.read_text(encoding='utf-8')
        self.assertNotIn(self.senha, gravado)
        self.assertIn('scrypt:', gravado)
        self.assertNotIn('scrypt:', self.cfg['HISTORICO'].read_text(encoding='utf-8'))
        if os.name == 'nt':
            from persistence.privacidade import conferir_acl
            conferir_acl(contas)
        else:
            self.assertEqual(contas.stat().st_mode & 0o777, 0o600)
        nova = create_app(self.cfg)
        self.assertEqual(nova.extensions['autenticacao'].autenticar('LIA', self.senha), self.pessoal)
        self.assertFalse(hasattr(self.pessoal, 'senha_hash'))

    def test_unicidade_usuario_e_cliente(self):
        for nome, papel, cliente in [('OPERADOR', PapelAcesso.GESTAO, None),
                                      ('segunda', PapelAcesso.CLIENTE, self.titular['identificador'])]:
            with self.subTest(nome=nome), self.assertRaises(ValueError):
                self.auth.provisionar(nome, self.senha, papel, cliente)

    def test_associacao_inexistente_ou_incompativel(self):
        for papel, cliente in [(PapelAcesso.CLIENTE, str(uuid4())), (PapelAcesso.CLIENTE, None),
                               (PapelAcesso.GESTAO, self.titular['identificador'])]:
            with self.subTest(papel=papel), self.assertRaises(ValueError):
                self.auth.provisionar('teste', self.senha, papel, cliente)

    def test_corrupcao_nao_publica_nem_sobrescreve(self):
        dest = self.pasta / 'contas.json'
        for conteudo in [b'{', b'{}', b'[{}]']:
            dest.write_bytes(conteudo)
            self.assertEqual(self.login('operador').status_code, 503)
            with self.assertRaises(ErroDeInfraestrutura):
                self.auth.provisionar('nova', self.senha, PapelAcesso.GESTAO)
            self.assertEqual(dest.read_bytes(), conteudo)

    def test_rejeita_sobreposicao_contas_e_historico(self):
        with self.assertRaises(ValueError):
            create_app({**self.cfg, 'HISTORICO': self.pasta / 'contas.json'})

    def test_login_roteia_por_papel_limpa_sessao_e_ignora_next(self):
        with self.http.session_transaction() as sess:
            sess['lixo'] = 'anterior'
        resp = self.login('operador', next='https://example.invalid/')
        self.assertEqual(resp.location, '/gestao/')
        with self.http.session_transaction() as sess:
            self.assertNotIn('lixo', sess)
        self.assertEqual(self.http.get('/gestao/').status_code, 200)
        self.assertEqual(self.http.get('/cliente/').status_code, 403)

    def test_erro_de_login_uniforme(self):
        a = self.login('lia', 'incorreta')
        b = self.login('desconhecido', 'incorreta')
        self.assertEqual(a.status_code, 401)
        self.assertEqual(a.data, b.data)
        self.assertNotIn(b'scrypt:', a.data)

    def test_login_cliente_escape_e_papel(self):
        self.assertEqual(self.login().location, '/cliente/')
        resp = self.http.get('/cliente/?cliente_id=' + self.outro['identificador'])
        self.assertIn(b'Lia &lt;Vale&gt;', resp.data)
        self.assertNotIn(b'Outro Titular', resp.data)
        self.assertNotIn(b'Faturamento', resp.data)
        self.assertNotIn(self.senha.encode(), resp.data)
        self.assertEqual(self.http.get('/gestao/').status_code, 403)

    def test_recurso_pessoal_autoriza_pelo_evento_da_entrada(self):
        ids = []
        for i, obj in enumerate([self.titular, self.outro], 1):
            placa = 'EX' + str(i)
            self.srv.cadastrar_veiculo('carro', placa, 'Teste')
            self.srv.vincular_veiculo(placa, obj['identificador'])
            ids.append(self.srv.iniciar_estadia(placa, i, obj['identificador'])['estadia_id'])
        self.login()
        self.assertIn(b'EX1', self.http.get(f'/cliente/estadias/{ids[0]}').data)
        terceiro = self.http.get(f'/cliente/estadias/{ids[1]}')
        ausente = self.http.get('/cliente/estadias/9999')
        self.assertEqual((terceiro.status_code, terceiro.data), (404, ausente.data))
        self.assertNotIn(b'EX2', self.http.get('/cliente/').data)

    def test_acesso_anonimo_e_logout(self):
        self.assertEqual(self.http.get('/gestao/').location, '/entrar')
        self.login()
        self.assertEqual(self.http.get('/sair').status_code, 405)
        self.assertEqual(self.http.post('/sair', data={'csrf_token': self.token('/cliente/')}).status_code, 303)
        self.assertEqual(self.http.get('/cliente/').location, '/entrar')

    def test_csrf_login_logout_e_rotacao(self):
        antes = self.token()
        for valor in ['', 'inválido']:
            self.assertEqual(self.http.post('/entrar', data={'csrf_token': valor}).status_code, 400)
        self.login()
        self.assertEqual(self.http.post('/sair', data={'csrf_token': antes}).status_code, 400)
        self.assertEqual(self.http.get('/cliente/').status_code, 200)

    def test_sessao_expirada_exige_novo_login(self):
        self.login()
        with patch('web.seguranca.agora', return_value=10**10):
            resp = self.http.get('/cliente/')
        self.assertEqual(resp.status_code, 401)
        self.assertIn('Sessão expirada'.encode(), resp.data)
        self.assertEqual(self.http.get('/cliente/').location, '/entrar')

    def test_cookie_e_cache(self):
        self.app.config['SESSION_COOKIE_SECURE'] = True
        resp = self.http.get('/entrar', base_url='https://localhost')
        cookie = resp.headers['Set-Cookie']
        for item in ['Secure', 'HttpOnly', 'SameSite=Lax']:
            self.assertIn(item, cookie)
        self.assertIn('no-store', resp.headers['Cache-Control'])

    def test_falha_operacional_nao_vira_ocupacao_zero(self):
        self.login('operador')
        self.cfg['HISTORICO'].write_text('{')
        resp = self.http.get('/gestao/')
        self.assertEqual(resp.status_code, 503)
        self.assertNotIn(b'Traceback', resp.data)
        self.assertNotIn(b'Mapa de vagas', resp.data)
        self.assertNotIn(b'R$ 0,00', resp.data)

    def test_conflito_e_resultado_incerto_nao_reexecutam(self):
        self.login('operador')
        for erro, status in [(ConflitoDeHistorico(), 409), (ResultadoIncerto('operacao_presente'), 503)]:
            with patch.object(self.srv, 'consultar_ocupacao', side_effect=erro) as ler:
                self.assertEqual(self.http.get('/gestao/').status_code, status)
                ler.assert_called_once()

    def test_viewmodel_imutavel_e_valores_exatos(self):
        vm = OcupacaoViewModel.da_consulta({'livres': 7, 'ocupadas': 3, 'total': 10})
        self.assertEqual(vm.percentual, 30)
        with self.assertRaises(FrozenInstanceError):
            vm.livres = 0
        self.assertEqual(dinheiro('40.005'), 'R$ 40,01')
        self.assertEqual(dinheiro('6.1'), 'R$ 6,10')
        for original, exibido in [('6.125', '6,13'), ('0.0001', '0,00'), ('0.005', '0,01'),
                                  ('1e-1000', '0,00'), ('9999.995', '10.000,00')]:
            with self.subTest(original=original):
                self.assertEqual(dinheiro(original), 'R$ ' + exibido)
        self.assertEqual(centavos(613), 'R$ 6,13')
        self.assertEqual(horario('2026-11-20T13:15:00-03:00'), '20/11/2026 às 13:15 (-03:00)')

    def test_cli_oculta_senha_e_provisiona_os_dois_papeis(self):
        runner = self.app.test_cli_runner()
        for nome, papel, args in [('nova.gestao', 'gestao', []),
                                  ('nova.pessoal', 'cliente', ['--cliente-id', self.outro['identificador']])]:
            res = runner.invoke(args=['criar-conta', '--usuario', nome, '--papel', papel, *args],
                                input=self.senha + '\n' + self.senha + '\n')
            self.assertEqual(res.exit_code, 0, res.output)
            self.assertNotIn(self.senha, res.output)
            self.assertEqual(self.auth.autenticar(nome, self.senha).papel, papel)

    def test_provisionamento_concorrente_preserva_unicidade(self):
        barreira = Barrier(2)
        def criar():
            barreira.wait(timeout=5)
            try:
                self.auth.provisionar('mesmo', self.senha, PapelAcesso.GESTAO)
                return True
            except ValueError:
                return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            tarefas = [pool.submit(criar) for _ in range(2)]
            self.assertCountEqual([t.result() for t in tarefas], [True, False])
        self.assertIsNotNone(self.auth.autenticar('operador', self.senha))

    def test_terminal_e_segundo_servidor_respeitam_a_reserva(self):
        self.http.get('/entrar')
        main = Path(__file__).resolve().parents[1] / 'main.py'
        chamada = [sys.executable, '-B', str(main)]
        env = {**os.environ, 'MOVE_HISTORICO': str(self.cfg['HISTORICO'])}
        bloqueado = subprocess.run(chamada, cwd=self.pasta, env=env, input='4\n', capture_output=True, text=True)
        self.assertNotEqual(bloqueado.returncode, 0)
        self.assertIn('em uso', bloqueado.stderr)
        segunda = create_app(self.cfg)
        self.addCleanup(segunda.extensions['escritor'].fechar)
        self.assertEqual(segunda.test_client().get('/entrar').status_code, 503)
        self.app.extensions['escritor'].fechar()
        livre = subprocess.run(chamada, cwd=self.pasta, env=env, input='4\n', capture_output=True, text=True)
        self.assertEqual(livre.returncode, 0, livre.stderr)

    def test_sessao_verifica_conta_em_cada_acesso(self):
        self.login('operador')
        (self.pasta / 'contas.json').write_text('[]')  # remoção externa em fixture
        self.assertEqual(self.http.get('/gestao/').status_code, 401)
        self.assertEqual(self.http.get('/gestao/').location, '/entrar')

    def test_arquivo_de_contas_preservado_em_falha_de_gravacao(self):
        destino = self.pasta / 'contas.json'
        anterior = destino.read_bytes()
        with patch('persistence.historico_json.os.replace', side_effect=OSError()), self.assertRaises(ErroDeInfraestrutura):
            self.auth.provisionar('adicional', self.senha, PapelAcesso.GESTAO)
        self.assertEqual(destino.read_bytes(), anterior)
        self.assertIsNone(self.auth.autenticar('adicional', self.senha))

    def test_indisponibilidade_financeira_preserva_ocupacao(self):
        self.login('operador')
        with patch.object(self.srv, 'consultar_faturamento', side_effect=ErroDeInfraestrutura()):
            resp = self.http.get('/gestao/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Dados financeiros indispon', resp.data)
        self.assertNotIn(b'R$ 0,00', resp.data)
        self.assertIn(b'Mapa de vagas', resp.data)

    def test_recuperacao_preserva_estadia_autorizada(self):
        self.srv.cadastrar_veiculo('carro', 'V1', 'Modelo')
        titular = self.titular['identificador']
        self.srv.vincular_veiculo('V1', titular)
        identificador = self.srv.iniciar_estadia('V1', 1, titular)['estadia_id']
        self.login()
        caminho = f'/cliente/estadias/{identificador}'
        with patch.object(self.srv, 'listar_estadias_ativas', side_effect=ResultadoIncerto('operacao_presente')):
            resposta = self.http.get(caminho)
        self.assertEqual(resposta.status_code, 503)
        self.assertIn('Consultar estado'.encode(), resposta.data)
        self.assertIn(f'href="{caminho}"'.encode(), resposta.data)
        self.assertEqual(self.http.get(caminho).status_code, 200)
