from model.veiculo import Veiculo


class Caminhao(Veiculo):
    TARIFA_POR_HORA = 20

    def calcular_tarifa(self, horas):
        return self.TARIFA_POR_HORA * horas
