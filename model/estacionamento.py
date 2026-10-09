from copy import deepcopy
import math
from datetime import datetime

from model.vaga import Vaga
from model.veiculo import Veiculo


class Estacionamento:
    def __init__(self, arquivo="historico.json"):
        self._vagas = [Vaga(num+1) for num in range(10)]
        self._historico = []
        self._veiculos = {}
        # Somente os adaptadores antigos usam este destino.
        self._arquivo_legado = arquivo
        self._repository_legado = None

    @property
    def vagas(self):
        return tuple(self._vagas)

    @property
    def historico(self):
        return deepcopy(self._historico)

    @property
    def veiculos(self):
        return tuple(self._veiculos.values())

    def cadastrar_veiculo(self, veiculo):
        if not isinstance(veiculo, Veiculo):
            raise ValueError("Informe um veículo válido.")
        if veiculo.placa in self._veiculos:
            raise ValueError(f"A placa {veiculo.placa} já está cadastrada.")
        self._veiculos[veiculo.placa] = veiculo
        self._historico.append({
            "acao": "cadastro", "placa": veiculo.placa,
            "tipo": type(veiculo).__name__.lower(), "modelo": veiculo.modelo,
        })
        return veiculo

    def buscar_veiculo(self, placa):
        placa = Veiculo.normalizar_placa(placa)
        if placa not in self._veiculos:
            raise ValueError(f"Veículo {placa} não cadastrado.")
        return self._veiculos[placa]

    def estacionar_cadastrado(self, placa, num_vaga):
        self.estacionar(self.buscar_veiculo(placa), num_vaga)

    def retirar_por_placa(self, placa, horas):
        veiculo = self.buscar_veiculo(placa)
        for vaga in self._vagas:
            if vaga.ocupada and vaga.veiculo.placa == veiculo.placa:
                return self.retirar(vaga.numero, horas)
        raise ValueError(f"Veículo {veiculo.placa} não está estacionado.")

    def _buscar_vaga(self, numero):
        if type(numero) is not int or not 1 <= numero <= len(self.vagas):
            raise ValueError(f"Número da vaga deve ser inteiro entre 1 e {len(self.vagas)}.")
        return self.vagas[numero - 1]

    def estacionar(self, veiculo, num_vaga):
        if not isinstance(veiculo, Veiculo):
            raise ValueError("Informe um veículo válido.")
        existente = self._veiculos.get(veiculo.placa)
        if existente is not None:
            if type(existente) is not type(veiculo) or existente.modelo != veiculo.modelo:
                raise ValueError("Placa cadastrada com outro tipo ou modelo.")
            veiculo = existente
        vaga = self._buscar_vaga(num_vaga)
        if any(v.ocupada and v.veiculo.placa == veiculo.placa for v in self.vagas):
            raise ValueError(f"O veículo {veiculo.placa} já está estacionado.")
        vaga.ocupar(veiculo)
        self._veiculos[veiculo.placa] = veiculo
        self._historico.append({
            "acao": "entrada", "placa": veiculo.placa,
            "tipo": type(veiculo).__name__.lower(), "modelo": veiculo.modelo,
            "vaga": vaga.numero,
            "horario_entrada": datetime.now().astimezone().isoformat(),
        })

    def retirar(self, num_vaga, num_horas):
        vaga = self._buscar_vaga(num_vaga)
        if (isinstance(num_horas, bool) or not isinstance(num_horas, (int, float))
                or not math.isfinite(num_horas) or num_horas < 0):
            raise ValueError("Horas devem ser um número finito maior ou igual a zero.")
        if not vaga.ocupada:
            raise ValueError(f"A vaga {vaga.numero} já está livre.")
        veiculo = vaga.veiculo
        tarifa = veiculo.calcular_tarifa(num_horas)
        if not math.isfinite(tarifa):
            raise ValueError("O número de horas informado resulta em uma tarifa inválida.")
        entrada = next((evento for evento in reversed(self._historico)
                        if evento["acao"] == "entrada"
                        and evento["placa"] == veiculo.placa
                        and evento["vaga"] == vaga.numero), None)
        vaga.liberar()
        self._historico.append({
            "acao": "saida", "placa": veiculo.placa,
            "tipo": type(veiculo).__name__.lower(), "modelo": veiculo.modelo,
            "vaga": vaga.numero,
            "horario_entrada": entrada["horario_entrada"] if entrada else None,
            "horario_saida": datetime.now().astimezone().isoformat(),
            "horas": num_horas, "valor": tarifa,
        })
        return tarifa

    def relatorio(self):
        ocupadas = sum(1 for vaga in self.vagas if vaga.ocupada)
        return {
            "ocupadas": ocupadas,
            "livres": len(self.vagas) - ocupadas,
            "faturamento": sum(e["valor"] for e in self._historico if e["acao"] == "saida"),
        }

    @classmethod
    def reconstruir(cls, dados):
        """Reconstrói um agregado validado em memória, sem acessar arquivos."""
        from model.carro import Carro
        from model.moto import Moto
        from model.caminhao import Caminhao

        est = cls()
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
                est._historico[-1] = deepcopy(evento)
        except (KeyError, TypeError, ValueError, OverflowError) as erro:
            raise ValueError(f"Histórico JSON inconsistente; arquivo preservado: {erro}") from erro
        return est

    @classmethod
    def carregar_historico(cls, arquivo="historico.json"):
        """Adaptador da API v2; novos consumidores devem usar Repository."""
        from repository.estacionamento_repository import EstacionamentoRepository
        repository = EstacionamentoRepository(arquivo)
        est = repository.carregar()
        est._repository_legado = repository
        est._arquivo_legado = arquivo
        return est

    def salvar_historico(self, arquivo=None):
        """Adaptador da API v2, sem leitura ou escrita implementada no Model."""
        from pathlib import Path
        from repository.estacionamento_repository import EstacionamentoRepository
        repository = self._repository_legado
        destino = self._arquivo_legado if arquivo is None else arquivo
        if repository is None or Path(destino).resolve() != repository.arquivo.resolve():
            repository = EstacionamentoRepository(destino)
        repository.salvar(self)
        self._repository_legado = repository
        self._arquivo_legado = destino
