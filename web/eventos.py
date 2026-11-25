"""Projeção do histórico usando somente campos com significado no tipo de evento."""
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, localcontext


ROTULOS = {'cadastro_cliente': 'Cadastro de cliente', 'cadastro': 'Cadastro de veículo',
           'vinculo': 'Vínculo', 'entrada': 'Entrada legada', 'saida': 'Saída legada',
           'entrada_cliente': 'Entrada identificada', 'pagamento_confirmado': 'Pagamento confirmado',
           'saida_cliente': 'Saída concluída'}


def eventos_identificados(historico):
    entradas = {}
    eventos = []
    for numero, origem in enumerate(historico, 1):
        acao = origem['acao']
        e = {'numero': numero, 'acao': acao, 'rotulo': ROTULOS[acao]}
        if acao == 'cadastro_cliente':
            e.update(cliente_id=origem['identificador'], nome=origem['nome'], categoria=origem['categoria'])
        else:
            e['placa'] = origem['placa']
        if acao in ('cadastro', 'entrada', 'saida', 'entrada_cliente'):
            e.update(tipo=origem['tipo'], modelo=origem.get('modelo'))
        if acao in ('entrada', 'saida', 'entrada_cliente', 'saida_cliente'):
            e.update(vaga=origem['vaga'], horario_entrada=origem['horario_entrada'])
        if acao in ('vinculo', 'entrada_cliente'):
            e['cliente_id'] = origem['cliente_id']
        if acao == 'entrada_cliente':
            e.update(categoria=origem['categoria'], estadia_id=origem['estadia_id'])
            entradas[e['estadia_id']] = e
        if acao in ('pagamento_confirmado', 'saida_cliente'):
            entrada = entradas[origem['estadia_id']]
            for campo in ('cliente_id', 'categoria', 'estadia_id', 'tipo'):
                e[campo] = entrada[campo]
            e.update(horas=origem['horas'], valor_centavos=origem['valor_centavos'])
        if acao in ('saida', 'saida_cliente'):
            e['horario_saida'] = origem['horario_saida']
        if acao == 'saida':
            e.update(valor=origem['valor'], horas=origem['horas'])
        if acao == 'saida_cliente':
            e.update(pagamento=origem['pagamento'], desconto=origem['desconto'], tarifa_base=origem['tarifa_base'])
        eventos.append(e)
    return eventos


@dataclass(frozen=True)
class RelatorioSaidas:
    receita: Decimal
    pagas: int
    isentas: int
    legadas: int
    por_tipo: tuple
    por_categoria: tuple

    @classmethod
    def do_periodo(cls, eventos, inicio=None, fim=None):
        tipos, categorias, situacoes = Counter(), Counter(), Counter()
        valores = []
        for e in eventos:
            if e['acao'] not in ('saida', 'saida_cliente'):
                continue
            dia = datetime.fromisoformat(e['horario_saida']).date()
            if (inicio and dia < inicio) or (fim and dia > fim):
                continue
            tipos[e['tipo']] += 1
            categorias[e.get('categoria', 'legado')] += 1
            situacoes[e.get('pagamento', 'legado')] += 1
            valor = Decimal(e['valor']) if e['acao'] == 'saida' else Decimal(f"{e['valor_centavos']}e-2")
            valores.append(valor)
        # Mantém tanto as unidades do maior valor quanto a fração legada mais fina.
        with localcontext() as ctx:
            if valores:
                ctx.prec = max(1, max(v.adjusted() for v in valores) - min(v.as_tuple().exponent for v in valores)
                               + len(str(len(valores))) + 1)
            receita = sum(valores, Decimal(0))
        return cls(receita, situacoes['confirmado'], situacoes['isento'], situacoes['legado'],
                   tuple(sorted(tipos.items())), tuple(sorted(categorias.items())))
