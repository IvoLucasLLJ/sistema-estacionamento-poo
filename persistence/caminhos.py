"""Localização do histórico compartilhado pelos executáveis do MOVE."""
import os
from pathlib import Path

from persistence.ambiente_termux import caminho_interno


RAIZ_MOVE = Path(__file__).resolve().parents[1]


def caminho_local(caminho):
    """Resolve a configuração relativa a esta instalação, inclusive após um chdir."""
    caminho_interno(RAIZ_MOVE)
    return caminho_interno((RAIZ_MOVE / Path(caminho).expanduser()).resolve())


def historico_local():
    return caminho_local(os.environ.get('MOVE_HISTORICO', 'historico.json'))
