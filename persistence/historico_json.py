"""Leitura validada e substituição atômica do histórico de uma única instância."""
import json
import os
import tempfile
from pathlib import Path

def _rejeitar_constante(valor):
    raise ValueError(f"Número não finito no JSON: {valor}")


def ler(arquivo):
    """Retorna eventos e bytes originais; ausência é distinta de arquivo vazio."""
    try:
        conteudo = Path(arquivo).read_bytes()
        dados = json.loads(conteudo.decode("utf-8"), parse_constant=_rejeitar_constante)
    except FileNotFoundError:
        return [], None
    except (ValueError, UnicodeError) as erro:
        raise ValueError("Histórico JSON inválido; arquivo preservado.") from erro
    return dados, conteudo


def carregar(arquivo):
    """Compatibilidade com a API antiga; reconstrução pertence ao Model."""
    from model.estacionamento import Estacionamento
    return Estacionamento.carregar_historico(arquivo)


def salvar(arquivo, historico, esperado=None):
    destino = Path(arquivo)
    conteudo = json.dumps(historico, ensure_ascii=False, indent=4, allow_nan=False).encode("utf-8")

    def verificar_destino():
        try:
            atual = destino.read_bytes()
        except FileNotFoundError:
            atual = None
        if atual != esperado:
            raise OSError("Histórico alterado por outra execução; arquivo preservado. Reinicie o programa.")

    verificar_destino()
    temporario = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=destino.parent,
                                         prefix=destino.name + ".", suffix=".tmp", delete=False) as saida:
            temporario = Path(saida.name)
            saida.write(conteudo.decode("utf-8"))
            saida.flush()
            os.fsync(saida.fileno())
        verificar_destino()
        os.replace(temporario, destino)
        return conteudo
    finally:
        if temporario is not None and temporario.exists():
            temporario.unlink()
