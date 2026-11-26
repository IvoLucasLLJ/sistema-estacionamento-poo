from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, url_for

from service.estacionamento_service import ErroDeInfraestrutura
from web.seguranca import acesso_restrito, csrf_token, destino, encerrar_sessao, iniciar_sessao, selecionar_ambiente

acesso = Blueprint('acesso', __name__)


@acesso.get('/')
def raiz():
    return redirect(destino())


@acesso.route('/entrar', methods=['GET', 'POST'])
def entrar():
    if g.identidade is not None:
        return redirect(destino())
    if request.method == 'POST':
        if len(request.form.getlist('ambiente')) > 1:
            abort(400)
        identidade = current_app.extensions['autenticacao'].autenticar(
            request.form.get('usuario'), request.form.get('senha'))
        if identidade:
            iniciar_sessao(identidade, request.form.get('ambiente'))
            return redirect(destino(), code=303)
        return render_template('login.html', erro='Usuário ou senha inválidos.'), 401
    return render_template('login.html')


@acesso.route('/criar-conta', methods=['GET', 'POST'])
def criar_conta():
    if g.identidade is not None:
        return redirect(destino())
    revisoes = current_app.extensions['revisoes']
    operacao = 'cadastro_pessoal'
    erro, status = None, 200
    if request.method == 'POST':
        formulario = request.form
        campos = {'nome', 'usuario', 'senha', 'confirmacao', 'csrf_token', 'revisao'}
        if set(formulario) != campos or any(len(formulario.getlist(c)) != 1 for c in campos):
            abort(400)
        if revisoes.obter(formulario['revisao'], csrf_token(), operacao, consumir=True) is None:
            abort(409)
        try:
            current_app.extensions['autenticacao'].cadastrar_pessoal(
                formulario['nome'], formulario['usuario'], formulario['senha'], formulario['confirmacao'])
        except ValueError as exc:
            erro, status = str(exc), 422
        except ErroDeInfraestrutura:
            erro = ('Não foi possível confirmar o cadastro. Tente entrar com o usuário e a senha '
                    'escolhidos para retomar. Se o usuário ainda não existir, volte a criar a conta.')
            status = 503
        else:
            flash('Conta criada. Entre com seu usuário e senha.', 'cadastro')
            return redirect(url_for('acesso.entrar'), code=303)
    return render_template('cadastro.html', erro=erro, revisao=revisoes.emitir(csrf_token(), operacao),
                           nome=request.form.get('nome', ''), usuario=request.form.get('usuario', '')), status


@acesso.post('/ambiente')
@acesso_restrito()
def alternar_ambiente():
    selecionar_ambiente(request.form.get('ambiente'))
    return redirect(destino(), code=303)


@acesso.post('/sair')
@acesso_restrito()
def sair():
    encerrar_sessao()
    return redirect(url_for('acesso.entrar'), code=303)
