from model.caminhao import Caminhao
from model.carro import Carro
from model.estacionamento import Estacionamento
from model.moto import Moto


class Controller:
    def __init__(self):
        self.estacionamento = Estacionamento()

    def estacionar_veiculo(self, tipo, placa, modelo, vaga):
        if not isinstance(tipo, str):
            raise ValueError("Tipo inválido")
        tipo = tipo.strip().lower()
        if tipo == "carro":
            veiculo = Carro(placa, modelo)
        elif tipo == "moto":
            veiculo = Moto(placa, modelo)
        elif tipo == "caminhao":
            veiculo = Caminhao(placa, modelo)
        else:
            raise ValueError("Tipo inválido")
        self.estacionamento.estacionar(veiculo, vaga)

    def retirar_veiculo(self, vaga, horas):
        return self.estacionamento.retirar(vaga, horas)

    def relatorio(self):
        return self.estacionamento.relatorio()

    def salvar(self):
        self.estacionamento.salvar_historico()
