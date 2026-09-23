class Carro:
    def __init__(self, placa: str, modelo: str):
        self.placa = placa
        self.modelo = modelo

    def calcular_tarifa(self, horas: float) -> float:
        valor_hora = 5.00
        return horas * valor_hora


class Moto:
    def __init__(self, placa: str, modelo: str):
        self.placa = placa
        self.modelo = modelo

    def calcular_tarifa(self, horas: float) -> float:
        valor_hora = 3.00
        return horas * valor_hora


class Caminhao:
    def __init__(self, placa: str, modelo: str):
        self.placa = placa
        self.modelo = modelo

    def calcular_tarifa(self, horas: float) -> float:
        valor_hora = 10.00
        return horas * valor_hora
