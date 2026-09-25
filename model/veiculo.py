class Veiculo:
    def __init__(self, placa, modelo):
        if not isinstance(placa, str) or not placa.strip():
            raise ValueError("Informe uma placa válida.")
        if not isinstance(modelo, str) or not modelo.strip():
            raise ValueError("Informe um modelo válido.")
        self.placa = placa.strip().upper().replace("-", "").replace(" ", "")
        if not self.placa or not self.placa.isalnum():
            raise ValueError("A placa deve conter letras ou números.")
        self.modelo = modelo.strip()
        















# from abc import ABC, abstractmethod


# class Veiculo(ABC):
#     def __init__(self, placa, modelo):
#         self.placa = placa
#         self.modelo = modelo

#     @abstractmethod
#     def calcular_tarifa(self, horas):
#         pass
