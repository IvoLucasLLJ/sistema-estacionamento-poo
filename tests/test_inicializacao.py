"""Regressões de preparação do cenário e de início seguro do servidor."""
import io
import os
import shutil
import socket
import subprocess
import sys
from contextlib import redirect_stderr
from pathlib import Path
from secrets import token_urlsafe
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from persistence.ambiente_termux import prefixo_termux
from persistence.exclusividade import HistoricoEmUso
from service.estacionamento_service import ErroDeInfraestrutura
from web import create_app
from web.__main__ import main, opcoes, reservar_porta, servir
from web.demonstracao import preparar_demonstracao, provisionar_demonstracao


class InicializacaoTests(TestCase):
    def setUp(self):
        self.raiz = Path(self.enterContext(TemporaryDirectory())).resolve()
        self.operacao = self.raiz / 'operação'
        self.operacao.mkdir()
        self.enterContext(patch('web.demonstracao.RAIZ_MOVE', self.raiz))
        self.enterContext(patch.dict(os.environ, MOVE_DADOS=str(self.operacao),
                                     MOVE_CONTAS=str(self.operacao / 'contas.json'),
                                     MOVE_HISTORICO=str(self.operacao / 'legado.json')))

    def test_cenario_reutilizado_com_financeiro_e_arquivos_independentes(self):
        segredo = token_urlsafe(36)
        with patch.dict(os.environ, MOVE_SECRET_KEY=segredo, MOVE_HTTPS='1'):
            cfg, titular = preparar_demonstracao()
            app = create_app(cfg)
        self.assertNotEqual(app.secret_key, segredo)
        self.assertFalse(app.config['SESSION_COOKIE_SECURE'])
        self.assertNotEqual(app.config['SESSION_COOKIE_NAME'], 'move_session')
        s = app.extensions['estacionamento']
        self.assertEqual(s.buscar_cliente(titular)['nome'], 'Lia Vale')
        self.assertEqual(s.consultar_ocupacao(), dict(total=10, ocupadas=3, livres=7))
        self.assertEqual(s.consultar_cobranca('AV1', '1.225')['valor_centavos'], 613)
        self.assertEqual(s.consultar_cobranca('NM4', '2')['valor_centavos'], 0)
        self.assertEqual(s.consultar_faturamento()['centavos'], 4000)
        s.cadastrar_cliente('comum', 'Cliente de ensaio')
        pasta = cfg['DADOS']
        antes = {p.name: p.read_bytes() for p in pasta.iterdir()}
        self.assertEqual(preparar_demonstracao(), (cfg, titular))
        self.assertEqual({p.name: p.read_bytes() for p in pasta.iterdir()}, antes)
        self.assertEqual(list(self.operacao.iterdir()), [])

    def test_rejeita_pasta_desconhecida_e_colisao_com_configuracao_operacional(self):
        pasta = self.raiz / '.move-demonstracao'
        pasta.mkdir(mode=0o700)
        antigo = pasta / 'historico.json'
        antigo.write_bytes(b'preservar')
        with self.assertRaises(OSError):
            preparar_demonstracao()
        self.assertEqual(antigo.read_bytes(), b'preservar')
        with patch.dict(os.environ, MOVE_HISTORICO=str(antigo)), self.assertRaisesRegex(ValueError, 'operacional'):
            preparar_demonstracao()

    def test_falha_ao_semear_permanece_fora_do_cenario_publicado(self):
        with patch('web.demonstracao.criar_cenario', side_effect=ErroDeInfraestrutura('gravação')), self.assertRaises(ErroDeInfraestrutura):
            preparar_demonstracao()
        self.assertFalse((self.raiz / '.move-demonstracao').exists())
        self.assertEqual(list(self.raiz.glob('.move-cenario-*/')), [])
        self.assertTrue(preparar_demonstracao()[0]['HISTORICO'].is_file())

    def test_rejeita_reutilizacao_de_arquivo_externo(self):
        cfg, _ = preparar_demonstracao()
        externo = self.operacao / 'contas.json'
        externo.write_text('[]', encoding='utf-8')
        cfg['CONTAS'].unlink()
        # Um link físico também exporia o cadastro externo e dispensa privilégios no Windows.
        if os.name == 'nt':
            os.link(externo, cfg['CONTAS'])
        else:
            cfg['CONTAS'].symlink_to(externo)
        with self.assertRaisesRegex(ValueError, 'Arquivo de demonstração inválido'):
            preparar_demonstracao()
        self.assertEqual(externo.read_bytes(), b'[]')

    def test_pasta_incompleta_ou_historico_corrompido_nao_anuncia_disponibilidade(self):
        cfg, _ = preparar_demonstracao()
        cfg['HISTORICO'].write_bytes(b'{')
        with patch('web.__main__.servir') as iniciar, patch('web.__main__.socket.create_server'), \
                self.assertRaises(ErroDeInfraestrutura):
            main(['--demonstracao'])
        iniciar.assert_not_called()
        self.assertEqual(cfg['HISTORICO'].read_bytes(), b'{')
        (cfg['DADOS'] / 'sessao.key').unlink()
        with self.assertRaises(FileNotFoundError):
            preparar_demonstracao()
        self.assertFalse((cfg['DADOS'] / 'sessao.key').exists())

    def test_rede_exige_ip_privado_especifico_e_demonstracao(self):
        self.assertIsNone(opcoes([]).rede_privada)
        for args in (['--rede-privada', '192.168.0.2'], ['--porta', '0'], ['--porta', '65536'],
                     *(['--demonstracao', '--rede-privada', ip] for ip in
                       ['0.0.0.0', '127.0.0.1', '8.8.8.8', '169.254.1.2', 'localhost', '172.32.0.1'])):
            with self.subTest(args=args), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                opcoes(args)
        args = ['--demonstracao', '--rede-privada', '192.168.1.20']
        with patch('web.__main__.socket.create_server') as escuta, \
                patch('web.__main__.provisionar_demonstracao'), patch('web.__main__.servir') as executar:
            main(args)
        escuta.assert_called_once_with(('192.168.1.20', 5000))
        app = executar.call_args.args[0]
        self.addCleanup(app.extensions['escritor'].fechar)
        self.assertEqual(app.config['TRUSTED_HOSTS'], ['192.168.1.20'])
        self.assertEqual(app.test_client().get('/entrar', base_url='http://192.168.1.20').status_code, 200)
        recusada = app.test_client().get('/entrar', base_url='http://localhost')
        self.assertEqual(recusada.status_code, 400)
        self.assertEqual(recusada.mimetype, 'text/plain')

    def test_porta_ocupada_ou_historico_bloqueado_impede_abertura(self):
        with socket.create_server(('127.0.0.1', 0)) as outra, patch('sys.stdin.isatty', return_value=False), \
                patch('web.__main__.abrir_navegador') as abrir, self.assertRaisesRegex(ValueError, 'ocupada'):
            main(['--demonstracao', '--porta', str(outra.getsockname()[1])])
        abrir.assert_not_called()
        self.assertFalse((self.raiz / '.move-demonstracao').exists())
        cfg, _ = preparar_demonstracao()
        app = create_app(cfg)
        escritor = app.extensions['escritor']
        self.addCleanup(escritor.fechar)
        escritor.abrir()
        with patch('web.__main__.socket.create_server'), patch('web.__main__.servir') as iniciar, self.assertRaises(HistoricoEmUso):
            main(['--demonstracao'])
        iniciar.assert_not_called()

    def test_porta_alternativa_escolhida_pelo_usuario(self):
        with socket.create_server(('127.0.0.1', 0)) as ocupada:
            with socket.create_server(('127.0.0.1', 0)) as candidata:
                numero = candidata.getsockname()[1]
            with patch('builtins.input', return_value=str(numero)), \
                    reservar_porta('127.0.0.1', ocupada.getsockname()[1], True) as selecionada:
                self.assertEqual(selecionada.getsockname(), ('127.0.0.1', numero))

    def test_conta_pendente_requer_terminal_e_contas_corrompidas_sao_preservadas(self):
        cfg, titular = preparar_demonstracao()
        app = create_app(cfg)
        with patch('sys.stdin.isatty', return_value=False), self.assertRaisesRegex(ValueError, 'gestao.demo'):
            provisionar_demonstracao(app, titular)
        cfg['CONTAS'].write_bytes(b'{')
        with self.assertRaises(ErroDeInfraestrutura):
            provisionar_demonstracao(app, titular)
        self.assertEqual(cfg['CONTAS'].read_bytes(), b'{')

    def test_falha_na_sondagem_http_impede_abrir_navegador(self):
        cfg, _ = preparar_demonstracao()
        app = create_app(cfg)
        self.addCleanup(app.extensions['escritor'].fechar)
        app.before_request(lambda: ('indisponível', 503))
        with socket.create_server(('127.0.0.1', 0)) as porta, \
                patch('web.__main__.abrir_navegador') as abrir, self.assertRaisesRegex(ValueError, 'login'):
            servir(app, porta, '127.0.0.1', porta.getsockname()[1], True)
        abrir.assert_not_called()


class PreparoDaVenvTests(TestCase):
    def setUp(self):
        self.pasta = Path(self.enterContext(TemporaryDirectory())).resolve()
        self.raiz = self.pasta / 'Instalação de teste'
        self.raiz.mkdir()
        projeto = Path(__file__).resolve().parents[1]
        self.entrada = ('INICIAR_MOVE_ANDROID.sh' if prefixo_termux() else
                        'INICIAR_MOVE_WINDOWS.cmd' if os.name == 'nt' else
                        'INICIAR_MOVE_MAC.command' if sys.platform == 'darwin' else 'INICIAR_MOVE_LINUX.sh')
        (self.raiz / 'persistence').mkdir()
        for nome in ('exclusividade.py', 'ambiente_termux.py'):
            shutil.copy2(projeto / 'persistence' / nome, self.raiz / 'persistence')
        for nome in ('iniciar_move.py', 'INICIAR_MOVE_LINUX.sh', self.entrada):
            shutil.copy2(projeto / nome, self.raiz / nome)

    def iniciar(self, python):
        return subprocess.run([str(self.raiz / self.entrada)], cwd=self.pasta,
                              env={**os.environ, 'MOVE_PYTHON': str(python)},
                              capture_output=True, encoding='utf-8', timeout=20)

    def test_python_ausente_interrompe_antes_de_preparar(self):
        resultado = self.iniciar(self.pasta / 'ausente')
        self.assertNotEqual(resultado.returncode, 0)
        self.assertRegex(resultado.stderr, 'Python adequado (não|nao) encontrado')
        self.assertFalse((self.raiz / '.venv').exists())

    def test_diretorio_desconhecido_e_preservado(self):
        venv = self.raiz / '.venv'
        venv.mkdir()
        arquivo = venv / 'preservar.txt'
        arquivo.write_bytes(b'original')
        resultado = self.iniciar(sys.executable)
        self.assertNotEqual(resultado.returncode, 0)
        self.assertIn('renomeie a pasta', resultado.stderr)
        self.assertEqual(arquivo.read_bytes(), b'original')
        self.assertFalse((self.raiz / '.move-demonstracao').exists())
