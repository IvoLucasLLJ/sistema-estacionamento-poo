"""Ensaio de duas aberturas em uma cópia descartável do MOVE."""
import os
import re
import signal
import socket
import subprocess
import sys
import time
from http.cookiejar import CookieJar
from pathlib import Path
from secrets import token_urlsafe
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, ProxyHandler, build_opener

from web import create_app
from web.demonstracao import preparar_demonstracao


def conferir_logins(url, senha):
    for usuario, destino in [('gestao.demo', '/gestao/'), ('cliente.demo', '/cliente/'), ('master.demo', '/gestao/')]:
        navegador = build_opener(ProxyHandler({}), HTTPCookieProcessor(CookieJar()))
        with navegador.open(url + '/entrar', timeout=5) as login:
            csrf = re.search(rb'name="csrf_token" value="([^"]+)"', login.read())[1].decode()
        dados = urlencode(dict(usuario=usuario, senha=senha, csrf_token=csrf)).encode()
        with navegador.open(url + '/entrar', dados, timeout=5) as portal:
            assert (portal.status, portal.url) == (200, url + destino)


def conferir_reaberturas(raiz, comando):
    if (raiz / '.move-demonstracao').exists():
        raise ValueError('O ensaio requer uma cópia nova, sem cenário de demonstração.')
    env = dict(os.environ, MOVE_HISTORICO=str(raiz / 'operacao.json'),
               MOVE_DADOS=str(raiz / 'operacao'), PYTHONIOENCODING='utf-8', PIP_NO_INDEX='1')
    with patch('web.demonstracao.RAIZ_MOVE', raiz), patch.dict(os.environ, env):
        config, lia = preparar_demonstracao()
    app = create_app(config)
    senha = token_urlsafe(32)
    for usuario, papel, vinculo in [('gestao.demo', 'gestao', []), ('cliente.demo', 'cliente', ['--cliente-id', lia]),
                                    ('master.demo', 'gestao', [])]:
        resultado = app.test_cli_runner().invoke(args=['criar-conta', '--usuario', usuario,
                                                       '--papel', papel, *vinculo], input=f'{senha}\n{senha}\n')
        assert resultado.exit_code == 0, resultado.exception
    arquivos = [config['HISTORICO'], config['CONTAS'], config['DADOS'] / 'sessao.key']
    antes = [arquivo.read_bytes() for arquivo in arquivos]
    with TemporaryDirectory() as logs:
        for abertura in range(2):
            with socket.create_server(('127.0.0.1', 0)) as reserva:
                porta = reserva.getsockname()[1]
            url = f'http://127.0.0.1:{porta}'
            log = Path(logs) / f'inicio-{abertura}.log'
            with log.open('wb') as saida:
                proc = subprocess.Popen([*comando, '--sem-navegador', '--porta', str(porta)], cwd=raiz,
                                        env=env, stdin=subprocess.DEVNULL, stdout=saida, stderr=subprocess.STDOUT)
                try:
                    limite = time.monotonic() + 30
                    while proc.poll() is None and time.monotonic() < limite:
                        if b'MOVE dispon' in log.read_bytes():
                            break
                        time.sleep(0.05)
                    assert (url + '/entrar').encode() in log.read_bytes(), log.read_bytes()
                    conferir_logins(url, senha)
                    if os.name != 'nt' and abertura == 0:
                        proc.send_signal(signal.SIGINT)
                        assert proc.wait(15) == 0
                finally:
                    if proc.poll() is None:
                        if os.name == 'nt' and comando[0].lower().endswith('.cmd'):
                            # O CMD e o preparador aguardam o filho Flask. Encerrar só o pai deixaria o filho ativo.
                            subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'], check=True)
                        else:
                            proc.kill()
                    proc.wait(10)
            assert [arquivo.read_bytes() for arquivo in arquivos] == antes


if __name__ == '__main__':
    raiz = Path.cwd().resolve()
    if (raiz.parent != Path(os.environ['RUNNER_TEMP']).resolve() or (raiz / '.git').exists()
            or len(sys.argv) != 2 or Path(sys.argv[1]).resolve().parent != raiz):
        sys.exit('Execute o ensaio na cópia descartável extraída pelo workflow.')
    conferir_reaberturas(raiz, [sys.argv[1]])
    print('Inicializador do pacote: duas aberturas, três logins em cada e persistência preservada.')
