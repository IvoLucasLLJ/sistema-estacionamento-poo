"""Gerações ativas das sessões assinadas do Flask, inclusive após reinício."""
from hashlib import sha256
from time import time

from persistence import historico_json
from persistence.exclusividade import trava_de_arquivo
from service.estacionamento_service import ErroDeInfraestrutura


class SessoesAtivas:
    def __init__(self, arquivo):
        self._arquivo = arquivo

    def _ler(self):
        registros, versao = historico_json.ler(self._arquivo)
        if versao is None:
            return {}, None
        if not isinstance(registros, dict) or any(type(v) is not int for v in registros.values()):
            raise ValueError('Formato de sessões inválido.')
        return registros, versao

    @staticmethod
    def _chave(token):
        return sha256(token.encode()).hexdigest()

    def ativa(self, token):
        if not token:
            return False
        try:
            registros, _ = self._ler()
            return registros.get(self._chave(token), 0) > time()
        except (OSError, ValueError, RecursionError) as erro:
            raise ErroDeInfraestrutura('Registro de sessões indisponível.') from erro

    def substituir(self, anterior=None, nova=None, expira=None):
        """Registra login, troca ou logout. Uma geração só pode ser trocada uma vez."""
        try:
            with trava_de_arquivo(str(self._arquivo) + '.lock', esperar=True):
                registros, versao = self._ler()
                agora = time()
                registros = {k: v for k, v in registros.items() if v > agora}
                if anterior and registros.pop(self._chave(anterior), None) is None:
                    return False
                if nova:
                    registros[self._chave(nova)] = expira
                historico_json.salvar(self._arquivo, registros, versao)
                return True
        except (OSError, ValueError, RecursionError) as erro:
            raise ErroDeInfraestrutura('Falha ao atualizar o registro de sessões.') from erro
