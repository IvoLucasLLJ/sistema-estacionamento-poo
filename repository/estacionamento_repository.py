"""Persistência do agregado Estacionamento no formato JSON do MOVE."""
from pathlib import Path

from model.estacionamento import Estacionamento
from persistence import historico_json


class EstacionamentoRepository:
    def __init__(self, arquivo="historico.json"):
        self.arquivo = Path(arquivo)
        self._conteudo_esperado = None

    def carregar(self):
        """Publica o agregado somente depois de validar todos os eventos."""
        dados, conteudo = historico_json.ler(self.arquivo)
        estacionamento = Estacionamento.reconstruir(dados)
        self._conteudo_esperado = conteudo
        return estacionamento

    def salvar(self, estacionamento):
        """Atualiza a referência de conflito somente após gravação bem-sucedida."""
        if not isinstance(estacionamento, Estacionamento):
            raise ValueError("Informe um estacionamento válido.")
        self._conteudo_esperado = historico_json.salvar(
            self.arquivo, estacionamento.historico, self._conteudo_esperado
        )
