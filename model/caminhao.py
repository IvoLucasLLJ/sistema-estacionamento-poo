from model.veiculo import Veiculo


class Caminhao(Veiculo):
    def calcular_tarifa(self, horas):
        return 20 * horas
