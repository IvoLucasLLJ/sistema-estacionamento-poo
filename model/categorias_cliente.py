from model.cliente_comum import ClienteComum
from model.cliente_mensalista import ClienteMensalista
from model.cliente_vip import ClienteVIP


_CLASSES_POR_CATEGORIA = {
    classe.CATEGORIA: classe for classe in (ClienteComum, ClienteVIP, ClienteMensalista)
}


def classe_da_categoria(categoria):
    if not isinstance(categoria, str) or categoria not in _CLASSES_POR_CATEGORIA:
        raise ValueError("Categoria de cliente desconhecida.")
    return _CLASSES_POR_CATEGORIA[categoria]
