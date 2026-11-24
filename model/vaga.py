from model.veiculo import Veiculo


class Vaga:
    def __init__(self, numero):
        if type(numero) is not int or numero < 1:
            raise ValueError("Número da vaga deve ser um inteiro positivo.")
        self._numero = numero
        self._veiculo = None
        self._estadia = None

    @property
    def numero(self):
        return self._numero

    @property
    def ocupada(self):
        return self._veiculo is not None

    @property
    def veiculo(self):
        return self._veiculo

    def ocupar(self, veiculo, *, estadia=None):
        if not isinstance(veiculo, Veiculo):
            raise ValueError("Informe um veículo válido.")
        if self.ocupada:
            raise ValueError(f"A vaga {self.numero} já está ocupada.")
        self._veiculo = veiculo
        self._estadia = estadia

    def liberar(self, *, estadia=None):
        if not self.ocupada:
            raise ValueError(f"A vaga {self.numero} já está livre.")
        if self._estadia is not estadia:
            raise ValueError("A vaga só pode ser liberada pela conclusão da sua estadia.")
        veiculo = self._veiculo
        self._veiculo = None
        self._estadia = None
        return veiculo
