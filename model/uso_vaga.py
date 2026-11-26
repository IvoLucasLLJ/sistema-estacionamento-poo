"""Características independentes da tarifa, da categoria comercial e da ocupação."""
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from model.veiculo import Veiculo

MOTORES = {'desconhecida': 'Não informada', 'convencional': 'Não recarregável',
           'eletrica': 'Elétrico recarregável', 'plugin': 'Híbrido plug-in'}
GRUPOS = {'pcd': 'PcD com comprometimento de mobilidade', 'idoso': 'Pessoa idosa',
          'obesa': 'Pessoa obesa', 'gestante': 'Gestante', 'colo': 'Criança de colo até dois anos'}
CLASSIFICACOES = {'comum': 'Comum', 'eletrica': 'Recarga elétrica', 'pcd': 'Exclusiva PcD',
                  'idoso': 'Pessoa idosa', 'adicional': 'Acessibilidade adicional',
                  'familia': 'Gestante ou criança de colo'}


@dataclass(frozen=True)
class BeneficiarioFicticio:
    titular: str
    numero: int

    def __post_init__(self):
        if type(self.numero) is not int or not 1 <= self.numero <= 999:
            raise ValueError('Use um número fictício de beneficiário entre 1 e 999.')


@dataclass(frozen=True)
class AutorizacaoUso:
    """Conferência fictícia da Gestão para o beneficiário transportado neste contexto."""
    identificador: int
    cliente_id: str
    placa: str
    grupo: str
    beneficiario: str
    conferencia: str
    validade: date
    pessoa: BeneficiarioFicticio

    def __post_init__(self):
        if self.grupo not in GRUPOS or self.beneficiario not in ('condutor', 'passageiro'):
            raise ValueError('Informe o grupo e a condição do beneficiário.')
        if self.grupo == 'colo' and self.beneficiario != 'passageiro':
            raise ValueError('A criança precisa estar presente como passageira.')
        meios = ('fisica', 'digital') if self.grupo in ('pcd', 'idoso') else ('administrativa',)
        if self.conferencia not in meios:
            raise ValueError('Confira a credencial física ou digital para PcD/idoso; nos demais grupos use conferência administrativa.')


@dataclass(frozen=True)
class ContextoUso:
    cliente_id: str | None
    categoria: str | None
    veiculo: "Veiculo"
    dia: date
    autorizacoes: tuple = ()
    vip: bool = False

    def autorizacao(self, grupos):
        return next((a for a in self.autorizacoes if a.cliente_id == self.cliente_id
                     and a.placa == self.veiculo.placa and a.grupo in grupos and a.validade >= self.dia), None)


class Carregador:
    def __init__(self):
        self._disponivel = True

    @property
    def disponivel(self):
        return self._disponivel

    def definir_disponibilidade(self, disponivel):
        if type(disponivel) is not bool or disponivel == self.disponivel:
            raise ValueError('Informe uma mudança válida de disponibilidade do carregador.')
        self._disponivel = disponivel
