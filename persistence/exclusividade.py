"""Reserva cooperativa do histórico entre os executáveis locais do MOVE (Linux)."""
import fcntl
from pathlib import Path
from threading import Lock


class HistoricoEmUso(OSError):
    pass


class EscritorLocal:
    def __init__(self, historico):
        self.caminho = Path(str(Path(historico).resolve()) + '.lock')
        self._arquivo = None
        self._guarda = Lock()

    def abrir(self):
        with self._guarda:
            if self._arquivo is None:
                arquivo = self.caminho.open('a')
                try:
                    fcntl.flock(arquivo, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError as erro:
                    arquivo.close()
                    raise HistoricoEmUso('Histórico em uso por outra execução do MOVE.') from erro
                except OSError:
                    arquivo.close()
                    raise
                self._arquivo = arquivo

    def fechar(self):
        with self._guarda:
            if self._arquivo is not None:
                self._arquivo.close()
                self._arquivo = None
