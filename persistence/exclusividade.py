"""Travas cooperativas sobre arquivos auxiliares estáveis, no sistema de arquivos local."""
import os
from contextlib import contextmanager
from pathlib import Path
from threading import Lock

from persistence.ambiente_termux import caminho_interno


class HistoricoEmUso(OSError):
    pass


if os.name == 'nt':
    import ctypes
    import msvcrt
    from ctypes import wintypes
    from time import sleep

    _kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    for _funcao in (_kernel.LockFile, _kernel.UnlockFile):
        _funcao.argtypes = (wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD,
                            wintypes.DWORD, wintypes.DWORD)
        _funcao.restype = wintypes.BOOL

    def _bloquear(arquivo, esperar):
        handle = msvcrt.get_osfhandle(arquivo.fileno())
        # A faixa [0, 1) pode ultrapassar o EOF, sem precisar modificar o arquivo.
        while not _kernel.LockFile(handle, 0, 0, 1, 0):
            codigo = ctypes.get_last_error()
            if codigo != 33:  # ERROR_LOCK_VIOLATION
                raise ctypes.WinError(codigo)
            if not esperar:
                raise HistoricoEmUso('Histórico em uso por outra execução do MOVE.')
            sleep(0.05)

    def _desbloquear(arquivo):
        if not _kernel.UnlockFile(msvcrt.get_osfhandle(arquivo.fileno()), 0, 0, 1, 0):
            raise ctypes.WinError(ctypes.get_last_error())
else:
    import fcntl

    def _bloquear(arquivo, esperar):
        try:
            fcntl.flock(arquivo, fcntl.LOCK_EX if esperar else fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as erro:
            raise HistoricoEmUso('Histórico em uso por outra execução do MOVE.') from erro

    def _desbloquear(arquivo):
        fcntl.flock(arquivo, fcntl.LOCK_UN)


@contextmanager
def trava_de_arquivo(caminho, *, esperar=False):
    with caminho_interno(Path(caminho)).open('a+b') as arquivo:
        _bloquear(arquivo, esperar)
        try:
            yield
        finally:
            _desbloquear(arquivo)


class EscritorLocal:
    def __init__(self, historico):
        self.caminho = Path(str(Path(historico).resolve()) + '.lock')
        self._reserva = None
        self._guarda = Lock()

    def abrir(self):
        with self._guarda:
            if self._reserva is None:
                reserva = trava_de_arquivo(self.caminho)
                reserva.__enter__()
                self._reserva = reserva

    def fechar(self):
        with self._guarda:
            if self._reserva is not None:
                reserva, self._reserva = self._reserva, None
                reserva.__exit__(None, None, None)
