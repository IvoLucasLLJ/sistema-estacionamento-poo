import os
import secrets
from pathlib import Path
from tempfile import NamedTemporaryFile


def configurar(app, opcoes):
    raiz = Path(app.root_path).parent
    app.config.from_mapping(
        DADOS=os.environ.get('MOVE_DADOS', raiz / 'instance'),
        CONTAS=os.environ.get('MOVE_CONTAS'),
        HISTORICO=os.environ.get('MOVE_HISTORICO', raiz / 'historico.json'),
        SECRET_KEY=os.environ.get('MOVE_SECRET_KEY'), SESSION_COOKIE_NAME='move_session',
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.environ.get('MOVE_HTTPS', '0') == '1',
        DURACAO_SESSAO=1800, MAX_CONTENT_LENGTH=16384, TRUSTED_HOSTS=['localhost', '127.0.0.1'],
    )
    app.config.update(opcoes or {})
    dados = Path(app.config['DADOS']).expanduser().resolve()
    dados.mkdir(mode=0o700, parents=True, exist_ok=True)
    contas = Path(app.config.get('CONTAS') or dados / 'contas.json').expanduser().resolve()
    historico = Path(app.config['HISTORICO']).expanduser().resolve()
    chave = dados / 'sessao.key'
    caminhos = [historico, contas, chave, Path(str(historico) + '.lock'), Path(str(contas) + '.lock')]
    if len(set(caminhos)) != len(caminhos) or any(p.is_relative_to(Path(app.static_folder)) for p in caminhos):
        raise ValueError('Use arquivos privados distintos, fora da pasta estática.')
    app.config.update(CONTAS=contas, HISTORICO=historico)
    if app.config['SECRET_KEY'] is None:
        if not chave.exists():
            with NamedTemporaryFile(dir=dados) as temporario:
                temporario.write(secrets.token_bytes(32))
                temporario.flush()
                os.fsync(temporario.fileno())
                try:
                    os.link(temporario.name, chave)
                except FileExistsError:
                    pass
        app.config['SECRET_KEY'] = chave.read_bytes()
    if len(app.config['SECRET_KEY']) < 32:
        raise ValueError('A chave da sessão precisa ter pelo menos 32 bytes.')
