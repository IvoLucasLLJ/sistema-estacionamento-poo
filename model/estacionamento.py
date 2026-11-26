from copy import deepcopy
import math
from datetime import UTC, date, datetime, timedelta
from decimal import Context, Decimal, DecimalException, localcontext

from model.caminhao import Caminhao
from model.carro import Carro
from model.categorias_cliente import classe_da_categoria, preco_da_mudanca
from model.cliente import Cliente
from model.estadia import Cobranca, Estadia, reais_de_centavos
from model.moto import Moto
from model.uso_vaga import AutorizacaoUso, BeneficiarioFicticio, ContextoUso
from model.vaga import DISTRIBUICAO, ReservaVaga, VagaProtegida, construir_vagas
from model.veiculo import Veiculo


_CLASSES_DE_VEICULOS = {"carro": Carro, "moto": Moto, "caminhao": Caminhao}
_ORIGEM_CIVIL = datetime(1970, 1, 1)
_ORIGEM_UTC = datetime(1970, 1, 1, tzinfo=UTC)


def _saida_legada_anterior(entrada, saida):
    inicio = datetime.fromisoformat(entrada)
    fim = datetime.fromisoformat(saida)
    if (inicio.tzinfo is None) == (fim.tzinfo is None):
        return fim < inicio

    # Um relógio civil sem fuso admite deslocamentos estritamente entre -24 e +24 h.
    # Só há inversão certa quando nenhum desses deslocamentos permite a sequência.
    inicio_relativo = inicio - (_ORIGEM_CIVIL if inicio.tzinfo is None else _ORIGEM_UTC)
    fim_relativo = fim - (_ORIGEM_CIVIL if fim.tzinfo is None else _ORIGEM_UTC)
    return inicio_relativo - fim_relativo >= timedelta(days=1)


class Estacionamento:
    def __init__(self, arquivo="historico.json", *, distribuicao=DISTRIBUICAO):
        self._vagas = construir_vagas(distribuicao)
        self._autorizacoes = {}
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
        self._vinculos[veiculo.placa] = cliente.identificador
        self._historico.append({"acao": "vinculo", "placa": veiculo.placa,
                                "cliente_id": cliente.identificador})

    def cliente_do_veiculo(self, placa):
        return self._clientes.get(self._vinculos.get(self.buscar_veiculo(placa).placa))

    def veiculos_do_cliente(self, cliente_id):
        cliente = self.buscar_cliente(cliente_id)
        return tuple(self._veiculos[p] for p, dono in self._vinculos.items() if dono == cliente.identificador)

    def mudar_categoria(self, cliente_id, origem, destino):
        atual = self.buscar_cliente(cliente_id)
        if atual.categoria != origem:
            raise ValueError("Sua categoria mudou. Confira o valor antes de confirmar.")
        valor = preco_da_mudanca(origem, destino)
        # A estadia aberta conserva a instância que recebeu na entrada.
        novo = classe_da_categoria(destino)(atual.nome, identificador=atual.identificador)
        self._clientes[novo.identificador] = novo
        self._historico.append(dict(acao="mudanca_categoria", cliente_id=novo.identificador,
                                    origem=origem, categoria=destino, valor_centavos=valor))

    def conferir_autorizacao(self, cliente_id, placa, grupo, beneficiario, conferencia, validade, numero_beneficiario=1):
        veiculo = self.buscar_veiculo(placa)
        if self._vinculos.get(veiculo.placa) != self.buscar_cliente(cliente_id).identificador:
            raise ValueError("Veículo sem vínculo com o titular.")
        numero = len(self._historico) + 1
        if not isinstance(validade, str):
            raise ValueError("Informe uma data de validade.")
        pessoa = BeneficiarioFicticio(cliente_id, numero_beneficiario)
        credencial = AutorizacaoUso(numero, cliente_id, veiculo.placa, grupo, beneficiario,
                                    conferencia, date.fromisoformat(validade), pessoa)
        if conferencia == "digital" and any(a.pessoa == pessoa and a.grupo == grupo and a.conferencia == "digital"
                                           and a.placa != veiculo.placa for a in self.autorizacoes(cliente_id)):
            raise ValueError("Revogue o vínculo digital anterior deste beneficiário antes de vinculá-lo a outro veículo.")
        self._autorizacoes[numero] = credencial
        self._historico.append(dict(acao="autorizacao_conferida", autorizacao_id=numero,
                                    cliente_id=cliente_id, placa=veiculo.placa, grupo=grupo,
                                    beneficiario=beneficiario, conferencia=conferencia, validade=validade,
                                    numero_beneficiario=numero_beneficiario))
        return numero

    def autorizacoes(self, cliente_id):
        return tuple(a for a in self._autorizacoes.values() if a.cliente_id == cliente_id)

    def revogar_autorizacao(self, cliente_id, numero):
        autorizacao = self._autorizacoes.get(numero)
        if type(numero) is not int or not autorizacao or autorizacao.cliente_id != cliente_id:
            raise ValueError("Autorização indisponível para revogação.")
        del self._autorizacoes[numero]
        self._historico.append(dict(acao="autorizacao_revogada", cliente_id=cliente_id, autorizacao_id=numero))

    def alterar_carregador(self, numero, disponivel):
        aparelho = self._buscar_vaga(numero).carregador
        if aparelho is None:
            raise ValueError("Esta vaga não possui carregador.")
        aparelho.definir_disponibilidade(disponivel)
        self._historico.append(dict(acao="estado_carregador", vaga=numero, disponivel=disponivel))

    def contexto(self, veiculo, dia, vip=False, autorizacao_id=None):
        if type(vip) is not bool:
            raise ValueError("Destinação inválida.")
        dono = self._clientes.get(self._vinculos.get(veiculo.placa))
        autorizacoes = self.autorizacoes(dono.identificador) if dono else ()
        if autorizacao_id is not None:
            autorizacoes = tuple(a for a in autorizacoes if a.identificador == autorizacao_id)
        return ContextoUso(dono.identificador if dono else None, dono.categoria if dono else None,
                           veiculo, dia, autorizacoes, vip)

    def reservar_vaga(self, cliente_id, placa, numero, *, vip=False):
        self._reservar_vaga(cliente_id, placa, numero, vip, date.today())

    def _reservar_vaga(self, cliente_id, placa, numero, vip, dia):
        titular = self.buscar_cliente(cliente_id)
        placa = Veiculo.normalizar_placa(placa)
        if self._vinculos.get(placa) != titular.identificador:
            raise ValueError("Selecione um veículo do seu cadastro.")
        if any(v.ocupada and v.veiculo.placa == placa for v in self.vagas):
            raise ValueError("Este veículo já está estacionado.")
        if any(v.reserva and v.reserva.placa == placa for v in self.vagas):
            raise ValueError("Este veículo já tem uma reserva. Cancele-a para escolher outra vaga.")
        vaga = self._buscar_vaga(numero)
        contexto = self.contexto(self.buscar_veiculo(placa), dia, vip)
        vaga.validar_uso(contexto)
        autorizacao = contexto.autorizacao(vaga.grupos) if isinstance(vaga, VagaProtegida) else None
        reserva = ReservaVaga(len(self._historico) + 1, titular.identificador, placa, vip,
                              autorizacao.identificador if autorizacao else None)
        vaga.reservar(reserva, contexto=contexto)
        self._historico.append(dict(acao="reserva_vaga", cliente_id=titular.identificador,
                                    vaga=numero, placa=placa, reserva_id=reserva.identificador))
        if vip or vaga.classificacao != "comum":
            self._historico[-1].update(vip=vip, dia=dia.isoformat(), classificacao=vaga.classificacao)
        if isinstance(vaga, VagaProtegida):
            self._historico[-1]["autorizacao_id"] = contexto.autorizacao(vaga.grupos).identificador

    def cancelar_reserva(self, cliente_id, numero, reserva_id):
        vaga = self._buscar_vaga(numero)
        reserva = vaga.reserva
        vaga.cancelar_reserva(cliente_id, reserva_id)
        self._historico.append(dict(acao="cancelamento_reserva", cliente_id=cliente_id,
                                    vaga=numero, placa=reserva.placa, reserva_id=reserva_id))

    def iniciar_estadia(self, placa, vaga, cliente_id, *, beneficiario_presente=False):
        cliente = self.buscar_cliente(cliente_id)
        if self.cliente_do_veiculo(placa) is not cliente:
            raise ValueError("O veículo não está vinculado ao cliente informado.")
        self._estacionar(self.buscar_veiculo(placa), vaga, datetime.now().astimezone().isoformat(),
                         beneficiario_presente=beneficiario_presente)

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
        if veiculo.motorizacao != "desconhecida":
            self._historico[-1]["motorizacao"] = veiculo.motorizacao
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

    def _estacionar(self, veiculo, num_vaga, horario, *, registrar_classe=True, beneficiario_presente=False):
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
        if any(v is not vaga and v.reserva and v.reserva.placa == veiculo.placa for v in self.vagas):
            raise ValueError("Este veículo tem reserva em outra vaga.")
        cliente = self._clientes.get(self._vinculos.get(veiculo.placa))
        estadia = None
        if cliente is not None:
            # O identificador é a posição da entrada no histórico, contando a partir de 1.
            estadia = Estadia(len(self._historico) + 1, veiculo, cliente, vaga, horario)
            evento.update(acao="entrada_cliente", cliente_id=cliente.identificador,
                          categoria=estadia.categoria, estadia_id=estadia.identificador)
        vip = bool(vaga.reserva and vaga.reserva.vip)
        contexto = self.contexto(veiculo, datetime.fromisoformat(horario).date(), vip,
                                 vaga.reserva.autorizacao_id if vaga.reserva else None)
        vaga.validar_uso(contexto)
        if registrar_classe or vip or vaga.classificacao != "comum":
            evento.update(classificacao=vaga.classificacao, vip=vip)
        if isinstance(vaga, VagaProtegida):
            if beneficiario_presente is not True:
                raise ValueError("Confirme a presença do beneficiário nesta entrada identificada.")
            evento["autorizacao_id"] = contexto.autorizacao(vaga.grupos).identificador
        if existente is None and veiculo.motorizacao != "desconhecida":
            evento["motorizacao"] = veiculo.motorizacao
        vaga.ocupar(veiculo, estadia=estadia, contexto=contexto)
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
        return self._retirar_legado(num_vaga, num_horas, datetime.now().astimezone().isoformat())

    def _retirar_legado(self, num_vaga, num_horas, horario_saida):
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
        if entrada is None:
            raise ValueError("Saída sem entrada correspondente.")
        if _saida_legada_anterior(entrada["horario_entrada"], horario_saida):
            raise ValueError("Saída anterior à entrada.")
        vaga.liberar()
        self._historico.append({
            "acao": "saida", "placa": veiculo.placa,
            "tipo": type(veiculo).__name__.lower(), "modelo": veiculo.modelo,
            "vaga": vaga.numero,
            "horario_entrada": entrada["horario_entrada"],
            "horario_saida": horario_saida,
            "horas": num_horas, "valor": tarifa,
        })
        return tarifa

    def _faturamento(self):
        legados = [e['valor'] for e in self._historico if e['acao'] == 'saida']
        valores = [Decimal(str(valor)) for valor in legados]
        centavos = [e['valor_centavos'] for e in self._historico if e['acao'] == 'saida_cliente']
        if centavos:
            valores.append(reais_de_centavos(sum(centavos)))
        if not valores:
            return 0
        # Alinha as casas de todas as saídas e reserva espaço para os transportes da soma.
        precisao = max(v.adjusted() for v in valores) - min(v.as_tuple().exponent for v in valores)
        with localcontext(Context(prec=max(1, precisao + len(str(len(valores))) + 1))):
            total = sum(valores, Decimal(0))
        if not centavos:
            # Mantém o tipo histórico quando sua representação pública reproduz a soma.
            legado = float(total) if any(isinstance(v, float) for v in legados) else int(total)
            if Decimal(str(legado)) == total:
                return legado
        return total

    def relatorio(self):
        ocupadas = sum(1 for vaga in self.vagas if vaga.ocupada)
        return {
            "ocupadas": ocupadas,
            "livres": sum(vaga.livre for vaga in self.vagas),
            "faturamento": self._faturamento(),
        }

    def _reproduzir_evento_veiculo(self, acao, evento):
        classe = _CLASSES_DE_VEICULOS[evento["tipo"]]
        # Arquivos da versão anterior não registravam o modelo.
        veiculo = classe(evento["placa"], evento.get("modelo", "Modelo não registrado"),
                       evento.get("motorizacao", "desconhecida"))
        if evento['placa'] != veiculo.placa:
            raise ValueError("Placa do histórico não normalizada.")
        if acao in ("entrada", "saida") and veiculo.placa in self._vinculos:
            raise ValueError("Evento legado incompatível com veículo vinculado.")
        if acao == "cadastro":
            self.cadastrar_veiculo(veiculo)
        elif acao == "entrada":
            datetime.fromisoformat(evento["horario_entrada"])
            self._estacionar(veiculo, evento["vaga"], evento["horario_entrada"],
                             registrar_classe="classificacao" in evento)
            for campo in ("classificacao", "vip"):
                if self._historico[-1].get(campo) != evento.get(campo):
                    raise ValueError("Destinação da entrada incompatível.")
        elif acao == "saida":
            entrada = next((e for e in reversed(self._historico)
                            if e['acao'] == 'entrada' and e['placa'] == veiculo.placa), None)
            if entrada is None or evento['horario_entrada'] != entrada['horario_entrada']:
                raise ValueError("Saída sem entrada correspondente.")
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
            tarifa = self._retirar_legado(evento['vaga'], evento['horas'], evento['horario_saida'])
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
            self._estacionar(self.buscar_veiculo(placa), evento["vaga"], horario,
                             registrar_classe="classificacao" in evento, beneficiario_presente="autorizacao_id" in evento)
        else:
            if not isinstance(evento["horas"], str):
                raise ValueError("As horas da estadia devem estar em texto decimal.")
            consulta = self.consultar_cobranca(placa, Decimal(evento["horas"]))
            if acao == "pagamento_confirmado":
                self.confirmar_pagamento(consulta, confirmado=True)
            else:
                self._concluir_saida(consulta, evento["horario_saida"])

        # A regra de negócio gera o evento esperado, inclusive os centavos e o estado de pagamento.
        self._validar_evento_reproduzido(evento)

    def _validar_evento_reproduzido(self, evento):
        esperado = self._historico[-1]
        if evento.keys() != esperado.keys() or any(
            type(evento[k]) is not type(v) or evento[k] != v for k, v in esperado.items()
        ):
            raise ValueError("Evento incompatível com o vínculo, a estadia ou a cobrança.")

    @classmethod
    def reconstruir(cls, dados, *, distribuicao=DISTRIBUICAO):
        """Reconstrói um agregado validado em memória, sem acessar arquivos."""
        est = cls(distribuicao=distribuicao)
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
                elif acao in ("autorizacao_conferida", "autorizacao_revogada", "estado_carregador"):
                    if acao == "autorizacao_conferida":
                        est.conferir_autorizacao(*(evento[k] for k in ("cliente_id", "placa", "grupo",
                                                "beneficiario", "conferencia", "validade", "numero_beneficiario")))
                    elif acao == "autorizacao_revogada":
                        est.revogar_autorizacao(evento["cliente_id"], evento["autorizacao_id"])
                    else:
                        est.alterar_carregador(evento["vaga"], evento["disponivel"])
                    est._validar_evento_reproduzido(evento)
                elif acao in ("reserva_vaga", "cancelamento_reserva", "mudanca_categoria"):
                    if acao == "reserva_vaga":
                        dia = date.fromisoformat(evento["dia"]) if "dia" in evento else date.min
                        est._reservar_vaga(evento["cliente_id"], evento["placa"], evento["vaga"],
                                           evento.get("vip", False), dia)
                    elif acao == "cancelamento_reserva":
                        est.cancelar_reserva(evento["cliente_id"], evento["vaga"], evento["reserva_id"])
                    else:
                        est.mudar_categoria(evento["cliente_id"], evento["origem"], evento["categoria"])
                    est._validar_evento_reproduzido(evento)
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
