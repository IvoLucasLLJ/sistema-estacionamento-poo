from model.vaga import DISTRIBUICAO
from model.caminhao import Caminhao
from model.carro import Carro
from model.categorias_cliente import classe_da_categoria
from repository.estacionamento_repository import EstacionamentoRepository
from model.moto import Moto


class Controller:
    def __init__(self, arquivo="historico.json", repository=None, *, distribuicao=DISTRIBUICAO):
        self.repository = repository if repository is not None else EstacionamentoRepository(arquivo, distribuicao=distribuicao)
        self._estacionamento = self.repository.carregar()

    @property
    def estacionamento(self):
        return self._estacionamento

    def cadastrar_cliente(self, categoria, nome):
        classe = classe_da_categoria(categoria)
        return self.estacionamento.cadastrar_cliente(classe(nome))

    def buscar_cliente(self, identificador):
        return self.estacionamento.buscar_cliente(identificador)

    def listar_clientes(self):
        return self.estacionamento.listar_clientes()

    def vincular_veiculo(self, placa, cliente_id):
        self.estacionamento.vincular_veiculo(placa, cliente_id)

    def cliente_do_veiculo(self, placa):
        return self.estacionamento.cliente_do_veiculo(placa)

    def veiculos_do_cliente(self, cliente_id):
        return self.estacionamento.veiculos_do_cliente(cliente_id)

    def iniciar_estadia(self, placa, vaga, cliente_id, *, beneficiario_presente=False):
        self.estacionamento.iniciar_estadia(placa, vaga, cliente_id, beneficiario_presente=beneficiario_presente)

    def consultar_cobranca(self, placa, horas):
        return self.estacionamento.consultar_cobranca(placa, horas)

    def confirmar_pagamento(self, cobranca, *, confirmado):
        self.estacionamento.confirmar_pagamento(cobranca, confirmado=confirmado)

    def consultar_pagamento(self, placa):
        return self.estacionamento.consultar_pagamento(placa)

    def concluir_saida(self, cobranca):
        return self.estacionamento.concluir_saida(cobranca)

    @staticmethod
    def _criar_veiculo(tipo, placa, modelo, motorizacao="desconhecida"):
        if not isinstance(tipo, str):
            raise ValueError("Tipo inválido")
        tipo = tipo.strip().lower()
        if tipo == "carro":
            veiculo = Carro(placa, modelo, motorizacao)
        elif tipo == "moto":
            veiculo = Moto(placa, modelo, motorizacao)
        elif tipo == "caminhao":
            veiculo = Caminhao(placa, modelo, motorizacao)
        else:
            raise ValueError("Tipo inválido")
        return veiculo

    def cadastrar_veiculo(self, tipo, placa, modelo, motorizacao="desconhecida"):
        return self.estacionamento.cadastrar_veiculo(self._criar_veiculo(tipo, placa, modelo, motorizacao))

    def buscar_veiculo(self, placa):
        return self.estacionamento.buscar_veiculo(placa)

    def listar_veiculos(self):
        return self.estacionamento.veiculos

    def listar_vagas(self):
        return self.estacionamento.vagas

    def consultar_historico(self):
        return self.estacionamento.historico

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
