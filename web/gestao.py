"""Operação administrativa. Toda leitura e escrita operacional passa pelo serviço."""
from datetime import date

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, url_for

from service.estacionamento_service import ConflitoDeHistorico, ErroDeInfraestrutura, ErroDeNegocio, ResultadoIncerto
from web.apresentacao import CATEGORIAS, TIPOS, OcupacaoViewModel, PaginaVagas, centavos, dinheiro, horario
from web.contas import PapelAcesso
from web.eventos import ROTULOS, RelatorioSaidas, eventos_identificados
from web.revisoes import consumir, emitir
from web.seguranca import acesso_restrito, csrf_token

gestao = Blueprint('gestao', __name__, url_prefix='/gestao')
PAGAMENTOS = {'sem_confirmacao': 'Sem confirmação', 'confirmado': 'Pagamento confirmado',
              'isento': 'Isento', 'legado': 'Legado'}


@gestao.before_request
@acesso_restrito(PapelAcesso.GESTAO)
def verificar_papel():
    return None


@gestao.context_processor
def rotulos():
    return dict(categorias=CATEGORIAS, tipos=TIPOS, pagamentos=PAGAMENTOS)


def servico():
    return current_app.extensions['estacionamento']


def buscar(operacao, chave):
    try:
        return operacao(chave)
    except ErroDeNegocio:
        abort(404)


def ir(endpoint, **valores):
    return redirect(url_for('gestao.' + endpoint, **valores), code=303)


@gestao.get('/')
def inicio():
    servico = current_app.extensions['estacionamento']
    leitura = servico.consultar_ocupacao(detalhada=True)
    ocupacao = OcupacaoViewModel.da_consulta(leitura)
    try:
        financeiro = servico.consultar_faturamento()
        pendentes = len(servico.listar_pagamentos_abertos())
    except (ConflitoDeHistorico, ResultadoIncerto):
        raise
    except ErroDeInfraestrutura:
        financeiro = pendentes = None
    return render_template('gestao.html', ocupacao=ocupacao, vagas=PaginaVagas.filtrar(leitura['mapa'], {}).vagas,
                           indicadores=leitura['indicadores'],
                           financeiro=financeiro, pendentes=pendentes)


@gestao.get('/vagas')
def vagas():
    lista = servico().consultar_vagas()
    numero = request.args.get('vaga', type=int)
    selecao = next((v for v in lista if v['numero'] == numero), None)
    if 'vaga' in request.args and not selecao:
        abort(400)
    ativas = {e['vaga']: e for e in servico().listar_estadias_ativas()}
    pagina = PaginaVagas.filtrar(lista, request.args)
    chave = emitir(f'carregador/{numero}', dict(disponivel=not selecao['carregador'])) if selecao and selecao['carregador'] is not None else None
    return render_template('gestao/vagas.html', vagas=pagina.vagas, pagina=pagina, selecao=selecao,
                           ativas=ativas, revisao=chave)


@gestao.post('/vagas/<int:numero>/carregador')
def carregador(numero):
    dados = consumir(f'carregador/{numero}')
    g.consulta_operacao = url_for('gestao.vagas', vaga=numero)
    servico().alterar_carregador(numero, dados['disponivel'])
    return ir('vagas', vaga=numero)


@gestao.post('/clientes/<identificador>/autorizacoes')
def conferir(identificador):
    consumir(f'conferir/{identificador}')
    g.consulta_operacao = url_for('gestao.cliente', identificador=identificador)
    servico().conferir_autorizacao(identificador, *(request.form.get(k, '') for k in
                                   ('placa', 'grupo', 'beneficiario', 'conferencia', 'validade')),
                                  numero_beneficiario=request.form.get('numero_beneficiario', type=int))
    flash('Conferência simulada registrada.')
    return ir('cliente', identificador=identificador)


@gestao.post('/clientes/<identificador>/autorizacoes/<int:numero>/revogar')
def revogar(identificador, numero):
    g.consulta_operacao = url_for('gestao.cliente', identificador=identificador)
    consumir(f'revogar/{identificador}/{numero}')
    servico().revogar_autorizacao(identificador, numero)
    return ir('cliente', identificador=identificador)


@gestao.get('/estadias')
def estadias():
    busca = request.args.get('q', '').strip().casefold()
    estado = request.args.get('pagamento', '')
    clientes = {c['identificador']: c['nome'] for c in servico().listar_clientes()}
    lista = []
    for e in servico().listar_estadias_ativas():
        nome = clientes.get(e['cliente_id'], '')
        if (not estado or estado == e['pagamento']) and coincide(
                busca, e['placa'], e['estadia_id'], nome, e['cliente_id']):
            lista.append(dict(e, nome=nome))
    return render_template('gestao/estadias.html', lista=lista)


def coincide(busca, *valores):
    return any(busca in str(v).casefold() for v in valores if v is not None)


@gestao.route('/clientes', methods=['GET', 'POST'])
def clientes():
    erro = None
    if request.method == 'POST':
        g.consulta_operacao = url_for('gestao.clientes')
        consumir('cliente')
        try:
            novo = servico().cadastrar_cliente(request.form.get('categoria'), request.form.get('nome'))
        except ErroDeNegocio as exc:
            erro = str(exc)
        else:
            flash('Cliente cadastrado.')
            return ir('cliente', identificador=novo['identificador'])
    busca = request.args.get('q', '').strip().casefold()
    categoria = request.args.get('categoria', '')
    lista = [c for c in servico().listar_clientes() if (not categoria or categoria == c['categoria'])
             and coincide(busca, c['nome'], c['identificador'])]
    lista.sort(key=lambda c: (c['nome'].casefold(), c['identificador']))
    return render_template('gestao/clientes.html', lista=lista, revisao=emitir('cliente'), erro=erro), 422 if erro else 200


@gestao.route('/veiculos', methods=['GET', 'POST'])
def veiculos():
    erro = None
    if request.method == 'POST':
        g.consulta_operacao = url_for('gestao.veiculos', q=request.form.get('placa'))
        consumir('veiculo')
        try:
            novo = servico().cadastrar_veiculo(request.form.get('tipo'), request.form.get('placa'),
                                               request.form.get('modelo'), request.form.get('motorizacao', 'desconhecida'))
        except ErroDeNegocio as exc:
            erro = str(exc)
        else:
            flash('Veículo cadastrado.')
            return ir('veiculo', placa=novo['placa'])
    busca = request.args.get('q', '').strip().replace('-', '').replace(' ', '').casefold()
    tipo = request.args.get('tipo', '')
    lista = [v for v in servico().listar_veiculos() if (not tipo or tipo == v['tipo'])
             and coincide(busca, v['placa'])]
    return render_template('gestao/veiculos.html', lista=lista, revisao=emitir('veiculo'), erro=erro), 422 if erro else 200


@gestao.get('/clientes/<identificador>')
def cliente(identificador):
    s = servico()
    c = buscar(s.buscar_cliente, identificador)
    chave = c['identificador']
    eventos = eventos_identificados(s.consultar_historico())
    frota = s.veiculos_do_cliente(chave)
    vinculados = {e['placa'] for e in eventos if e['acao'] == 'vinculo'}
    ativas = s.listar_estadias_ativas()
    ocupadas = {e['placa'] for e in ativas}
    inelegiveis = vinculados | ocupadas
    elegiveis = [v for v in s.listar_veiculos() if v['placa'] not in inelegiveis]
    autorizacoes = s.autorizacoes(chave)
    revogacoes = {a.identificador: emitir(f'revogar/{chave}/{a.identificador}') for a in autorizacoes}
    return render_template('gestao/cliente.html', c=c, frota=frota, elegiveis=elegiveis, autorizacoes=autorizacoes, revogacoes=revogacoes,
                           conferir_revisao=emitir(f'conferir/{chave}'),
                           ativas=[e for e in ativas if e['cliente_id'] == chave],
                           eventos=[e for e in eventos if e.get('cliente_id') == chave])


@gestao.get('/veiculos/<placa>')
def veiculo(placa):
    s = servico()
    v = buscar(s.buscar_veiculo, placa)
    ativo = next((e for e in s.listar_estadias_ativas() if e['placa'] == v['placa']), None)
    dono = s.cliente_do_veiculo(v['placa'])
    return render_template('gestao/veiculo.html', v=v, dono=dono, ativo=ativo,
                           clientes=[] if dono or ativo else s.listar_clientes())


@gestao.post('/clientes/<identificador>/veiculos')
def cadastrar_veiculo_do_cliente(identificador):
    g.consulta_operacao = url_for('gestao.cliente', identificador=identificador)
    servico().cadastrar_veiculo_do_cliente(identificador, request.form.get('tipo'),
                                          request.form.get('placa'), request.form.get('modelo'), request.form.get('motorizacao', 'desconhecida'))
    flash('Veículo cadastrado e vinculado ao cliente.')
    return ir('cliente', identificador=identificador)


@gestao.post('/vinculos')
def vincular():
    g.consulta_operacao = url_for('gestao.veiculos', q=request.form.get('placa'))
    resultado = servico().vincular_veiculo(request.form.get('placa'), request.form.get('cliente_id'))
    flash('Vínculo registrado.')
    return ir('veiculo', placa=resultado['placa'])


def dados_entrada(cliente_id, placa, vaga):
    s = servico()
    clientes = s.listar_clientes()
    dono = s.buscar_cliente(cliente_id) if cliente_id else None
    frota = s.veiculos_do_cliente(dono['identificador']) if dono else []
    vagas = s.consultar_vagas()
    ocupadas = {v['placa'] for v in vagas if v['ocupada']}
    placa = placa or next((v['placa'] for v in frota if v['placa'] not in ocupadas), '')
    opcoes = s.opcoes_de_vaga(cliente_id, placa, entrada=True) if any(v['placa'] == placa for v in frota) else []
    disponiveis = [v for v in opcoes if not v['motivo']]
    restricoes = sorted({v['motivo'] for v in opcoes if v['motivo'] and v['estado'] != 'ocupada'})
    return dict(clientes=clientes, dono=dono, frota=frota, vagas=vagas, restricoes=restricoes,
                ocupadas=ocupadas, disponiveis=disponiveis, placa=placa, vaga=vaga)


@gestao.route('/entrada', methods=['GET', 'POST'])
def entrada():
    if request.method == 'POST':
        g.consulta_operacao = url_for('gestao.historico', acao='entrada_cliente')
        dados = consumir('entrada')
        if dados.pop('protegida', False) and request.form.get('presente') != 'sim':
            abort(400)
        g.consulta_operacao = url_for('gestao.historico', q=dados['placa'], acao='entrada_cliente')
        expectativa = dados.pop('expectativa_uso')
        try:
            e = servico().iniciar_estadia(**dados, expectativa_uso=expectativa, beneficiario_presente=request.form.get('presente') == 'sim')
        except ErroDeNegocio as exc:
            contexto = dados_entrada(**dados)
            return render_template('gestao/entrada.html', **contexto, erro=str(exc)), 409
        flash('Entrada registrada.')
        return ir('detalhe_estadia', numero=e['estadia_id'])

    cliente_id = request.args.get('cliente_id', '')
    placa = request.args.get('placa', '')
    vaga = request.args.get('vaga', type=int)
    contexto = dados_entrada(cliente_id, placa, vaga)
    if 'revisar' in request.args:
        veiculo = next((v for v in contexto['frota'] if v['placa'] == placa), None)
        disponivel = any(v['numero'] == vaga for v in contexto['disponiveis'])
        if not veiculo or not disponivel:
            return render_template('gestao/entrada.html', **contexto,
                                   erro='Confira o vínculo, a situação do veículo e a vaga disponível.'), 422
        dados = dict(cliente_id=cliente_id, placa=placa, vaga=vaga)
        selecionada = next(v for v in contexto['disponiveis'] if v['numero'] == vaga)
        dados['expectativa_uso'] = {k: selecionada[k] for k in ('classificacao','vip','reserva_id','conferencia')}
        dados['protegida'] = selecionada['classificacao'] not in ('comum', 'eletrica')
        contexto.update(revisao=emitir('entrada', dados), veiculo=veiculo, selecionada=selecionada)
    return render_template('gestao/entrada.html', **contexto)


def contexto_estadia(numero):
    e = buscar(servico().consultar_estadia, numero)
    dono = servico().buscar_cliente(e['cliente_id'])
    v = servico().buscar_veiculo(e['placa'])
    return dict(e=e, dono=dono, v=v)


def consulta_original(numero):
    return url_for('gestao.detalhe_estadia', numero=numero, recuperar=1)


@gestao.get('/estadias/<int:numero>')
def detalhe_estadia(numero):
    contexto = contexto_estadia(numero)
    e = contexto['e']
    chave = None
    if e['situacao'] == 'ativa' and e['pagamento'] == 'confirmado':
        chave = emitir(f'saida/{numero}', e['cobranca'])
    return render_template('gestao/estadia.html', **contexto, revisao=chave)


@gestao.get('/estadias/<int:numero>/saida')
def saida(numero):
    contexto = contexto_estadia(numero)
    e = contexto['e']
    if e['situacao'] != 'ativa' or e['pagamento'] == 'confirmado':
        return ir('detalhe_estadia', numero=numero)
    cotacao = chave = erro = None
    if 'horas' in request.args:
        horas = request.args['horas'].strip().replace(',', '.')
        try:
            cotacao = servico().consultar_cobranca(e['placa'], horas)
            if cotacao['estadia_id'] != numero:
                return ir('detalhe_estadia', numero=numero)
            operacao = 'pagamento' if cotacao['valor_centavos'] else 'saida'
            chave = emitir(f'{operacao}/{numero}', cotacao)
        except ErroDeNegocio as exc:
            erro = str(exc)
    return render_template('gestao/saida.html', **contexto, cotacao=cotacao,
                           revisao=chave, erro=erro), 422 if erro else 200


@gestao.route('/estadias/<int:numero>/pagamento', methods=['GET', 'POST'])
def pagamento(numero):
    g.consulta_operacao = consulta_original(numero)
    operacao = f'pagamento/{numero}'
    if request.method == 'POST':
        c = consumir(operacao)
        if request.form.get('decisao') == 'cancelar':
            return ir('saida', numero=numero)
        if request.form.get('decisao') != 'confirmar':
            abort(400)
        try:
            servico().confirmar_pagamento(c['placa'], c['horas'], c, confirmado=True)
        except ErroDeNegocio:
            return revisao_superada(numero)
        flash('Pagamento confirmado. A vaga continua ocupada.')
        return ir('detalhe_estadia', numero=numero)
    chave = request.args.get('revisao', '')
    c = current_app.extensions['revisoes'].obter(chave, csrf_token(), operacao)
    if c is None:
        abort(409)
    contexto = contexto_estadia(numero)
    if contexto['e']['situacao'] != 'ativa' or contexto['e']['pagamento'] != 'sem_confirmacao':
        return revisao_superada(numero)
    return render_template('gestao/pagamento.html', **contexto, cotacao=c, revisao=chave)


def revisao_superada(numero):
    return render_template('erro.html', titulo='Cotação desatualizada', modelo='M08',
                           mensagem='Consulte a estadia original e revise a situação atual.',
                           retorno=consulta_original(numero), acao='Consultar estado', atencao=True), 409


@gestao.post('/estadias/<int:numero>/concluir')
def concluir(numero):
    g.consulta_operacao = consulta_original(numero)
    c = consumir(f'saida/{numero}')
    try:
        servico().concluir_saida(c['placa'], c['horas'], c)
    except ErroDeNegocio:
        return revisao_superada(numero)
    flash('Saída concluída. Vaga liberada.')
    return ir('detalhe_estadia', numero=numero)


@gestao.get('/pagamentos')
def fila():
    nomes = {c['identificador']: c['nome'] for c in servico().listar_clientes()}
    lista = [dict(e, nome=nomes.get(e['cliente_id'])) for e in servico().listar_estadias_ativas()
             if e['pagamento'] == 'confirmado']
    return render_template('gestao/fila.html', lista=lista)


def campos_do_evento(evento):
    campos = [
        ('placa', 'Placa', str), ('cliente_id', 'UUID do cliente', str), ('nome', 'Cliente', str),
        ('categoria', 'Categoria', CATEGORIAS.get), ('tipo', 'Tipo', TIPOS.get), ('modelo', 'Modelo', str),
        ('classificacao', 'Classificação da vaga', str), ('vip', 'Destinação VIP', lambda v: 'Sim' if v else 'Não'),
        ('vaga', 'Vaga', lambda n: f'{n:03d}'), ('estadia_id', 'Estadia', str), ('horario_entrada', 'Entrada', horario),
        ('horario_saida', 'Saída', horario), ('horas', 'Duração (h)', lambda h: str(h).replace('.', ',')),
        ('tarifa_base', 'Tarifa-base', dinheiro), ('desconto', 'Desconto', dinheiro),
        ('valor', 'Valor legado', dinheiro), ('valor_centavos', 'Valor definitivo', centavos),
        ('origem', 'Categoria anterior', CATEGORIAS.get), ('reserva_id', 'Reserva', str),
        ('pagamento', 'Situação financeira', PAGAMENTOS.get),
    ]
    return [(rotulo, formatar(evento[chave])) for chave, rotulo, formatar in campos
            if evento.get(chave) is not None]


@gestao.get('/historico')
def historico():
    lista = eventos_identificados(servico().consultar_historico())
    numero = request.args.get('evento', type=int)
    detalhe = None
    if 'evento' in request.args:
        if numero is None or not 1 <= numero <= len(lista):
            abort(404)
        detalhe = lista[numero - 1]
    busca = request.args.get('q', '').strip().casefold()
    acao = request.args.get('acao', '')
    lista = [e for e in lista if (not acao or e['acao'] == acao)
             and coincide(busca, e['numero'], e.get('placa'), e.get('cliente_id'),
                          e.get('nome'), e.get('estadia_id'))]
    return render_template('gestao/historico.html', eventos=lista, acoes=ROTULOS, detalhe=detalhe,
                           campos=campos_do_evento(detalhe) if detalhe else [])


@gestao.get('/relatorios')
def relatorios():
    datas = []
    try:
        for campo in ('inicio', 'fim'):
            texto = request.args.get(campo)
            datas.append(date.fromisoformat(texto) if texto else None)
    except ValueError:
        raise ErroDeNegocio('Informe datas válidas para a saída.') from None
    inicio, fim = datas
    if inicio and fim and inicio > fim:
        raise ErroDeNegocio('A data inicial deve preceder ou coincidir com a data final.')
    s = servico()
    relatorio = RelatorioSaidas.do_periodo(eventos_identificados(s.consultar_historico()), inicio, fim)
    leitura = s.consultar_ocupacao(detalhada=True)
    return render_template('gestao/relatorios.html', rel=relatorio,
                           ocupacao=OcupacaoViewModel.da_consulta(leitura),
                           faturamento=s.consultar_faturamento(), indicadores=leitura['indicadores'])
