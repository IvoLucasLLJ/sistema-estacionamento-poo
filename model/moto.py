
from model.veiculo import Veiculo


class Moto(Veiculo):
    TARIFA_POR_HORA = 5

    def calcular_tarifa(self, horas):
        return self.TARIFA_POR_HORA * horas
