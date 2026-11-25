from flask import Blueprint, current_app, g, redirect, render_template, request, session, url_for

from web.apresentacao import OcupacaoViewModel
from web.contas import PapelAcesso
from web.seguranca import acesso_restrito, destino, estadia_do_titular, iniciar_sessao

acesso = Blueprint('acesso', __name__)
cliente = Blueprint('cliente', __name__, url_prefix='/cliente')


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


@cliente.get('/', endpoint='inicio')
@cliente.get('/estadias/<int:estadia_id>', endpoint='estadia')
@acesso_restrito(PapelAcesso.CLIENTE)
def inicio_cliente(estadia_id=None):
    servico = current_app.extensions['estacionamento']
    selecionada = estadia_do_titular(estadia_id) if estadia_id is not None else None
    titular = g.identidade.cliente_id
    ativas = [e for e in servico.listar_estadias_ativas() if e['cliente_id'] == titular]
    return render_template('cliente.html', cadastro=g.cliente, selecionada=selecionada,
                           ativas=ativas, veiculos=servico.veiculos_do_cliente(titular),
                           ocupacao=OcupacaoViewModel.da_consulta(servico.consultar_ocupacao()))
