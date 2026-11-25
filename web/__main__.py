"""Execução local em primeiro plano, com uma reserva de histórico por servidor."""
import argparse
import errno
from http.client import HTTPConnection, HTTPException
from ipaddress import IPv4Address, IPv4Network
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryFile
from threading import Thread
import webbrowser

import click
from werkzeug.serving import WSGIRequestHandler, make_server

from persistence.ambiente_termux import prefixo_termux
from service.estacionamento_service import ErroDeInfraestrutura
from web import create_app
from web.demonstracao import preparar_demonstracao, provisionar_demonstracao


class RequisicaoLocal(WSGIRequestHandler):
    """Permite drenar as requisições ao sair, inclusive se o navegador pré-conectou e ficou ocioso."""
    timeout = 8


def opcoes(argumentos=None):
    cli = argparse.ArgumentParser(description='Inicia o MOVE em um único processo.')
    cli.add_argument('--demonstracao', action='store_true', help='Usar o cenário fictício separado.')
    cli.add_argument('--porta', type=int, default=5000, help='Porta TCP local (padrão 5000).')
    cli.add_argument('--rede-privada', metavar='IP', help='Servir a demonstração no IPv4 específico da rede privada.')
    cli.add_argument('--sem-navegador', action='store_true', help='Exibir a URL sem abrir uma aba.')
    args = cli.parse_args(argumentos)
    if not 1 <= args.porta <= 65535:
        cli.error('Escolha uma porta de 1 a 65535.')
    if args.rede_privada:
        try:
            ip = IPv4Address(args.rede_privada)
        except ValueError:
            cli.error('Informe o endereço IPv4 da interface privada do computador.')
        if not args.demonstracao or not any(ip in IPv4Network(rede) for rede in
                                            ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16')):
            cli.error('A rede exige --demonstracao e o IPv4 de uma interface privada específica.')
    return args


def abrir_navegador(url):
    try:
        termux = prefixo_termux()
        if termux:
            abridor = termux / 'bin/termux-open-url'
            if abridor.is_file() and subprocess.run([str(abridor), url], check=False).returncode == 0:
                return
            print('Abra a URL acima no navegador do Android.')
            return
        if sys.platform == 'darwin':
            if subprocess.run(['open', '-a', 'Google Chrome', url], stderr=subprocess.DEVNULL).returncode == 0:
                return
        elif os.name == 'nt':
            for chave in ('PROGRAMFILES', 'PROGRAMFILES(X86)', 'LOCALAPPDATA'):
                if os.environ.get(chave):
                    chrome = Path(os.environ[chave]) / 'Google/Chrome/Application/chrome.exe'
                    if chrome.is_file() and webbrowser.BackgroundBrowser(str(chrome)).open(url):
                        return
        elif os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'):
            chrome = shutil.which('google-chrome') or shutil.which('google-chrome-stable')
            if chrome and webbrowser.BackgroundBrowser(chrome).open(url):
                return
        else:
            print('Sessão sem interface gráfica. Abra a URL no navegador.')
            return
        if webbrowser.open_new_tab(url):
            return
    except (OSError, webbrowser.Error):
        pass
    print('Abra a URL acima no seu navegador.')


def reservar_porta(host, porta, interativo):
    while True:
        try:
            return socket.create_server((host, porta))
        except OSError as erro:
            if erro.errno != errno.EADDRINUSE:
                raise ValueError(f'Não foi possível reservar {host}:{porta}. Confira o endereço e a permissão da porta. {erro}') from erro
            mensagem = f'Porta {porta} ocupada.'
            if not interativo:
                alternativa = 5001 if porta != 5001 else 5002
                raise ValueError(f'{mensagem} Escolha outra, por exemplo --porta {alternativa}.') from erro
            escolha = input(f'{mensagem} Digite outra porta ou pressione Enter para encerrar: ').strip()
            if not escolha:
                raise click.Abort()
            if not escolha.isascii() or not escolha.isdecimal() or len(escolha) > 5 or not 1 <= int(escolha) <= 65535:
                raise ValueError('Porta inválida. Use um número de 1 a 65535.')
            porta = int(escolha)


def servir(app, porta_reservada, host, porta, abrir):
    # O mesmo descritor permanece reservado desde o início da preparação da aplicação.
    with make_server(host, porta, app, threaded=True, request_handler=RequisicaoLocal,
                     fd=porta_reservada.fileno()) as servidor:
        servidor.daemon_threads = False
        thread = Thread(target=servidor.serve_forever)
        thread.start()
        try:
            conexao = HTTPConnection(host, porta, timeout=8)
            try:
                conexao.request('GET', '/entrar')
                resposta = conexao.getresponse()
                if resposta.status != 200 or b'name="csrf_token"' not in resposta.read():
                    raise ValueError('O login do MOVE não respondeu corretamente. Confira o histórico e a configuração.')
            finally:
                conexao.close()
            url = f'http://{host}:{porta}/entrar'
            print(f'MOVE disponível em {url}\nPara encerrar, pressione Ctrl+C neste terminal.', flush=True)
            if abrir:
                abrir_navegador(url)
            try:
                while thread.is_alive():
                    thread.join(0.25)
            except KeyboardInterrupt:
                print('\nEncerrando o MOVE.')
        finally:
            servidor.shutdown()
            thread.join()


def main(argumentos=None):
    args = opcoes(argumentos)
    host = args.rede_privada or '127.0.0.1'
    if args.rede_privada:
        print('Demonstração em rede privada. HTTP transmite a senha sem criptografia. Use apenas contas fictícias e encerre após demonstrar.', flush=True)
    with reservar_porta(host, args.porta, args.demonstracao and sys.stdin.isatty()) as porta:
        config, titular = preparar_demonstracao() if args.demonstracao else ({}, None)
        if args.rede_privada:
            config['TRUSTED_HOSTS'] = [host]
        app = create_app(config)
        escritor = app.extensions['escritor']
        escritor.abrir()
        try:
            app.extensions['estacionamento'].consultar_ocupacao()
            for diretorio in {app.config['HISTORICO'].parent, app.config['DADOS'], app.config['CONTAS'].parent}:
                with TemporaryFile(dir=diretorio):
                    pass
            if args.demonstracao:
                provisionar_demonstracao(app, titular)
                print('Demonstração fictícia · Apresentação nos dois portais: master.demo · '
                      'Gestão: gestao.demo · Cliente: cliente.demo', flush=True)
            else:
                if not app.extensions['autenticacao'].contas.tem_gestor():
                    print('Nenhuma conta de Gestão. Provisione com python -m flask --app web criar-conta --usuario gestor --papel gestao.')
                if not app.config['HISTORICO'].exists():
                    print(f"Histórico operacional ainda ausente. A primeira escrita usará {app.config['HISTORICO']}.")
            servir(app, porta, host, porta.getsockname()[1], args.demonstracao and not args.sem_navegador)
        finally:
            escritor.fechar()


if __name__ == '__main__':
    os.umask(0o077)
    try:
        main()
    except (KeyboardInterrupt, EOFError, click.Abort):
        sys.exit('\nInicialização interrompida pelo usuário.')
    except (OSError, ValueError, HTTPException, ErroDeInfraestrutura, click.ClickException) as erro:
        sys.exit(f'Inicialização interrompida. {erro}')
