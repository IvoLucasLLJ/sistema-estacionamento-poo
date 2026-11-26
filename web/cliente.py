"""Consultas e operações pessoais do titular autenticado."""
from collections import Counter
from datetime import date, datetime

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, url_for

from model.categorias_cliente import PRECOS_CATEGORIA_CENTAVOS, preco_da_mudanca
from service.estacionamento_service import ConflitoDeHistorico, ErroDeInfraestrutura, ErroDeNegocio, ResultadoIncerto
from web.apresentacao import CATEGORIAS, TIPOS, OcupacaoViewModel, PaginaVagas
from web.consultas_pessoais import ConsultasPessoais
from web.contas import PapelAcesso
from web.revisoes import consumir, emitir
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
    s = current_app.extensions['estacionamento']
    titular = g.identidade.cliente_id
    reservas = leitura_parcial(lambda: s.consultar_ocupacao(titular=titular)['minhas_reservas'])
    return render_template('cliente.html', reservas=reservas, autorizacoes=leitura_parcial(lambda: s.autorizacoes(titular)), ativas=ativas, frota=frota, ocupacao=ocupacao)


@cliente.get('/estadias')
def estadias():
    ativas = g.pessoal.ativas()
    frota = leitura_parcial(g.pessoal.veiculos) if ativas else []
    modelos = {v['placa']: v['modelo'] for v in frota or ()}
    return render_template('cliente/estadias.html', ativas=ativas, modelos=modelos)


@cliente.route('/veiculos', methods=['GET', 'POST'])
def veiculos():
    erro = None
    if request.method == 'POST':
        g.consulta_operacao = url_for('cliente.veiculos')
        try:
            current_app.extensions['estacionamento'].cadastrar_veiculo_do_cliente(
                g.identidade.cliente_id, request.form.get('tipo'), request.form.get('placa'), request.form.get('modelo'),
                request.form.get('motorizacao', 'desconhecida'))
        except ErroDeNegocio as exc:
            erro = str(exc)
        else:
            flash('Veículo cadastrado. Você pode adicionar outro abaixo.', 'pessoal')
            return redirect(g.consulta_operacao, code=303)
    frota = g.pessoal.veiculos()
    ativas = leitura_parcial(g.pessoal.ativas) if frota else []
    por_placa = None if ativas is None else {e['placa']: e for e in ativas}
    return render_template('cliente/veiculos.html', frota=frota, por_placa=por_placa, erro=erro), 422 if erro else 200


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
    s = current_app.extensions['estacionamento']
    titular = g.identidade.cliente_id
    dados = s.consultar_ocupacao(titular=titular, detalhada=True)
    ocupadas = {e['placa'] for e in g.pessoal.ativas()}
    reservadas = {r['placa'] for r in dados['minhas_reservas']}
    frota = [v for v in g.pessoal.veiculos() if v['placa'] not in ocupadas | reservadas]
    placa = request.args.get('placa') or (frota[0]['placa'] if frota else '')
    vip = request.args.get('vip') == '1'
    opcoes = s.opcoes_de_vaga(titular, placa, vip=vip) if placa else []
    tipo = request.args.get('classificacao')
    motivos = sorted({v['motivo'] for v in opcoes if v['estado'] == 'livre' and v['motivo']
                      and (not tipo or v['classificacao'] == tipo)})
    compativeis = [v for v in opcoes if not v['motivo']]
    pagina = PaginaVagas.filtrar(compativeis, request.args)
    return render_template('cliente/disponibilidade.html', ocupacao=OcupacaoViewModel.da_consulta(dados),
                           pagina=pagina, frota=frota, placa=placa, vip=vip, motivos=motivos,
                           indicadores=dados['indicadores'], reservas=dados['minhas_reservas'],
                           compativeis=Counter(v['classificacao'] for v in compativeis) if placa else None,
                           consulta=datetime.now().astimezone().isoformat())


@cliente.route('/reservas/<int:vaga>', methods=['GET', 'POST'])
def reservar(vaga):
    s = current_app.extensions['estacionamento']
    titular = g.identidade.cliente_id
    g.consulta_operacao = url_for('cliente.disponibilidade')
    operacao = f'reserva/{vaga}'
    erro = None
    if request.method == 'POST':
        revisada = consumir(operacao)
        try:
            placa = request.form.get('placa')
            if revisada.get('placa') and placa != revisada['placa']:
                raise ErroDeNegocio('A seleção mudou. Revise a reserva.')
            s.reservar_vaga(titular, placa, vaga, vip=revisada['vip'])
        except ErroDeNegocio as exc:
            erro = str(exc)
        else:
            flash(f'Reserva confirmada para a vaga {vaga:03d}.', 'pessoal')
            return redirect(g.consulta_operacao, code=303)
    dados = s.consultar_ocupacao(titular=titular, detalhada=True)
    disponivel = vaga in dados['numeros_livres']
    indisponiveis = {e['placa'] for e in g.pessoal.ativas()} | {r['placa'] for r in dados['minhas_reservas']}
    frota = [v for v in g.pessoal.veiculos() if v['placa'] not in indisponiveis]
    placa = request.args.get('placa', '')
    vip = request.args.get('vip') == '1'
    if placa:
        frota = [v for v in frota if v['placa'] == placa]
    permitidos = []
    for v in frota:
        opcao = next((op for op in s.opcoes_de_vaga(titular, v['placa'], vip=vip) if op['numero'] == vaga), None)
        if opcao and not opcao['motivo']:
            permitidos.append(v)
        elif opcao and placa:
            erro = erro or opcao['motivo']
    frota = permitidos
    return render_template('cliente/reserva.html', vip=vip, vaga=vaga, frota=frota, disponivel=disponivel,
                           erro=erro, revisao=emitir(operacao, dict(placa=placa, vip=vip)) if disponivel and frota else None), (
                               409 if erro or not disponivel else 200)


@cliente.post('/reservas/<int:vaga>/<int:reserva_id>/cancelar')
def cancelar_reserva(vaga, reserva_id):
    g.consulta_operacao = url_for('cliente.disponibilidade')
    current_app.extensions['estacionamento'].cancelar_reserva(g.identidade.cliente_id, vaga, reserva_id)
    flash('Reserva cancelada. A vaga está disponível novamente.', 'pessoal')
    return redirect(g.consulta_operacao, code=303)


@cliente.get('/tarifas')
def tarifas():
    s = current_app.extensions['estacionamento']
    beneficios = {'comum': 'Cobrança integral', 'vip': '50% de desconto',
                  'mensalista': 'Valor zero por utilização'}
    return render_template('cliente/tarifas.html', tarifas=s.consultar_tarifas(), beneficios=beneficios,
                           precos=PRECOS_CATEGORIA_CENTAVOS, mudancas=s.mudancas_de_categoria(g.identidade.cliente_id))


@cliente.route('/tarifas/<categoria>', methods=['GET', 'POST'])
def mudar_categoria(categoria):
    if categoria not in PRECOS_CATEGORIA_CENTAVOS:
        abort(404)
    g.consulta_operacao = url_for('cliente.tarifas')
    operacao = f'categoria/{categoria}'
    if request.method == 'POST':
        dados = consumir(operacao)
        try:
            current_app.extensions['estacionamento'].mudar_categoria(
                g.identidade.cliente_id, dados['origem'], categoria)
        except ErroDeNegocio:
            abort(409)
        flash(f'Categoria alterada para {CATEGORIAS[categoria]}.', 'pessoal')
        return redirect(g.consulta_operacao, code=303)
    origem = g.cliente['categoria']
    if categoria == origem:
        return redirect(g.consulta_operacao)
    return render_template('cliente/mudanca_categoria.html', categoria=categoria,
                           valor=preco_da_mudanca(origem, categoria), revisao=emitir(operacao, dict(origem=origem)))


@cliente.get('/perfil')
def perfil():
    return render_template('cliente/perfil.html')
