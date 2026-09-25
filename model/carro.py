from model.veiculo import Veiculo


class Carro(Veiculo):
    def calcular_tarifa(self, horas):
        return 10 * horas

