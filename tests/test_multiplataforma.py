"""Contratos de processo, disco e inicialização, com os mecanismos reais do SO hospedeiro."""
import multiprocessing
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from hashlib import sha256
from http.cookiejar import CookieJar
from pathlib import Path
from secrets import token_urlsafe
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, ProxyHandler, build_opener

from persistence import historico_json, privacidade
from persistence.exclusividade import EscritorLocal, HistoricoEmUso
from web import create_app
from web.demonstracao import preparar_demonstracao


def segurar_historico(arquivo, canal):
    escritor = EscritorLocal(arquivo)
    escritor.abrir()
    try:
        canal.send('reservado')
        canal.recv()
    finally:
        escritor.fechar()
        canal.close()


def provisionar_em_processo(pasta, nome, canal):
    app = create_app(dict(DADOS=pasta, HISTORICO=pasta / 'histórico.json'))
    auth = app.extensions['autenticacao']
    canal.send(sha256(app.secret_key).digest())
    canal.recv()
    senha = token_urlsafe(32)
    auth.provisionar(nome, senha, 'gestao')
    try:
        auth.provisionar('compartilhada', senha, 'gestao')
        canal.send('criada')
    except ValueError as erro:
        canal.send(str(erro))
    finally:
        canal.close()


class MultiplataformaTests(TestCase):
    def setUp(self):
        self.raiz = Path(self.enterContext(TemporaryDirectory())).resolve() / 'Avaliação 林'
        privacidade.criar_pasta_privada(self.raiz)

    def processo(self, alvo, *args):
        ctx = multiprocessing.get_context('spawn')
        pai, filho = ctx.Pipe()
        proc = ctx.Process(target=alvo, args=(*args, filho))
        proc.start()
        filho.close()

        def limpar():
            if proc.is_alive():
                proc.kill()
            proc.join(10)
            pai.close()
            proc.close()

        self.addCleanup(limpar)
        return proc, pai

    def receber(self, canal):
        self.assertTrue(canal.poll(20), 'Processo filho não confirmou a etapa.')
        return canal.recv()

    def test_bloqueio_persiste_ao_substituir_json_e_libera_apos_saida_ou_morte(self):
        arquivo = self.raiz / 'histórico.json'
        escritor = EscritorLocal(arquivo)
        versao = None
        for fatal in (False, True):
            with self.subTest(fatal=fatal):
                proc, canal = self.processo(segurar_historico, arquivo)
                self.assertEqual(self.receber(canal), 'reservado')
                # O lock tem identidade própria mesmo quando o JSON ganha outro inode.
                eventos = [{'identificador': 22, 'nome': 'Íris', 'encerrado': fatal}]
                versao = historico_json.salvar(arquivo, eventos, versao)
                with self.assertRaises(HistoricoEmUso):
                    escritor.abrir()
                if fatal:
                    proc.kill()
                else:
                    canal.send('encerrar')
                proc.join(10)
                self.assertFalse(proc.is_alive())
                escritor.abrir()
                escritor.fechar()
                self.assertTrue(escritor.caminho.is_file())
                self.assertEqual(historico_json.ler(arquivo), (eventos, versao))

    def test_leitor_aberto_mantem_versao_anterior_durante_publicacao_atomica(self):
        arquivo = self.raiz / 'histórico.json'
        antes = historico_json.salvar(arquivo, [{'id': 22}])
        with privacidade.abrir_leitura(arquivo) as leitor:
            depois = historico_json.salvar(arquivo, [{'id': 22}, {'id': 23}], antes)
            self.assertEqual(leitor.read(), antes)
            self.assertEqual(arquivo.read_bytes(), depois)

    def test_acesso_invalido_nao_e_classificado_como_concorrencia(self):
        escritor = EscritorLocal(self.raiz / 'arquivo.json')
        escritor.caminho.mkdir()
        with self.assertRaises(OSError) as falha:
            escritor.abrir()
        self.assertNotIsInstance(falha.exception, HistoricoEmUso)

    def test_provisionamentos_em_processos_preservam_chave_e_unicidade(self):
        processos = [self.processo(provisionar_em_processo, self.raiz, n) for n in ('gestao.a', 'gestao.b')]
        chaves = [self.receber(c) for _, c in processos]
        self.assertEqual(chaves[0], chaves[1])
        for _, canal in processos:
            canal.send('iniciar')
        self.assertCountEqual([self.receber(c) for _, c in processos], ['criada', 'Nome de usuário já utilizado.'])
        for proc, _ in processos:
            proc.join(10)
            self.assertEqual(proc.exitcode, 0)
        registros, _ = historico_json.ler(self.raiz / 'contas.json')
        self.assertEqual({r['usuario'] for r in registros}, {'gestao.a', 'gestao.b', 'compartilhada'})
        self.assertEqual(len({r['id'] for r in registros}), 3)

    def test_arquivo_privado_respeita_o_controle_nativo_de_acesso(self):
        destino = self.raiz / 'teste.json'
        historico_json.salvar(destino, [])
        if os.name == 'nt':
            import win32security as seg
            privacidade.conferir_acl(destino)
            # Fixture vazia. Uma permissão de leitura para todos deve ser identificada.
            sd = seg.ConvertStringSecurityDescriptorToSecurityDescriptor('D:P(A;;FA;;;BA)(A;;FA;;;OW)(A;;FR;;;WD)', 1)
            seg.SetNamedSecurityInfo(str(destino), seg.SE_FILE_OBJECT, seg.DACL_SECURITY_INFORMATION,
                                     None, None, sd.GetSecurityDescriptorDacl(), None)
            with self.assertRaises(PermissionError):
                privacidade.conferir_acl(destino)
        else:
            self.assertEqual(destino.stat().st_mode & 0o777, 0o600)

    def test_servidor_em_copia_unicode_reabre_os_dois_portais(self):
        origem = Path(__file__).resolve().parents[1]
        for nome in ('web', 'service', 'persistence', 'controller', 'repository', 'model', 'view'):
            shutil.copytree(origem / nome, self.raiz / nome, ignore=shutil.ignore_patterns('__pycache__'))
        env = dict(os.environ, MOVE_HISTORICO=str(self.raiz / 'operacao.json'),
                   MOVE_DADOS=str(self.raiz / 'operacao'), PYTHONIOENCODING='utf-8')
        with patch('web.demonstracao.RAIZ_MOVE', self.raiz), patch.dict(os.environ, env):
            config, lia = preparar_demonstracao()
        app = create_app(config)
        auth = app.extensions['autenticacao']
        senha = token_urlsafe(32)
        auth.provisionar('gestao.demo', senha, 'gestao')
        auth.provisionar('cliente.demo', senha, 'cliente', lia)
        antes = [p.read_bytes() for p in (config['HISTORICO'], config['CONTAS'])]
        for abertura in range(2):
            with socket.create_server(('127.0.0.1', 0)) as reserva:
                porta = reserva.getsockname()[1]
            url = f'http://127.0.0.1:{porta}'
            log = self.raiz / f'inicio-{abertura}.log'
            with log.open('wb') as saida:
                proc = subprocess.Popen([sys.executable, '-B', '-m', 'web', '--demonstracao',
                                         '--sem-navegador', '--porta', str(porta)], cwd=self.raiz,
                                        env=env, stdout=saida, stderr=subprocess.STDOUT)
                try:
                    limite = time.monotonic() + 20
                    while proc.poll() is None and time.monotonic() < limite:
                        if b'MOVE dispon' in log.read_bytes():
                            break
                        time.sleep(0.05)
                    self.assertIn(f'{url}/entrar'.encode(), log.read_bytes(), log.read_bytes())
                    for usuario, destino in [('gestao.demo', '/gestao/'), ('cliente.demo', '/cliente/')]:
                        navegador = build_opener(ProxyHandler({}), HTTPCookieProcessor(CookieJar()))
                        with navegador.open(url + '/entrar', timeout=5) as login:
                            csrf = re.search(rb'name="csrf_token" value="([^"]+)"', login.read())[1].decode()
                        dados = urlencode(dict(usuario=usuario, senha=senha, csrf_token=csrf)).encode()
                        with navegador.open(url + '/entrar', dados, timeout=5) as portal:
                            self.assertEqual((portal.status, portal.url), (200, url + destino))
                finally:
                    if proc.poll() is None:
                        proc.kill()
                    proc.wait(10)
            self.assertEqual([p.read_bytes() for p in (config['HISTORICO'], config['CONTAS'])], antes)
