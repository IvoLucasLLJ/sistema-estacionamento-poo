from model.cliente_comum import ClienteComum
from model.cliente_mensalista import ClienteMensalista
from model.cliente_vip import ClienteVIP


_CLASSES_POR_CATEGORIA = {
    classe.CATEGORIA: classe for classe in (ClienteComum, ClienteVIP, ClienteMensalista)
}

PRECOS_CATEGORIA_CENTAVOS = {"comum": 0, "vip": 25000, "mensalista": 50000}


def preco_da_mudanca(origem, destino):
    classe_da_categoria(origem)
    classe_da_categoria(destino)
    if origem == destino:
        raise ValueError("Esta já é a sua categoria.")
    return max(0, PRECOS_CATEGORIA_CENTAVOS[destino] - PRECOS_CATEGORIA_CENTAVOS[origem])


def classe_da_categoria(categoria):
    if not isinstance(categoria, str) or categoria not in _CLASSES_POR_CATEGORIA:
        raise ValueError("Categoria de cliente desconhecida.")
    return _CLASSES_POR_CATEGORIA[categoria]
