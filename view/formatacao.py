from decimal import Decimal, ROUND_HALF_UP, localcontext


def dinheiro(reais):
    """Formata reais em pt-BR com duas casas, arredondando somente a exibição."""
    valor = Decimal(str(reais))
    if not valor.is_finite():
        return 'Valor fora da faixa de representação'
    with localcontext(rounding=ROUND_HALF_UP):
        inteiro, fracao = format(valor, 'z,.2f').split('.')
    return 'R$ ' + inteiro.replace(',', '.') + ',' + fracao
