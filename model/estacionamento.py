from copy import deepcopy
import math
from datetime import datetime
from decimal import Context, Decimal, DecimalException, localcontext

from model.caminhao import Caminhao
from model.carro import Carro
from model.categorias_cliente import classe_da_categoria
from model.cliente import Cliente
from model.estadia import Cobranca, Estadia, reais_de_centavos
from model.moto import Moto
from model.vaga import Vaga
from model.veiculo import Veiculo


_CLASSES_DE_VEICULOS = {"carro": Carro, "moto": Moto, "caminhao": Caminhao}


class Estacionamento:
    def __init__(self, arquivo="historico.json"):
        self._vagas = [Vaga(num+1) for num in range(10)]
        self._historico = []
        self._veiculos = {}
        self._clientes = {}
        self._vinculos = {}
        self._estadias = {}
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

    def cadastrar_cliente(self, cliente):
        if (not isinstance(cliente, Cliente)
                or type(cliente) is not classe_da_categoria(cliente.categoria)):
            raise ValueError("Informe um cliente de uma categoria reconhecida.")
        if cliente.identificador in self._clientes:
            raise ValueError(f"Cliente {cliente.identificador} já cadastrado.")
        self._clientes[cliente.identificador] = cliente
        self._historico.append({
            "acao": "cadastro_cliente", "identificador": cliente.identificador,
            "nome": cliente.nome, "categoria": cliente.categoria,
        })
        return cliente

    def buscar_cliente(self, identificador):
        chave = Cliente.normalizar_identificador(identificador)
        if chave not in self._clientes:
            raise ValueError(f"Cliente {chave} não cadastrado.")
        return self._clientes[chave]

    def listar_clientes(self):
        return tuple(self._clientes.values())

    def vincular_veiculo(self, placa, cliente_id):
        veiculo = self.buscar_veiculo(placa)
        cliente = self.buscar_cliente(cliente_id)
        if veiculo.placa in self._vinculos:
            raise ValueError("Veículo já vinculado a um cliente.")
        if any(vaga.veiculo is veiculo for vaga in self._vagas):
            raise ValueError("Não é possível vincular um veículo estacionado.")
        self._vinculos[veiculo.placa] = cliente
        self._historico.append({"acao": "vinculo", "placa": veiculo.placa,
                                "cliente_id": cliente.identificador})

    def cliente_do_veiculo(self, placa):
        return self._vinculos.get(self.buscar_veiculo(placa).placa)

    def veiculos_do_cliente(self, cliente_id):
        cliente = self.buscar_cliente(cliente_id)
        return tuple(self._veiculos[p] for p, dono in self._vinculos.items() if dono is cliente)

    def iniciar_estadia(self, placa, vaga, cliente_id):
        cliente = self.buscar_cliente(cliente_id)
        if self.cliente_do_veiculo(placa) is not cliente:
            raise ValueError("O veículo não está vinculado ao cliente informado.")
        self.estacionar_cadastrado(placa, vaga)

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
        self._estacionar(veiculo, num_vaga, datetime.now().astimezone().isoformat())

    def _estacionar(self, veiculo, num_vaga, horario):
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
        evento = {
            "acao": "entrada", "placa": veiculo.placa,
            "tipo": type(veiculo).__name__.lower(), "modelo": veiculo.modelo,
            "vaga": vaga.numero, "horario_entrada": horario,
        }
        cliente = self._vinculos.get(veiculo.placa)
        estadia = None
        if cliente is not None:
            # O identificador é a posição da entrada no histórico, contando a partir de 1.
            estadia = Estadia(len(self._historico) + 1, veiculo, cliente, vaga, horario)
            evento.update(acao="entrada_cliente", cliente_id=cliente.identificador,
                          categoria=estadia.categoria, estadia_id=estadia.identificador)
        vaga.ocupar(veiculo, estadia=estadia)
        self._veiculos[veiculo.placa] = veiculo
        if estadia is not None:
            self._estadias[veiculo.placa] = estadia
        self._historico.append(evento)

    def _estadia_ativa(self, placa):
        veiculo = self.buscar_veiculo(placa)
        estadia = self._estadias.get(veiculo.placa)
        if estadia is None:
            raise ValueError("Não há estadia vinculada ativa para o veículo.")
        return estadia

    def consultar_cobranca(self, placa, horas):
        return self._estadia_ativa(placa).consultar_cobranca(horas)

    def consultar_pagamento(self, placa):
        return self._estadia_ativa(placa).pagamento

    def _validar_consulta(self, cobranca):
        if not isinstance(cobranca, Cobranca):
            raise ValueError("Informe uma consulta de cobrança da estadia.")
        estadia = self._estadia_ativa(cobranca.placa)
        atual = estadia.consultar_cobranca(cobranca.horas)
        if atual != cobranca:
            raise ValueError("Cobrança incompatível com a estadia ativa.")
        return estadia, atual

    def confirmar_pagamento(self, cobranca, *, confirmado):
        estadia, atual = self._validar_consulta(cobranca)
        estadia.confirmar_pagamento(atual, confirmado)
        self._historico.append({"acao": "pagamento_confirmado", **atual.dados_do_pagamento()})

    def concluir_saida(self, cobranca):
        return self._concluir_saida(cobranca, datetime.now().astimezone().isoformat())

    def _concluir_saida(self, cobranca, horario):
        estadia, atual = self._validar_consulta(cobranca)
        situacao = estadia.situacao_para_saida(atual)
        if datetime.fromisoformat(horario) < datetime.fromisoformat(estadia.horario_entrada):
            raise ValueError("Saída anterior à entrada.")
        evento = {
            "acao": "saida_cliente", **atual.dados_do_pagamento(),
            "cliente_id": estadia.cliente.identificador, "categoria": estadia.categoria,
            "vaga": estadia.vaga.numero, "horario_entrada": estadia.horario_entrada,
            "horario_saida": horario, "tarifa_base": str(atual.tarifa_base),
            "desconto": str(atual.desconto), "pagamento": situacao,
        }
        estadia.vaga.liberar(estadia=estadia)
        del self._estadias[atual.placa]
        self._historico.append(evento)
        return atual.valor_devido

    def retirar(self, num_vaga, num_horas):
        vaga = self._buscar_vaga(num_vaga)
        if vaga.ocupada and vaga.veiculo.placa in self._vinculos:
            raise ValueError("Use a consulta de cobrança e a conclusão da estadia vinculada.")
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

    def _faturamento(self):
        total_legado = sum(e["valor"] for e in self._historico if e["acao"] == "saida")
        valores_centavos = [e["valor_centavos"] for e in self._historico if e["acao"] == "saida_cliente"]
        if not valores_centavos:
            return total_legado
        legado = Decimal(str(total_legado))
        if not legado.is_finite():
            return legado
        novo = reais_de_centavos(sum(valores_centavos))
        # Inclui as casas fracionárias do legado sem arredondá-las a centavos.
        casas = min(legado.as_tuple().exponent, -2)
        precisao = max(legado.adjusted(), novo.adjusted()) - casas + 2
        with localcontext(Context(prec=precisao)):
            return legado + novo

    def relatorio(self):
        ocupadas = sum(1 for vaga in self.vagas if vaga.ocupada)
        return {
            "ocupadas": ocupadas,
            "livres": len(self.vagas) - ocupadas,
            "faturamento": self._faturamento(),
        }

    def _reproduzir_evento_veiculo(self, acao, evento):
        classe = _CLASSES_DE_VEICULOS[evento["tipo"]]
        # Arquivos da versão anterior não registravam o modelo.
        veiculo = classe(evento["placa"], evento.get("modelo", "Modelo não registrado"))
        if evento['placa'] != veiculo.placa:
            raise ValueError("Placa do histórico não normalizada.")
        if acao in ("entrada", "saida") and veiculo.placa in self._vinculos:
            raise ValueError("Evento legado incompatível com veículo vinculado.")
        if acao == "cadastro":
            self.cadastrar_veiculo(veiculo)
        elif acao == "entrada":
            datetime.fromisoformat(evento["horario_entrada"])
            self.estacionar(veiculo, evento["vaga"])
        elif acao == "saida":
            entrada = next((e for e in reversed(self._historico)
                            if e['acao'] == 'entrada' and e['placa'] == veiculo.placa), None)
            if entrada is None or evento['horario_entrada'] != entrada['horario_entrada']:
                raise ValueError("Saída sem entrada correspondente.")
            inicio = datetime.fromisoformat(evento['horario_entrada'])
            fim = datetime.fromisoformat(evento['horario_saida'])
            if fim < inicio:
                raise ValueError("Saída anterior à entrada.")
            vaga = self._buscar_vaga(evento['vaga'])
            if not vaga.ocupada or vaga.veiculo.placa != veiculo.placa:
                raise ValueError("Saída incompatível com a ocupação.")
            if type(vaga.veiculo) is not classe or vaga.veiculo.modelo != veiculo.modelo:
                raise ValueError("Tipo ou modelo da saída incompatível.")
            valor = evento['valor']
            if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not math.isfinite(valor):
                raise ValueError("Valor inválido.")
            if "valor_centavos" in evento:
                centavos = evento["valor_centavos"]
                if type(centavos) is not int or reais_de_centavos(centavos) != Decimal(str(valor)):
                    raise ValueError("Centavos incompatíveis com o valor legado.")
            tarifa = self.retirar(evento['vaga'], evento['horas'])
            if valor != tarifa:
                raise ValueError("Valor incompatível com a tarifa.")

    def _reproduzir_evento_estadia(self, acao, evento):
        placa = evento["placa"]
        if acao == "vinculo":
            self.vincular_veiculo(placa, evento["cliente_id"])
        elif acao == "entrada_cliente":
            horario = evento["horario_entrada"]
            if datetime.fromisoformat(horario).tzinfo is None:
                raise ValueError("Entrada vinculada exige horário com fuso.")
            if self.cliente_do_veiculo(placa) is None:
                raise ValueError("Entrada sem vínculo cadastrado.")
            self._estacionar(self.buscar_veiculo(placa), evento["vaga"], horario)
        else:
            if not isinstance(evento["horas"], str):
                raise ValueError("As horas da estadia devem estar em texto decimal.")
            consulta = self.consultar_cobranca(placa, Decimal(evento["horas"]))
            if acao == "pagamento_confirmado":
                self.confirmar_pagamento(consulta, confirmado=True)
            else:
                self._concluir_saida(consulta, evento["horario_saida"])

        # A regra de negócio gera o evento esperado, inclusive os centavos e o estado de pagamento.
        esperado = self._historico[-1]
        if evento.keys() != esperado.keys() or any(
            type(evento[k]) is not type(v) or evento[k] != v for k, v in esperado.items()
        ):
            raise ValueError("Evento incompatível com o vínculo, a estadia ou a cobrança.")

    @classmethod
    def reconstruir(cls, dados):
        """Reconstrói um agregado validado em memória, sem acessar arquivos."""
        est = cls()
        try:
            if not isinstance(dados, list):
                raise ValueError("O histórico deve ser uma lista.")
            for evento in dados:
                if not isinstance(evento, dict):
                    raise ValueError("Evento deve ser um objeto.")
                acao = evento["acao"]
                if acao == "cadastro_cliente":
                    classe = classe_da_categoria(evento["categoria"])
                    nome, identificador = evento["nome"], evento["identificador"]
                    cliente = classe(nome, identificador=identificador)
                    if cliente.nome != nome or cliente.identificador != identificador:
                        raise ValueError("Cadastro de cliente não normalizado.")
                    est.cadastrar_cliente(cliente)
                elif acao in ("cadastro", "entrada", "saida"):
                    est._reproduzir_evento_veiculo(acao, evento)
                elif acao in ("vinculo", "entrada_cliente", "pagamento_confirmado", "saida_cliente"):
                    est._reproduzir_evento_estadia(acao, evento)
                else:
                    raise ValueError("Ação desconhecida.")
                # Mantém horários e campos originais, sem substituir pela hora da leitura.
                est._historico[-1] = deepcopy(evento)
        except (KeyError, TypeError, ValueError, OverflowError, DecimalException) as erro:
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
