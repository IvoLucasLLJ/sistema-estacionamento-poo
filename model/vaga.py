from dataclasses import dataclass

from model.uso_vaga import Carregador
from model.veiculo import Veiculo


@dataclass(frozen=True)
class ReservaVaga:
    identificador: int
    cliente_id: str
    placa: str
    vip: bool = False
    autorizacao_id: int | None = None


class Vaga:
    classificacao = "comum"
    carregador = None

    def __init__(self, numero):
        if type(numero) is not int or numero < 1:
            raise ValueError("Número da vaga deve ser um inteiro positivo.")
        self._vip_em_uso = False
        self._numero = numero
        self._veiculo = None
        self._estadia = None
        self._reserva = None

    @property
    def numero(self):
        return self._numero

    @property
    def ocupada(self):
        return self._veiculo is not None

    @property
    def veiculo(self):
        return self._veiculo

    @property
    def reserva(self):
        return self._reserva

    @property
    def livre(self):
        return not self.ocupada and self.reserva is None

    @property
    def vip(self):
        return self._vip_em_uso or bool(self.reserva and self.reserva.vip)

    @property
    def estado(self):
        return "ocupada" if self.ocupada else "reservada" if self.reserva else "livre"

    def restricao(self, contexto):
        if contexto and contexto.vip:
            if self.classificacao != "comum":
                return "A destinação VIP exige uma vaga comum."
            if contexto.categoria not in ("vip", "mensalista"):
                return "O benefício exige categoria VIP ou Mensalista."
        return None

    def validar_uso(self, contexto):
        motivo = self.restricao(contexto)
        if motivo:
            raise ValueError(motivo)

    def reservar(self, reserva, *, contexto=None):
        if not isinstance(reserva, ReservaVaga):
            raise ValueError("Informe uma reserva válida.")
        if not self.livre:
            raise ValueError("Esta vaga não está disponível para reserva.")
        self.validar_uso(contexto)
        if contexto and (reserva.placa != contexto.veiculo.placa or reserva.cliente_id != contexto.cliente_id):
            raise ValueError("Reserva incompatível com o titular e o veículo.")
        if reserva.vip != bool(contexto and contexto.vip):
            raise ValueError("Destinação incompatível com a reserva.")
        self._reserva = reserva

    def cancelar_reserva(self, cliente_id, identificador):
        if (type(identificador) is not int or self.reserva is None or self.reserva.cliente_id != cliente_id
                or self.reserva.identificador != identificador):
            raise ValueError("Reserva indisponível para cancelamento.")
        self._reserva = None

    def ocupar(self, veiculo, *, estadia=None, contexto=None):
        if not isinstance(veiculo, Veiculo):
            raise ValueError("Informe um veículo válido.")
        if self.ocupada:
            raise ValueError(f"A vaga {self.numero} já está ocupada.")
        if self.reserva and (veiculo.placa != self.reserva.placa or estadia is None
                             or estadia.cliente.identificador != self.reserva.cliente_id):
            raise ValueError("Esta vaga está reservada para outro veículo.")
        if contexto and contexto.veiculo is not veiculo:
            raise ValueError("Contexto incompatível com o veículo.")
        if self.reserva and self.reserva.vip and not (contexto and contexto.vip):
            raise ValueError("Revalide o benefício desta reserva.")
        self.validar_uso(contexto)
        self._vip_em_uso = bool(self.reserva and self.reserva.vip)
        self._reserva = None
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
        self._vip_em_uso = False
        return veiculo


class VagaEletrica(Vaga):
    classificacao = 'eletrica'

    def __init__(self, numero):
        super().__init__(numero)
        self._carregador = Carregador()

    @property
    def carregador(self):
        return self._carregador

    def restricao(self, contexto):
        motivo = super().restricao(contexto)
        if motivo:
            return motivo
        if not self.carregador.disponivel:
            return 'Carregador indisponível.'
        if not contexto or contexto.veiculo.motorizacao not in ('eletrica', 'plugin'):
            return 'A recarga exige motorização elétrica ou híbrida plug-in cadastrada.'
        return None


class VagaProtegida(Vaga):
    def restricao(self, contexto):
        motivo = super().restricao(contexto)
        if motivo:
            return motivo
        if not contexto or not contexto.autorizacao(self.grupos):
            return 'É necessária conferência administrativa válida para este beneficiário e veículo.'
        return None


class VagaPCD(VagaProtegida):
    classificacao = 'pcd'
    grupos = ('pcd',)


class VagaIdoso(VagaProtegida):
    classificacao = 'idoso'
    grupos = ('idoso',)


class VagaAdicional(VagaProtegida):
    classificacao = 'adicional'
    grupos = ('pcd', 'obesa')


class VagaFamilia(VagaProtegida):
    classificacao = 'familia'
    grupos = ('gestante', 'colo')


DISTRIBUICAO = ((116, Vaga), (60, VagaEletrica), (4, VagaPCD), (10, VagaIdoso),
                (4, VagaAdicional), (6, VagaFamilia))
DISTRIBUICAO_HISTORICA = ((10, Vaga),)
VAGAS_POR_SETOR = 20


def construir_vagas(distribuicao):
    vagas = []
    for quantidade, classe in distribuicao:
        for _ in range(quantidade):
            vagas.append(classe(len(vagas) + 1))
    return vagas
