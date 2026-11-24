from abc import ABC, abstractmethod
from sys import float_info


class Cliente(ABC):
    @abstractmethod
    def calcular_cobranca(self, tarifa_base):
        """Retorna o valor por utilização ou lança ValueError se a tarifa-base for inválida."""

    @staticmethod
    def _validar_tarifa_base(tarifa_base):
        """Aceita int ou float não negativo dentro do intervalo finito de float."""
        if (isinstance(tarifa_base, bool) or not isinstance(tarifa_base, (int, float))
                or not 0 <= tarifa_base <= float_info.max):
            raise ValueError("Informe uma tarifa-base numérica, finita e maior ou igual a zero.")
