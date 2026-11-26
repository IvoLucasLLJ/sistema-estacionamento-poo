"""Projeções de leitura do MOVE. Os objetos do domínio ficam dentro da operação."""
from datetime import date
from model.vaga import VAGAS_POR_SETOR
from model.uso_vaga import CLASSIFICACOES
from decimal import Decimal, InvalidOperation


def cliente(objeto):
    return {"identificador": objeto.identificador, "categoria": objeto.categoria, "nome": objeto.nome}


def veiculo(objeto):
    return {"placa": objeto.placa, "tipo": type(objeto).__name__.lower(), "modelo": objeto.modelo,
            "motorizacao": objeto.motorizacao}


def cobranca(objeto):
    return {**objeto.dados_do_pagamento(), "tarifa_base": str(objeto.tarifa_base),
            "desconto": str(objeto.desconto)}


def decimal_de_texto(texto):
    try:
        return Decimal(texto)
    except InvalidOperation as erro:
        raise ValueError("Informe um texto decimal válido.") from erro


def conferir_expectativa(atual, expectativa):
    """Compara o DTO recebido com a cotação do domínio, inclusive os tipos do JSON."""
    if not isinstance(expectativa, dict):
        raise ValueError("Informe a cobrança consultada.")
    for campo, esperado in cobranca(atual).items():
        recebido = expectativa.get(campo)
        if type(recebido) is not type(esperado):
            raise ValueError(f"Campo de cobrança inválido: {campo}.")
        if campo in ("horas", "tarifa_base", "desconto"):
            recebido = decimal_de_texto(recebido)
            esperado = Decimal(esperado)
            if not recebido.is_finite():
                raise ValueError(f"O campo {campo} deve ser finito.")
        if recebido != esperado:
            raise ValueError(f"A cobrança consultada diverge da estadia atual: {campo}.")


def vagas(ctrl):
    resultado = []
    for vaga in ctrl.listar_vagas():
        dados = dict(numero=vaga.numero, ocupada=vaga.ocupada, placa=vaga.veiculo.placa if vaga.ocupada else None)
        dados.update(**publica(vaga))
        if vaga.reserva:
            dados.update(placa_reservada=vaga.reserva.placa, titular_reserva=vaga.reserva.cliente_id,
                         reserva_id=vaga.reserva.identificador)
        resultado.append(dados)
    return resultado


def ocupacao(ctrl, titular=None):
    todas = ctrl.listar_vagas()
    dados = {"ocupadas": sum(v.ocupada for v in todas), "livres": sum(v.livre for v in todas), "total": len(todas)}
    if titular is not None:
        dados['numeros_livres'] = [v.numero for v in todas if v.livre]
        dados['minhas_reservas'] = [dict(vaga=v.numero, placa=v.reserva.placa, id=v.reserva.identificador, vip=v.vip, classificacao=v.classificacao)
                                   for v in todas if v.reserva and v.reserva.cliente_id == titular]
    return dados


def faturamento(ctrl):
    reais = Decimal(str(ctrl.relatorio()["faturamento"]))
    numerador, denominador = reais.as_integer_ratio()
    centavos, resto = divmod(numerador * 100, denominador)
    return {"reais": str(reais), "centavos": centavos if resto == 0 else None}


def historico(ctrl):
    eventos = ctrl.consultar_historico()
    for evento in eventos:
        if evento["acao"] == "saida":
            evento["valor"] = str(evento["valor"])
    return eventos


def estadia_do_evento(ctrl, entrada, saida=None):
    dados = {campo: entrada[campo] for campo in ("placa", "tipo", "vaga", "horario_entrada")}
    dados.update(classificacao=entrada.get("classificacao"), vip=entrada.get("vip", False))
    dados.update(estadia_id=None, cliente_id=None, categoria=None, situacao="ativa",
                 horario_saida=None, cobranca=None, pagamento="legado")
    if entrada["acao"] == "entrada":
        return dados

    dados.update({campo: entrada[campo] for campo in ("estadia_id", "cliente_id", "categoria")})
    if saida is not None:
        campos = ("estadia_id", "placa", "horas", "tarifa_base", "desconto", "valor_centavos")
        dados.update(situacao="concluida", horario_saida=saida["horario_saida"],
                     pagamento=saida["pagamento"], cobranca={campo: saida[campo] for campo in campos})
    else:
        pagamento = ctrl.consultar_pagamento(entrada["placa"])
        dados["pagamento"] = "sem_confirmacao" if pagamento is None else "confirmado"
        if pagamento is not None:
            dados["cobranca"] = cobranca(pagamento)
    return dados


def estadias_ativas(ctrl):
    # A vaga informa a ocupação atual. O evento fornece o horário original, inclusive no legado.
    entradas = {e["placa"]: e for e in ctrl.consultar_historico()
                if e["acao"] in ("entrada", "entrada_cliente")}
    return [estadia_do_evento(ctrl, entradas[v.veiculo.placa]) for v in ctrl.listar_vagas() if v.ocupada]


def estadia(ctrl, identificador):
    eventos = ctrl.consultar_historico()
    if type(identificador) is not int or not 1 <= identificador <= len(eventos):
        raise ValueError("Identificador de estadia inexistente.")
    entrada = eventos[identificador - 1]
    if entrada["acao"] != "entrada_cliente":
        raise ValueError("O identificador não corresponde a uma entrada vinculada.")
    saida = next((e for e in reversed(eventos) if e["acao"] == "saida_cliente"
                  and e["estadia_id"] == identificador), None)
    return estadia_do_evento(ctrl, entrada, saida)


def publica(vaga):
    return dict(numero=vaga.numero, setor=1 + (vaga.numero - 1) // VAGAS_POR_SETOR,
                classificacao=vaga.classificacao, estado=vaga.estado, vip=vaga.vip,
                carregador=vaga.carregador.disponivel if vaga.carregador else None)


def indicadores(ctrl):
    grupos = {tipo: dict(total=0, livres=0, reservadas=0, ocupadas=0) for tipo in CLASSIFICACOES}
    eletricas = falhas = vip = 0
    for v in ctrl.listar_vagas():
        grupo = grupos[v.classificacao]
        grupo['total'] += 1
        grupo[{'livre': 'livres', 'reservada': 'reservadas', 'ocupada': 'ocupadas'}[v.estado]] += 1
        if v.carregador:
            falhas += not v.carregador.disponivel
            eletricas += v.livre and v.carregador.disponivel
        vip += v.vip
    return dict(grupos=grupos, eletricas=eletricas, falhas=falhas, vip=vip)


def opcoes(ctrl, titular, placa, vip, entrada):
    """Projeção segura inclusive para o Cliente. Nunca transporta identidades de terceiros."""
    veiculo = next((v for v in ctrl.veiculos_do_cliente(titular) if v.placa == placa), None)
    if veiculo is None:
        raise ValueError('Selecione um veículo do seu cadastro.')
    vagas = ctrl.listar_vagas()
    reservado = next((v for v in vagas if v.reserva and v.reserva.placa == placa), None)
    estacionado = any(v.ocupada and v.veiculo.placa == placa for v in vagas)
    contexto = ctrl.estacionamento.contexto(veiculo, date.today(), reservado.vip if entrada and reservado else vip,
                                          reservado.reserva.autorizacao_id if entrada and reservado else None)
    resultado = []
    for v in vagas:
        motivo = v.restricao(contexto)
        if estacionado:
            motivo = 'Este veículo já está estacionado.'
        elif reservado and (not entrada or reservado is not v):
            motivo = f'Este veículo tem reserva na vaga {reservado.numero:03d}.'
        elif not v.livre and not (entrada and v is reservado):
            motivo = 'Vaga indisponível.'
        autorizacao = contexto.autorizacao(v.grupos) if hasattr(v, 'grupos') else None
        resultado.append(dict(**publica(v), motivo=motivo,
                              reserva_id=v.reserva.identificador if entrada and reservado is v else None,
                              conferencia=autorizacao.identificador if autorizacao else None,
                              beneficiario=autorizacao.beneficiario if autorizacao else None))
    return resultado
