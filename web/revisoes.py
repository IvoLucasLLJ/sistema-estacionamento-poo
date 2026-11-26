"""Formulários de uso único no processo que atende o MOVE."""
from dataclasses import dataclass
from secrets import token_urlsafe
from threading import Lock
from time import monotonic

from flask import abort, current_app, request

from web.seguranca import csrf_token


@dataclass(frozen=True)
class Revisao:
    sessao: str
    operacao: str
    dados: dict
    expira: float


class Revisoes:
    def __init__(self, validade=900, capacidade=4096):
        self._validade = validade
        self._capacidade = capacidade
        self._pendentes = {}
        self._trava = Lock()

    def emitir(self, sessao, operacao, dados=None):
        with self._trava:
            agora = monotonic()
            while self._pendentes:
                primeiro = next(iter(self._pendentes))
                if (len(self._pendentes) < self._capacidade
                        and self._pendentes[primeiro].expira > agora):
                    break
                del self._pendentes[primeiro]
            chave = token_urlsafe(32)
            self._pendentes[chave] = Revisao(sessao, operacao, dict(dados or {}), agora + self._validade)
            return chave

    def obter(self, chave, sessao, operacao, *, consumir=False):
        with self._trava:
            revisao = self._pendentes.get(chave)
            if (revisao is None or revisao.expira <= monotonic()
                    or revisao.sessao != sessao or revisao.operacao != operacao):
                return None
            if consumir:
                del self._pendentes[chave]
            return dict(revisao.dados)

    def invalidar_sessao(self, sessao):
        with self._trava:
            chaves = [chave for chave, revisao in self._pendentes.items() if revisao.sessao == sessao]
            for chave in chaves:
                del self._pendentes[chave]


def emitir(acao, dados=None):
    return current_app.extensions['revisoes'].emitir(csrf_token(), acao, dados)


def consumir(acao):
    dados = current_app.extensions['revisoes'].obter(
        request.form.get('revisao'), csrf_token(), acao, consumir=True)
    if dados is None:
        abort(409)
    return dados
