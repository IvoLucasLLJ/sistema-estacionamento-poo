from model.veiculo import Veiculo


class Carro(Veiculo):
    TARIFA_POR_HORA = 10

    def calcular_tarifa(self, horas):
        return self.TARIFA_POR_HORA * horas

