"""Casos de uso de um servidor MOVE de processo único com múltiplas threads."""
from pathlib import Path
from threading import Lock
from weakref import WeakValueDictionary

from controller.controller import Controller
from model.vaga import DISTRIBUICAO
from model.caminhao import Caminhao
from model.carro import Carro
from model.cliente_comum import ClienteComum
from model.moto import Moto
from persistence.historico_json import FalhaAntesDaSubstituicao, HistoricoAlterado
from service import representacoes as dto


class ErroDeNegocio(ValueError):
    """O domínio ou as pré-condições da solicitação recusaram a operação."""


class ErroDeInfraestrutura(Exception):
    """Falha ao carregar, validar ou persistir o histórico."""


class ConflitoDeHistorico(ErroDeInfraestrutura):
    """O Repository detectou uma alteração externa antes da substituição."""


class ResultadoIncerto(ErroDeInfraestrutura):
    """A gravação falhou ao confirmar o resultado. A operação não foi repetida."""

    def __init__(self, verificacao):
        self.verificacao = verificacao
        super().__init__(f"Confirmação de gravação indisponível ({verificacao}). Consulte o histórico.")


_bloqueios = WeakValueDictionary()
_guarda_do_registro = Lock()


class EstacionamentoService:
    def __init__(self, arquivo, *, distribuicao=DISTRIBUICAO):
        self._distribuicao = distribuicao
        self._arquivo = Path(arquivo).expanduser().resolve()
        with _guarda_do_registro:
            bloqueio = _bloqueios.get(self._arquivo)
            if bloqueio is None:
                bloqueio = _bloqueios[self._arquivo] = Lock()
            self._bloqueio = bloqueio

    def _executar(self, operacao, *, gravar=False):
        with self._bloqueio:
            try:
                ctrl = Controller(self._arquivo, distribuicao=self._distribuicao)
            except (OSError, ValueError, RecursionError) as erro:
                raise ErroDeInfraestrutura(f"Falha ao carregar o histórico: {erro}") from erro
            try:
                resultado = operacao(ctrl)
            except ValueError as erro:
                raise ErroDeNegocio(str(erro)) from erro
            if gravar:
                self._persistir(ctrl)
            return resultado

    def _persistir(self, ctrl):
        anterior = ctrl.repository.versao_carregada
        try:
            ctrl.salvar()
        except HistoricoAlterado as erro:
            raise ConflitoDeHistorico(str(erro)) from erro
        except FalhaAntesDaSubstituicao as erro:
            raise ErroDeInfraestrutura(f"Gravação interrompida antes da substituição: {erro}") from erro
        except Exception as erro:
            # A exceção pode ter chegado depois do replace. Apenas ler, ainda sob o lock.
            try:
                leitor = Controller(self._arquivo, distribuicao=self._distribuicao)
            except (OSError, ValueError, RecursionError):
                raise ResultadoIncerto("releitura_indisponivel") from erro
            if leitor.repository.versao_carregada == anterior:
                raise ErroDeInfraestrutura("Falha de gravação. O histórico anterior foi preservado.") from erro
            if leitor.consultar_historico() == ctrl.consultar_historico():
                raise ResultadoIncerto("operacao_presente") from erro
            raise ResultadoIncerto("historico_divergente") from erro

    def cadastrar_cliente(self, categoria, nome):
        return self._executar(lambda c: dto.cliente(c.cadastrar_cliente(categoria, nome)), gravar=True)

    def confirmar_cadastro_pessoal(self, cliente: ClienteComum):
        """Conclui uma reserva de UUID do servidor e reconhece sua eventual gravação anterior."""
        if type(cliente) is not ClienteComum:
            raise ErroDeNegocio("O cadastro pessoal exige um cliente comum.")

        def confirmar(ctrl):
            for existente in ctrl.listar_clientes():
                if existente.identificador == cliente.identificador:
                    if existente.nome != cliente.nome or existente.categoria != cliente.categoria:
                        raise ErroDeInfraestrutura("O histórico diverge do cadastro pessoal pendente.")
                    return
            ctrl.estacionamento.cadastrar_cliente(cliente)
            self._persistir(ctrl)

        self._executar(confirmar)

    def buscar_cliente(self, identificador):
        return self._executar(lambda c: dto.cliente(c.buscar_cliente(identificador)))

    def listar_clientes(self):
        return self._executar(lambda c: [dto.cliente(obj) for obj in c.listar_clientes()])

    def cadastrar_veiculo(self, tipo, placa, modelo, motorizacao="desconhecida"):
        return self._executar(lambda c: dto.veiculo(c.cadastrar_veiculo(tipo, placa, modelo, motorizacao)), gravar=True)

    def buscar_veiculo(self, placa):
        return self._executar(lambda c: dto.veiculo(c.buscar_veiculo(placa)))

    def cadastrar_veiculo_do_cliente(self, cliente_id, tipo, placa, modelo, motorizacao="desconhecida"):
        def cadastrar(ctrl):
            novo = ctrl.cadastrar_veiculo(tipo, placa, modelo, motorizacao)
            ctrl.vincular_veiculo(novo.placa, cliente_id)
            return dto.veiculo(novo)
        return self._executar(cadastrar, gravar=True)

    def listar_veiculos(self):
        return self._executar(lambda c: [dto.veiculo(obj) for obj in c.listar_veiculos()])

    def vincular_veiculo(self, placa, cliente_id):
        def vincular(c):
            c.vincular_veiculo(placa, cliente_id)
            return {"placa": c.buscar_veiculo(placa).placa,
                    "cliente_id": c.buscar_cliente(cliente_id).identificador}

        return self._executar(vincular, gravar=True)

    def cliente_do_veiculo(self, placa):
        def consultar(c):
            cliente = c.cliente_do_veiculo(placa)
            return dto.cliente(cliente) if cliente is not None else None

        return self._executar(consultar)

    def veiculos_do_cliente(self, cliente_id):
        return self._executar(lambda c: [dto.veiculo(obj) for obj in c.veiculos_do_cliente(cliente_id)])

    def consultar_vagas(self):
        return self._executar(dto.vagas)

    @staticmethod
    def consultar_tarifas():
        """Preços de referência em reais por hora, publicados pelas subclasses."""
        return {tipo.__name__.lower(): tipo.TARIFA_POR_HORA for tipo in (Carro, Moto, Caminhao)}

    def consultar_ocupacao(self, *, titular=None, detalhada=False):
        def consultar(ctrl):
            dados = dto.ocupacao(ctrl, titular)
            if detalhada:
                dados['indicadores'] = dto.indicadores(ctrl)
                if titular is None:
                    dados['mapa'] = dto.vagas(ctrl)
            return dados
        return self._executar(consultar)

    def reservar_vaga(self, cliente_id, placa, vaga, *, vip=False):
        return self._executar(lambda c: c.estacionamento.reservar_vaga(cliente_id, placa, vaga, vip=vip), gravar=True)

    def opcoes_de_vaga(self, titular, placa, *, vip=False, entrada=False):
        return self._executar(lambda c: dto.opcoes(c, titular, placa, vip, entrada))

    def indicadores(self):
        return self._executar(dto.indicadores)

    def autorizacoes(self, cliente_id):
        return self._executar(lambda c: c.estacionamento.autorizacoes(cliente_id))

    def conferir_autorizacao(self, cliente_id, placa, grupo, beneficiario, conferencia, validade, numero_beneficiario=1):
        return self._executar(lambda c: c.estacionamento.conferir_autorizacao(
            cliente_id, placa, grupo, beneficiario, conferencia, validade, numero_beneficiario), gravar=True)

    def revogar_autorizacao(self, cliente_id, numero):
        return self._executar(lambda c: c.estacionamento.revogar_autorizacao(cliente_id, numero), gravar=True)

    def alterar_carregador(self, vaga, disponivel):
        return self._executar(lambda c: c.estacionamento.alterar_carregador(vaga, disponivel), gravar=True)

    def cancelar_reserva(self, cliente_id, vaga, reserva_id):
        return self._executar(lambda c: c.estacionamento.cancelar_reserva(cliente_id, vaga, reserva_id), gravar=True)

    def mudar_categoria(self, cliente_id, origem, destino):
        return self._executar(lambda c: c.estacionamento.mudar_categoria(cliente_id, origem, destino), gravar=True)

    def mudancas_de_categoria(self, cliente_id):
        return self._executar(lambda c: [e for e in reversed(c.consultar_historico())
                                         if e['acao'] == 'mudanca_categoria' and e['cliente_id'] == cliente_id])

    def iniciar_estadia(self, placa, vaga, cliente_id, *, beneficiario_presente=False, expectativa_uso=None):
        def entrar(c):
            if expectativa_uso is not None:
                opcoes = dto.opcoes(c, cliente_id, placa, False, True)
                atual = next((v for v in opcoes if v['numero'] == vaga), None)
                if (not atual or atual['motivo'] or
                        any(atual[k] != expectativa_uso[k] for k in ('classificacao','vip','reserva_id','conferencia'))):
                    raise ValueError('As condições da vaga mudaram. Revise a entrada.')
            c.iniciar_estadia(placa, vaga, cliente_id, beneficiario_presente=beneficiario_presente)
            return dto.estadia_do_evento(c, c.consultar_historico()[-1])

        return self._executar(entrar, gravar=True)

    def listar_estadias_ativas(self):
        return self._executar(dto.estadias_ativas)

    def consultar_estadia(self, estadia_id):
        return self._executar(lambda c: dto.estadia(c, estadia_id))

    @staticmethod
    def _cotar(ctrl, placa, horas):
        if isinstance(horas, str):
            horas = dto.decimal_de_texto(horas)
        return ctrl.consultar_cobranca(placa, horas)

    def consultar_cobranca(self, placa, horas):
        return self._executar(lambda c: dto.cobranca(self._cotar(c, placa, horas)))

    def _conferir(self, ctrl, placa, horas, expectativa):
        atual = self._cotar(ctrl, placa, horas)
        dto.conferir_expectativa(atual, expectativa)
        return atual

    def confirmar_pagamento(self, placa, horas, expectativa, *, confirmado):
        def confirmar(c):
            cobranca = self._conferir(c, placa, horas, expectativa)
            c.confirmar_pagamento(cobranca, confirmado=confirmado)
            return dto.cobranca(cobranca)

        return self._executar(confirmar, gravar=True)

    def consultar_pagamento(self, placa):
        def consultar(c):
            pagamento = c.consultar_pagamento(placa)
            return dto.cobranca(pagamento) if pagamento is not None else None

        return self._executar(consultar)

    def concluir_saida(self, placa, horas, expectativa):
        def concluir(c):
            cobranca = self._conferir(c, placa, horas, expectativa)
            c.concluir_saida(cobranca)
            return dto.estadia(c, cobranca.estadia_id)

        return self._executar(concluir, gravar=True)

    def listar_pagamentos_abertos(self):
        return self._executar(lambda c: [e["cobranca"] for e in dto.estadias_ativas(c)
                                         if e["pagamento"] == "confirmado"])

    def consultar_faturamento(self):
        return self._executar(dto.faturamento)

    def consultar_historico(self):
        return self._executar(dto.historico)
