
from model.veiculo import Veiculo


class Moto(Veiculo):
    def calcular_tarifa(self, horas):
        return 5 * horas
