"""Projeções de leitura do MOVE. Os objetos do domínio ficam dentro da operação."""
from decimal import Decimal, InvalidOperation


def cliente(objeto):
    return {"identificador": objeto.identificador, "categoria": objeto.categoria, "nome": objeto.nome}


def veiculo(objeto):
    return {"placa": objeto.placa, "tipo": type(objeto).__name__.lower(), "modelo": objeto.modelo}


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
    return [{"numero": vaga.numero, "ocupada": vaga.ocupada,
             "placa": vaga.veiculo.placa if vaga.ocupada else None} for vaga in ctrl.listar_vagas()]


def ocupacao(ctrl):
    rel = ctrl.relatorio()
    return {"ocupadas": rel["ocupadas"], "livres": rel["livres"], "total": len(ctrl.listar_vagas())}


def faturamento(ctrl):
    reais = Decimal(str(ctrl.relatorio()["faturamento"]))
    # O relatório legado usa float e pode exceder seu intervalo ao somar saídas finitas.
    if not reais.is_finite():
        return {"reais": str(reais), "centavos": None}
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
