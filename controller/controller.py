from model.caminhao import Caminhao
from model.carro import Carro
from repository.estacionamento_repository import EstacionamentoRepository
from model.moto import Moto


class Controller:
    def __init__(self, arquivo="historico.json", repository=None):
        self.repository = repository if repository is not None else EstacionamentoRepository(arquivo)
        self._estacionamento = self.repository.carregar()

    @property
    def estacionamento(self):
        return self._estacionamento

    @staticmethod
    def _criar_veiculo(tipo, placa, modelo):
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
        return veiculo

    def cadastrar_veiculo(self, tipo, placa, modelo):
        return self.estacionamento.cadastrar_veiculo(self._criar_veiculo(tipo, placa, modelo))

    def buscar_veiculo(self, placa):
        return self.estacionamento.buscar_veiculo(placa)

    def estacionar_cadastrado(self, placa, vaga):
        self.estacionamento.estacionar_cadastrado(placa, vaga)

    def retirar_por_placa(self, placa, horas):
        return self.estacionamento.retirar_por_placa(placa, horas)

    def estacionar_veiculo(self, tipo, placa, modelo, vaga):
        self.estacionamento.estacionar(self._criar_veiculo(tipo, placa, modelo), vaga)

    def retirar_veiculo(self, vaga, horas):
        return self.estacionamento.retirar(vaga, horas)

    def relatorio(self):
        return self.estacionamento.relatorio()

    def salvar(self):
        self.repository.salvar(self.estacionamento)
