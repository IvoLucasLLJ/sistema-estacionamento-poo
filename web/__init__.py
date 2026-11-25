import click
from flask import Flask, g, render_template, request, url_for
from werkzeug.exceptions import HTTPException

from persistence.exclusividade import EscritorLocal
from service.estacionamento_service import (
    ConflitoDeHistorico, ErroDeInfraestrutura, ErroDeNegocio, EstacionamentoService, ResultadoIncerto,
)
from web.apresentacao import centavos, dinheiro, horario
from web.config import configurar
from web.contas import AutenticacaoService, ContaRepository, PapelAcesso
from web.rotas import acesso, cliente, gestao
from web.seguranca import csrf_token, destino, preparar_requisicao


def create_app(config=None):
    app = Flask(__name__)
    configurar(app, config)
    servico = EstacionamentoService(app.config['HISTORICO'])
    autenticacao = AutenticacaoService(ContaRepository(app.config['CONTAS']), servico)
    app.extensions.update(estacionamento=servico, autenticacao=autenticacao,
                          escritor=EscritorLocal(app.config['HISTORICO']))
    for area in (acesso, gestao, cliente):
        app.register_blueprint(area)
    app.before_request(preparar_requisicao)
    app.jinja_env.globals.update(csrf_token=csrf_token, destino=destino)
    app.jinja_env.filters['dinheiro'] = dinheiro
    app.jinja_env.filters['horario'] = horario
    app.jinja_env.filters['centavos'] = centavos

    @app.after_request
    def proteger(resposta):
        resposta.headers['Cache-Control'] = 'no-store'
        resposta.headers['X-Content-Type-Options'] = 'nosniff'
        resposta.headers['Referrer-Policy'] = 'no-referrer'
        resposta.headers['Content-Security-Policy'] = (
            "default-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        )
        return resposta

    def erro(status, titulo, mensagem, modelo='S05', acao='Voltar ao início', retorno=None,
             atencao=False):
        return render_template('erro.html', titulo=titulo, mensagem=mensagem, modelo=modelo,
                               acao=acao, retorno=retorno or destino(), atencao=atencao), status

    @app.errorhandler(HTTPException)
    def falha_http(exc):
        if 'identidade' not in g:
            g.identidade = None
        dados = {
            400: ('Solicitação inválida', 'Abra o formulário novamente e confira os dados.', 'M04'),
            401: ('Sessão expirada', 'Entre novamente para consultar seus dados.', 'S03'),
            403: ('Acesso negado', 'Sua conta não tem acesso a esta área.', 'S02'),
            404: ('Recurso indisponível', 'Não foi possível disponibilizar o recurso solicitado.', 'S04'),
        }
        estado = dados.get(exc.code, ('Solicitação indisponível', 'Volte ao início para continuar.', 'S04'))
        pagina, _ = erro(exc.code, *estado, atencao=exc.code == 401,
                         acao='Entrar novamente' if exc.code == 401 else 'Voltar ao início')
        resposta = exc.get_response()
        resposta.set_data(pagina)
        return resposta

    @app.errorhandler(ErroDeNegocio)
    def negocio(exc):
        return erro(422, 'Confira os dados', 'Não foi possível realizar a operação informada.', 'M04')

    @app.errorhandler(ConflitoDeHistorico)
    def conflito(exc):
        return erro(409, 'Histórico atualizado', 'Consulte o estado atual antes de continuar.', atencao=True)

    @app.errorhandler(ResultadoIncerto)
    def incerto(exc):
        original = g.get('estadia_autorizada')
        consulta = url_for('cliente.estadia', estadia_id=original) if original is not None else destino()
        return erro(503, 'Resultado incerto', 'Consulte a estadia original antes de qualquer novo envio.',
                    acao='Consultar estado', retorno=consulta, atencao=True)

    @app.errorhandler(ErroDeInfraestrutura)
    @app.errorhandler(500)
    def indisponivel(exc):
        # Somente consultas conhecidas podem ser retomadas. Um POST nunca é repetido.
        leitura = request.method == 'GET' and request.endpoint in {
            'gestao.inicio', 'cliente.inicio', 'cliente.estadia', 'acesso.entrar',
        }
        return erro(503, 'Serviço indisponível', 'Os dados não puderam ser consultados agora.',
                    acao='Repetir consulta' if leitura else 'Voltar ao início',
                    retorno=request.path if leitura else None)

    @app.cli.command('criar-conta')
    @click.option('--usuario', required=True)
    @click.option('--papel', type=click.Choice([p.value for p in PapelAcesso]), required=True)
    @click.option('--cliente-id', help='UUID cadastral para uma conta pessoal.')
    def criar_conta(usuario, papel, cliente_id):
        """Provisiona uma conta local com senha informada no terminal."""
        senha = click.prompt('Senha', hide_input=True, confirmation_prompt='Repita a senha')
        try:
            autenticacao.provisionar(usuario, senha, papel, cliente_id)
        except (ValueError, ErroDeInfraestrutura) as exc:
            raise click.ClickException(str(exc)) from exc
        click.echo('Conta criada.')

    return app
