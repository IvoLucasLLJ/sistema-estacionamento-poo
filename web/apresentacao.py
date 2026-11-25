from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext


CATEGORIAS = {'comum': 'Comum', 'vip': 'VIP', 'mensalista': 'Mensalista'}
TIPOS = {'carro': 'Carro', 'moto': 'Moto', 'caminhao': 'Caminhão'}


def horario(iso):
    instante = datetime.fromisoformat(iso)
    texto = instante.strftime('%d/%m/%Y às %H:%M')
    fuso = instante.strftime('%z')
    return f'{texto} ({fuso[:3]}:{fuso[3:]})' if fuso else texto


def dinheiro(reais):
    """Formata reais em pt-BR com duas casas, arredondando somente a exibição."""
    valor = Decimal(str(reais))
    if not valor.is_finite():
        return 'Valor fora da faixa de representação'
    with localcontext(rounding=ROUND_HALF_UP):
        inteiro, fracao = format(valor, 'z,.2f').split('.')
    return 'R$ ' + inteiro.replace(',', '.') + ',' + fracao


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
