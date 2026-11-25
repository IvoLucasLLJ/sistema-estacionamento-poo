from flask import Blueprint, current_app, g, redirect, render_template, request, session, url_for

from web.seguranca import acesso_restrito, destino, iniciar_sessao

acesso = Blueprint('acesso', __name__)


@acesso.get('/')
def raiz():
    return redirect(destino())


@acesso.route('/entrar', methods=['GET', 'POST'])
def entrar():
    if g.identidade is not None:
        return redirect(destino())
    if request.method == 'POST':
        identidade = current_app.extensions['autenticacao'].autenticar(
            request.form.get('usuario'), request.form.get('senha'))
        if identidade:
            iniciar_sessao(identidade)
            g.identidade = identidade
            return redirect(destino(), code=303)
        return render_template('login.html', erro='Usuário ou senha inválidos.'), 401
    return render_template('login.html')


@acesso.post('/sair')
@acesso_restrito()
def sair():
    session.clear()
    return redirect(url_for('acesso.entrar'), code=303)
