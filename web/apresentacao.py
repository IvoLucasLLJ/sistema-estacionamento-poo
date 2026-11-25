from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


CATEGORIAS = {'comum': 'Comum', 'vip': 'VIP', 'mensalista': 'Mensalista'}
TIPOS = {'carro': 'Carro', 'moto': 'Moto', 'caminhao': 'Caminhão'}


def horario(iso):
    instante = datetime.fromisoformat(iso)
    texto = instante.strftime('%d/%m/%Y às %H:%M')
    fuso = instante.strftime('%z')
    return f'{texto} ({fuso[:3]}:{fuso[3:]})' if fuso else texto


def dinheiro(reais):
    """Mantém a precisão legada e apresenta pelo menos duas casas decimais."""
    valor = Decimal(reais)
    if not valor.is_finite():
        return 'Valor fora da faixa de representação'
    if valor.is_zero():
        return 'R$ 0,00'
    if valor.adjusted() < -300:
        return 'R$ ' + format(valor, 'E').replace('.', ',')
    inteiro, _, fracao = format(valor, ',f').partition('.')
    return 'R$ ' + inteiro.replace(',', '.') + ',' + fracao.rstrip('0').ljust(2, '0')


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
