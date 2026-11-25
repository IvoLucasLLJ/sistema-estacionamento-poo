"""Portal consultivo do titular autenticado."""
from datetime import date, datetime

from flask import Blueprint, abort, current_app, g, render_template, request

from service.estacionamento_service import ConflitoDeHistorico, ErroDeInfraestrutura, ResultadoIncerto
from web.apresentacao import CATEGORIAS, TIPOS, OcupacaoViewModel
from web.consultas_pessoais import ConsultasPessoais
from web.contas import PapelAcesso
from web.seguranca import acesso_restrito, estadia_do_titular

cliente = Blueprint('cliente', __name__, url_prefix='/cliente')


@cliente.before_request
@acesso_restrito(PapelAcesso.CLIENTE)
def identificar():
    g.pessoal = ConsultasPessoais(current_app.extensions['estacionamento'], g.identidade.cliente_id)


@cliente.context_processor
def contexto():
    return dict(cadastro=g.get('cliente'), categorias=CATEGORIAS, tipos=TIPOS)


def ocupacao_atual():
    return OcupacaoViewModel.da_consulta(current_app.extensions['estacionamento'].consultar_ocupacao())


def leitura_parcial(ler):
    try:
        return ler()
    except (ConflitoDeHistorico, ResultadoIncerto):
        raise
    except ErroDeInfraestrutura:
        return None


@cliente.get('/')
def inicio():
    ativas = leitura_parcial(g.pessoal.ativas)
    frota = leitura_parcial(g.pessoal.veiculos)
    ocupacao = leitura_parcial(ocupacao_atual)
    if ativas is None and frota is None and ocupacao is None:
        raise ErroDeInfraestrutura('Consultas pessoais indisponíveis.')
    return render_template('cliente.html', ativas=ativas, frota=frota, ocupacao=ocupacao)


@cliente.get('/estadias')
def estadias():
    ativas = g.pessoal.ativas()
    frota = leitura_parcial(g.pessoal.veiculos) if ativas else []
    modelos = {v['placa']: v['modelo'] for v in frota or ()}
    return render_template('cliente/estadias.html', ativas=ativas, modelos=modelos)


@cliente.get('/veiculos')
def veiculos():
    frota = g.pessoal.veiculos()
    ativas = leitura_parcial(g.pessoal.ativas) if frota else []
    por_placa = None if ativas is None else {e['placa']: e for e in ativas}
    return render_template('cliente/veiculos.html', frota=frota, por_placa=por_placa)


@cliente.get('/estadias/<int:estadia_id>')
def estadia(estadia_id):
    e = estadia_do_titular(estadia_id)
    veiculo = current_app.extensions['estacionamento'].buscar_veiculo(e['placa'])
    outras = []
    if e['situacao'] == 'ativa':
        outras = [ativa for ativa in g.pessoal.ativas() if ativa['estadia_id'] != estadia_id]
    return render_template('cliente/estadia.html', e=e, v=veiculo, outras=outras)


@cliente.get('/estadias/<int:estadia_id>/comprovante')
def comprovante(estadia_id):
    e = estadia_do_titular(estadia_id)
    if e['situacao'] != 'concluida':
        abort(404)
    v = current_app.extensions['estacionamento'].buscar_veiculo(e['placa'])
    return render_template('cliente/estadia.html', e=e, v=v, comprovante=True)


@cliente.get('/historico')
def historico():
    lista = g.pessoal.historico()
    placas = sorted({e['placa'] for e in lista})
    estados = {'ativa': 'Ativa sem confirmação', 'aguardando': 'Pagamento confirmado · Ainda estacionado',
               'paga': 'Saída paga', 'isenta': 'Saída isenta'}
    placa = request.args.get('placa', '')
    estado = request.args.get('estado', '')
    try:
        inicio, fim = (date.fromisoformat(request.args[campo]) if request.args.get(campo) else None
                       for campo in ('inicio', 'fim'))
        if inicio and fim and inicio > fim:
            raise ValueError
    except ValueError:
        return render_template('cliente/historico.html', placas=placas, estados=estados,
                               erro='Confira as datas de entrada e a ordem do período.'), 422

    resultado = []
    for e in lista:
        dia = datetime.fromisoformat(e['horario_entrada']).date()
        if (not placa or e['placa'] == placa) and (not estado or e['estado'] == estado):
            if (not inicio or dia >= inicio) and (not fim or dia <= fim):
                resultado.append(e)
    return render_template('cliente/historico.html', lista=resultado, placas=placas, estados=estados,
                           possui_historico=bool(lista))


@cliente.get('/disponibilidade')
def disponibilidade():
    ocupacao = ocupacao_atual()
    return render_template('cliente/disponibilidade.html', ocupacao=ocupacao,
                           consulta=datetime.now().astimezone().isoformat())


@cliente.get('/tarifas')
def tarifas():
    tabela = current_app.extensions['estacionamento'].consultar_tarifas()
    beneficios = {'comum': 'Cobrança integral', 'vip': '50% de desconto',
                  'mensalista': 'Valor zero por utilização'}
    return render_template('cliente/tarifas.html', tarifas=tabela, beneficios=beneficios)


@cliente.get('/perfil')
def perfil():
    return render_template('cliente/perfil.html')
