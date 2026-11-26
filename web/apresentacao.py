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
        return self._porcentagem(self.ocupadas)

    @property
    def percentual_indisponivel(self):
        return self._porcentagem(self.total - self.livres)

    def _porcentagem(self, quantidade):
        valor = round(100 * quantidade / self.total, 1) if self.total else 0.0
        return int(valor) if valor.is_integer() else valor

    @property
    def reservadas(self):
        return self.total - self.ocupadas - self.livres


@dataclass(frozen=True)
class PaginaVagas:
    vagas: list
    quantidade: int
    pagina: int
    paginas: int
    setores: tuple

    @classmethod
    def filtrar(cls, vagas, filtros):
        from model.vaga import VAGAS_POR_SETOR
        setores = tuple(sorted({v['setor'] for v in vagas}))
        resultados = []
        for v in vagas:
            if any(filtros.get(k) and str(v[k]) != filtros[k] for k in ('setor', 'classificacao', 'estado')):
                continue
            if filtros.get('numero') and filtros['numero'].lstrip('0') != str(v['numero']):
                continue
            equipamento = filtros.get('equipamento')
            if equipamento and v['carregador'] is not (equipamento == 'disponivel'):
                continue
            if filtros.get('destinacao') == 'vip' and not v['vip']:
                continue
            resultados.append(v)
        try:
            numero = int(filtros.get('pagina', 1))
        except ValueError:
            numero = 1
        paginas = max(1, (len(resultados) + VAGAS_POR_SETOR - 1) // VAGAS_POR_SETOR)
        numero = min(max(1, numero), paginas)
        inicio = (numero - 1) * VAGAS_POR_SETOR
        return cls(resultados[inicio:inicio + VAGAS_POR_SETOR], len(resultados), numero, paginas, setores)
