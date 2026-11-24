from dataclasses import dataclass, field
from decimal import Context, Decimal, MAX_EMAX, MIN_EMIN, ROUND_HALF_UP, localcontext
from sys import float_info

from model.cliente import Cliente
from model.vaga import Vaga
from model.veiculo import Veiculo


def reais_de_centavos(centavos):
    """Conversão exata, inclusive quando a precisão decimal padrão é pequena."""
    return Decimal(f"{centavos}e-2")


@dataclass(frozen=True)
class Cobranca:
    """Consulta em reais. Apenas valor_centavos representa o montante a receber."""
    estadia_id: int
    placa: str
    horas: Decimal
    tarifa_base: Decimal
    desconto: Decimal
    valor_centavos: int

    @property
    def valor_devido(self):
        return reais_de_centavos(self.valor_centavos)

    def dados_do_pagamento(self):
        return {"estadia_id": self.estadia_id, "placa": self.placa,
                "horas": str(self.horas), "valor_centavos": self.valor_centavos}


@dataclass
class Estadia:
    identificador: int
    veiculo: Veiculo
    cliente: Cliente
    vaga: Vaga
    horario_entrada: str
    categoria: str = field(init=False)
    pagamento: Cobranca | None = field(default=None, init=False)

    def __post_init__(self):
        self.categoria = self.cliente.categoria

    def consultar_cobranca(self, horas):
        if isinstance(horas, bool) or not isinstance(horas, (int, float, Decimal)):
            raise ValueError("Informe horas numéricas.")
        horas = Decimal(str(horas)) if isinstance(horas, float) else Decimal(horas)
        if not horas.is_finite() or not 0 <= horas <= Decimal.from_float(float_info.max):
            raise ValueError("Horas fora do intervalo finito e não negativo.")
        if self.pagamento is not None and horas != self.pagamento.horas:
            raise ValueError("As horas já foram confirmadas no pagamento desta estadia.")
        if horas.is_zero():
            horas = Decimal(0)
        # Reserva dígitos para tarifa, metade, centavos e transporte do arredondamento.
        precisao = max(len(horas.as_tuple().digits), horas.adjusted(), 1) + 8
        with localcontext(Context(prec=precisao, Emin=MIN_EMIN, Emax=MAX_EMAX)):
            base = self.veiculo.calcular_tarifa(horas)
            devido = Decimal(self.cliente.calcular_cobranca(base))
            desconto = base - devido
            arredondado = devido.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            centavos = int(arredondado.scaleb(2))
        return Cobranca(self.identificador, self.veiculo.placa, horas, base, desconto, centavos)

    def confirmar_pagamento(self, cobranca, confirmado):
        if confirmado is not True:
            raise ValueError("Pagamento não confirmado.")
        if cobranca.valor_centavos == 0:
            raise ValueError("Estadia isenta de pagamento.")
        if self.pagamento is not None:
            raise ValueError("Pagamento já confirmado.")
        self.pagamento = cobranca

    def situacao_para_saida(self, cobranca):
        if self.pagamento is None and cobranca.valor_centavos == 0:
            return "isento"
        if self.pagamento != cobranca:
            raise ValueError("A cobrança desta estadia exige pagamento confirmado.")
        return "confirmado"
