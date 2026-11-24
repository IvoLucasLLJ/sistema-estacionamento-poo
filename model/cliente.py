from abc import ABC, abstractmethod
from decimal import Decimal
from sys import float_info
from uuid import UUID, uuid4


_GERAR_IDENTIFICADOR = object()


class Cliente(ABC):
    CATEGORIA = None

    def __init__(self, nome, *, identificador=_GERAR_IDENTIFICADOR):
        if not isinstance(nome, str) or not nome.strip():
            raise ValueError("Informe um nome de cliente válido.")
        self._nome = nome.strip()
        if identificador is _GERAR_IDENTIFICADOR:
            self._identificador = str(uuid4())
        else:
            self._identificador = self.normalizar_identificador(identificador)

    @staticmethod
    def normalizar_identificador(identificador):
        if not isinstance(identificador, str):
            raise ValueError("Identificador de cliente deve ser um UUID em texto.")
        try:
            return str(UUID(identificador))
        except ValueError as erro:
            raise ValueError("Identificador de cliente deve ser um UUID válido.") from erro

    @property
    def identificador(self):
        return self._identificador

    @property
    def nome(self):
        return self._nome

    @property
    def categoria(self):
        return type(self).CATEGORIA

    @abstractmethod
    def calcular_cobranca(self, tarifa_base):
        """Retorna o valor por utilização ou lança ValueError se a tarifa-base for inválida."""

    @staticmethod
    def _validar_tarifa_base(tarifa_base):
        """Preserva o limite anterior também para a cobrança decimal."""
        if isinstance(tarifa_base, Decimal):
            if not tarifa_base.is_finite() or not 0 <= tarifa_base <= Decimal.from_float(float_info.max):
                raise ValueError("Informe uma tarifa-base decimal finita e não negativa no intervalo válido.")
            return
        if (isinstance(tarifa_base, bool) or not isinstance(tarifa_base, (int, float))
                or not 0 <= tarifa_base <= float_info.max):
            raise ValueError("Informe uma tarifa-base numérica, finita e maior ou igual a zero.")
