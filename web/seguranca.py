import hmac
import secrets
from functools import wraps
from time import time as agora

from flask import abort, current_app, g, redirect, request, session, url_for
from werkzeug.exceptions import SecurityError

from service.estacionamento_service import ErroDeInfraestrutura, ErroDeNegocio
from web.contas import PapelAcesso


def csrf_token():
    if 'csrf' not in session:
        session['csrf'] = secrets.token_urlsafe(32)
    return session['csrf']


def iniciar_sessao(identidade):
    session.clear()
    session['conta'] = identidade.id
    session['expira'] = int(agora()) + current_app.config['DURACAO_SESSAO']
    csrf_token()


def destino():
    if g.identidade is None:
        return url_for('acesso.entrar')
    return url_for('gestao.inicio' if g.identidade.papel == PapelAcesso.GESTAO else 'cliente.inicio')


def preparar_requisicao():
    g.identidade = None
    g.contexto = None
    if isinstance(request.routing_exception, SecurityError):
        # O Flask recusou o host antes de criar o adaptador usado pelos templates.
        return 'Endereço de acesso inválido.', 400, {'Content-Type': 'text/plain; charset=utf-8'}
    if request.endpoint == 'static':
        return
    try:
        current_app.extensions['escritor'].abrir()
    except OSError as erro:
        raise ErroDeInfraestrutura('Histórico indisponível para este processo.') from erro
    if 'conta' in session:
        if agora() >= session.get('expira', 0):
            session.clear()
            abort(401)
        g.contexto = current_app.extensions['autenticacao'].contexto(
            session['conta'], current_app.config['VINCULOS_PORTAIS'],
            titular_demo=current_app.config.get('TITULAR_DEMO'))
        if g.contexto:
            g.identidade = g.contexto.identidade_ativa(session.get('conta_pessoal_ativa'))
        if g.identidade is None:
            session.clear()
            abort(401)
    if request.method not in {'GET', 'HEAD', 'OPTIONS'}:
        recebido = request.form.get('csrf_token', '')
        esperado = session.get('csrf')
        if not esperado or not hmac.compare_digest(recebido.encode(), esperado.encode()):
            abort(400)


def cliente_vinculado(identidade):
    try:
        return current_app.extensions['estacionamento'].buscar_cliente(identidade.cliente_id)
    except ErroDeNegocio:
        abort(404)


def selecionar_ambiente(ambiente):
    if ambiente not in {papel.value for papel in PapelAcesso}:
        abort(400)
    identidade = g.contexto.identidade_para(ambiente)
    if identidade is None:
        abort(403)
    if identidade != g.identidade:
        if identidade.papel == PapelAcesso.CLIENTE:
            cliente_vinculado(identidade)
            session['conta_pessoal_ativa'] = identidade.id
        else:
            session.pop('conta_pessoal_ativa', None)
        current_app.extensions['revisoes'].invalidar_sessao(session.pop('csrf'))
        csrf_token()
        g.identidade = identidade


def acesso_restrito(papel=None):
    def decorar(view):
        @wraps(view)
        def protegida(*args, **kwargs):
            if g.identidade is None:
                return redirect(url_for('acesso.entrar'))
            if papel is not None and g.identidade.papel != papel:
                abort(403)
            if papel == PapelAcesso.CLIENTE:
                g.cliente = cliente_vinculado(g.identidade)
            return view(*args, **kwargs)
        return protegida
    return decorar


def estadia_do_titular(estadia_id):
    try:
        dados = current_app.extensions['estacionamento'].consultar_estadia(estadia_id)
    except ErroDeNegocio:
        abort(404)
    if g.identidade.papel != PapelAcesso.CLIENTE or dados['cliente_id'] != g.identidade.cliente_id:
        abort(404)
    g.estadia_autorizada = dados['estadia_id']
    return dados
