"""Leitura validada e substituição atômica do histórico de uma única instância."""
import json
import math
import os
import tempfile
from datetime import datetime
from pathlib import Path

from model.carro import Carro
from model.moto import Moto
from model.caminhao import Caminhao


def _rejeitar_constante(valor):
    raise ValueError(f"Número não finito no JSON: {valor}")


def carregar(arquivo):
    from model.estacionamento import Estacionamento

    destino = Path(arquivo)
    est = Estacionamento(arquivo)
    try:
        conteudo = destino.read_bytes()
        dados = json.loads(conteudo.decode("utf-8"), parse_constant=_rejeitar_constante)
    except FileNotFoundError:
        return est
    except (ValueError, UnicodeError) as erro:
        raise ValueError("Histórico JSON inválido; arquivo preservado.") from erro
    try:
        if not isinstance(dados, list):
            raise ValueError("O histórico deve ser uma lista.")
        classes = {"carro": Carro, "moto": Moto, "caminhao": Caminhao}
        for evento in dados:
            if not isinstance(evento, dict):
                raise ValueError("Evento deve ser um objeto.")
            acao = evento["acao"]
            classe = classes[evento["tipo"]]
            # Arquivos da versão anterior não registravam o modelo.
            veiculo = classe(evento["placa"], evento.get("modelo", "Modelo não registrado"))
            if evento['placa'] != veiculo.placa:
                raise ValueError("Placa do histórico não normalizada.")
            if acao == "cadastro":
                est.cadastrar_veiculo(veiculo)
            elif acao == "entrada":
                datetime.fromisoformat(evento["horario_entrada"])
                est.estacionar(veiculo, evento["vaga"])
            elif acao == "saida":
                entrada = next((e for e in reversed(est._historico)
                                if e['acao'] == 'entrada' and e['placa'] == veiculo.placa), None)
                if entrada is None or evento['horario_entrada'] != entrada['horario_entrada']:
                    raise ValueError("Saída sem entrada correspondente.")
                inicio = datetime.fromisoformat(evento['horario_entrada'])
                fim = datetime.fromisoformat(evento['horario_saida'])
                if fim < inicio:
                    raise ValueError("Saída anterior à entrada.")
                vaga = est._buscar_vaga(evento['vaga'])
                if not vaga.ocupada or vaga.veiculo.placa != veiculo.placa:
                    raise ValueError("Saída incompatível com a ocupação.")
                if type(vaga.veiculo) is not classe or vaga.veiculo.modelo != veiculo.modelo:
                    raise ValueError("Tipo ou modelo da saída incompatível.")
                valor = evento['valor']
                if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not math.isfinite(valor):
                    raise ValueError("Valor inválido.")
                tarifa = est.retirar(evento['vaga'], evento['horas'])
                if valor != tarifa:
                    raise ValueError("Valor incompatível com a tarifa.")
            else:
                raise ValueError("Ação desconhecida.")
            # Mantém horários e campos originais, sem substituir pela hora da leitura.
            est._historico[-1] = dict(evento)
    except (KeyError, TypeError, ValueError, OverflowError) as erro:
        raise ValueError(f"Histórico JSON inconsistente; arquivo preservado: {erro}") from erro
    est._conteudo_arquivo = conteudo
    return est


def salvar(arquivo, historico, esperado=None):
    destino = Path(arquivo)
    conteudo = json.dumps(historico, ensure_ascii=False, indent=4, allow_nan=False).encode("utf-8")

    def verificar_destino():
        try:
            atual = destino.read_bytes()
        except FileNotFoundError:
            atual = None
        if atual != esperado:
            raise OSError("Histórico alterado por outra execução; arquivo preservado. Reinicie o programa.")

    verificar_destino()
    temporario = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=destino.parent,
                                         prefix=destino.name + ".", suffix=".tmp", delete=False) as saida:
            temporario = Path(saida.name)
            saida.write(conteudo.decode("utf-8"))
            saida.flush()
            os.fsync(saida.fileno())
        verificar_destino()
        os.replace(temporario, destino)
        return conteudo
    finally:
        if temporario is not None and temporario.exists():
            temporario.unlink()
