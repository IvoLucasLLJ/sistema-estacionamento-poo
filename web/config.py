import os
import secrets
from pathlib import Path

from persistence import privacidade

from persistence.caminhos import caminho_local, historico_local
from persistence.exclusividade import trava_de_arquivo


def chave_persistida(chave):
    # Todos os inicializadores usam a mesma trava. O Termux pode não oferecer os.link.
    with trava_de_arquivo(str(chave) + '.lock', esperar=True):
        if not chave.exists():
            temporario = None
            try:
                with privacidade.temporario_privado(chave) as (temporario, saida):
                    saida.write(secrets.token_bytes(32))
                    saida.flush()
                    os.fsync(saida.fileno())
                os.replace(temporario, chave)
            finally:
                if temporario is not None:
                    temporario.unlink(missing_ok=True)
        if os.name == 'nt':
            privacidade.conferir_acl(chave)
        return chave.read_bytes()


def configurar(app, opcoes):
    app.config.from_mapping(
        DADOS=os.environ.get('MOVE_DADOS', 'instance'),
        CONTAS=os.environ.get('MOVE_CONTAS'),
        DEMONSTRACAO=False,
        VINCULOS_PORTAIS={},
        HISTORICO=historico_local(),
        SECRET_KEY=os.environ.get('MOVE_SECRET_KEY'), SESSION_COOKIE_NAME='move_session',
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.environ.get('MOVE_HTTPS', '0') == '1',
        DURACAO_SESSAO=1800, MAX_CONTENT_LENGTH=16384, TRUSTED_HOSTS=['localhost', '127.0.0.1'],
    )
    app.config.update(opcoes or {})
    dados = caminho_local(app.config['DADOS'])
    privacidade.criar_pasta_privada(dados)
    contas = caminho_local(app.config.get('CONTAS') or dados / 'contas.json')
    historico = caminho_local(app.config['HISTORICO'])
    chave = caminho_local(dados / 'sessao.key')
    caminhos = [historico, contas, chave, Path(str(historico) + '.lock'), Path(str(contas) + '.lock'),
                Path(str(chave) + '.lock')]
    if len(set(caminhos)) != len(caminhos) or any(p.is_relative_to(Path(app.static_folder)) for p in caminhos):
        raise ValueError('Use arquivos privados distintos, fora da pasta estática.')
    if os.name == 'nt':
        privacidade.conferir_acl(contas.parent)
        if contas.exists():
            privacidade.conferir_acl(contas)
    app.config.update(DADOS=dados, CONTAS=contas, HISTORICO=historico)
    if app.config['SECRET_KEY'] is None:
        app.config['SECRET_KEY'] = chave_persistida(chave)
    if len(app.config['SECRET_KEY']) < 32:
        raise ValueError('A chave da sessão precisa ter pelo menos 32 bytes.')
