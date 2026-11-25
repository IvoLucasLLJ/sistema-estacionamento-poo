from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from view.formatacao import dinheiro


CATEGORIAS = {'comum': 'Comum', 'vip': 'VIP', 'mensalista': 'Mensalista'}
TIPOS = {'carro': 'Carro', 'moto': 'Moto', 'caminhao': 'Caminhão'}


def horario(iso):
    instante = datetime.fromisoformat(iso)
    texto = instante.strftime('%d/%m/%Y às %H:%M')
    fuso = instante.strftime('%z')
    return f'{texto} ({fuso[:3]}:{fuso[3:]})' if fuso else texto


def centavos(valor):
    return dinheiro(Decimal(f'{valor}e-2'))


@dataclass(frozen=True)
class OcupacaoViewModel:
    livres: int
    ocupadas: int
    total: int

    @classmethod
    def da_consulta(cls, dados):
        return cls(dados['livres'], dados['ocupadas'], dados['total'])

    @property
    def percentual(self):
        return round(100 * self.ocupadas / self.total) if self.total else 0
