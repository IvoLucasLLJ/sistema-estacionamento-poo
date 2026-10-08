from abc import ABC, abstractmethod


class Veiculo(ABC):
    def __init__(self, placa, modelo):
        self._placa = self.normalizar_placa(placa)
        if not isinstance(modelo, str) or not modelo.strip():
            raise ValueError("Informe um modelo válido.")
        self._modelo = modelo.strip()

    @staticmethod
    def normalizar_placa(placa):
        if not isinstance(placa, str) or not placa.strip():
            raise ValueError("Informe uma placa válida.")
        placa = placa.strip().upper().replace("-", "").replace(" ", "")
        if not placa or not placa.isalnum():
            raise ValueError("A placa deve conter letras ou números.")
        return placa

    @property
    def placa(self):
        return self._placa

    @property
    def modelo(self):
        return self._modelo

    @abstractmethod
    def calcular_tarifa(self, horas):
        """Cada tipo de veículo define sua tarifa por hora."""
