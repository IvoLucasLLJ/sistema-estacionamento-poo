"""Identidade de acesso local, independente das categorias comerciais."""
import re
from dataclasses import asdict, dataclass, field, replace
from enum import StrEnum
from pathlib import Path
from uuid import UUID, uuid4

from werkzeug.security import check_password_hash, generate_password_hash

from model.cliente_comum import ClienteComum
from persistence import historico_json
from persistence.exclusividade import trava_de_arquivo
from service.estacionamento_service import ErroDeInfraestrutura


MASTER_DEMO = 'master.demo'
USUARIOS_DEMO = frozenset({MASTER_DEMO, 'gestao.demo', 'cliente.demo'})


class PapelAcesso(StrEnum):
    GESTAO = 'gestao'
    CLIENTE = 'cliente'


def normalizar_usuario(valor):
    if not isinstance(valor, str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,64}', valor.strip()):
        raise ValueError('Use até 64 letras sem acento, algarismos, pontos, hífens ou sublinhados.')
    return valor.strip().lower()


@dataclass(frozen=True)
class Identidade:
    id: str
    usuario: str
    papel: PapelAcesso
    cliente_id: str | None


@dataclass(frozen=True)
class ContextoAcesso:
    principal: Identidade
    pessoal_vinculada: Identidade | None = None

    def identidade_ativa(self, conta_pessoal_id):
        if conta_pessoal_id is None:
            return self.principal
        if self.pessoal_vinculada and self.pessoal_vinculada.id == conta_pessoal_id:
            return self.pessoal_vinculada
        return None

    def identidade_para(self, ambiente):
        if ambiente == self.principal.papel:
            return self.principal
        if ambiente == PapelAcesso.CLIENTE:
            return self.pessoal_vinculada
        return None


@dataclass(frozen=True)
class ContaUsuario:
    identidade: Identidade
    senha_hash: str = field(repr=False)
    nome_pendente: str | None = None

    @classmethod
    def criar(cls, identidade, senha, *, nome_pendente=None):
        if not isinstance(senha, str) or not 12 <= len(senha) <= 256:
            raise ValueError('Use uma senha de 12 a 256 caracteres.')
        return cls(identidade, generate_password_hash(senha, method='scrypt:32768:8:1'), nome_pendente)

    @classmethod
    def do_registro(cls, registro):
        campos = {'id', 'usuario', 'papel', 'cliente_id', 'senha_hash'}
        if not isinstance(registro, dict) or registro.keys() not in (campos, campos | {'nome_pendente'}):
            raise ValueError('Estrutura de conta inválida.')
        identidade = Identidade(registro['id'], normalizar_usuario(registro['usuario']),
                                PapelAcesso(registro['papel']), registro['cliente_id'])
        if str(UUID(identidade.id)) != identidade.id or identidade.usuario != registro['usuario']:
            raise ValueError('Identidade inválida.')
        if identidade.papel == PapelAcesso.CLIENTE:
            if str(UUID(identidade.cliente_id)) != identidade.cliente_id:
                raise ValueError('Vínculo inválido.')
        elif identidade.cliente_id is not None:
            raise ValueError('Conta de Gestão com vínculo pessoal.')
        protegido = registro['senha_hash']
        if not re.fullmatch(r'scrypt:32768:8:1\$[A-Za-z0-9]{16}\$[a-f0-9]{128}', protegido):
            raise ValueError('Registro de senha inválido.')
        if 'nome_pendente' in registro:
            nome = registro['nome_pendente']
            if (identidade.papel != PapelAcesso.CLIENTE or identidade.usuario in USUARIOS_DEMO
                    or not isinstance(nome, str) or not nome.strip() or len(nome) > 120):
                raise ValueError('Reserva de cadastro pessoal inválida.')
        return cls(identidade, protegido, registro.get('nome_pendente'))

    def registro(self):
        dados = {**asdict(self.identidade), 'senha_hash': self.senha_hash}
        if self.nome_pendente is not None:
            dados['nome_pendente'] = self.nome_pendente
        return dados


class ContaRepository:
    def __init__(self, caminho):
        self.caminho = Path(caminho)

    def _ler(self):
        try:
            registros, anterior = historico_json.ler(self.caminho)
            if not isinstance(registros, list):
                raise ValueError('Coleção inválida.')
            contas = [ContaUsuario.do_registro(r) for r in registros]
            ids = [c.identidade for c in contas]
            for chaves in ([i.id for i in ids], [i.usuario for i in ids],
                           [i.cliente_id for i in ids if i.cliente_id]):
                if len(set(chaves)) != len(chaves):
                    raise ValueError('Identidades duplicadas.')
            return contas, anterior
        except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError) as erro:
            raise ErroDeInfraestrutura('Armazenamento de contas indisponível.') from erro

    def por_id(self, identificador):
        return next((c.identidade for c in self._ler()[0]
                     if c.identidade.id == identificador and c.nome_pendente is None), None)

    def por_usuario(self, usuario):
        return next((c for c in self._ler()[0] if c.identidade.usuario == usuario), None)

    def tem_gestor(self):
        return any(conta.identidade.papel == PapelAcesso.GESTAO for conta in self._ler()[0])

    def adicionar(self, conta):
        try:
            with trava_de_arquivo(str(self.caminho) + '.lock', esperar=True):
                contas, anterior = self._ler()
                for existente in contas:
                    i = existente.identidade
                    if i.usuario == conta.identidade.usuario:
                        raise ValueError('Nome de usuário já utilizado.')
                    if i.cliente_id and i.cliente_id == conta.identidade.cliente_id:
                        raise ValueError('Este cliente já possui uma conta.')
                registros = [c.registro() for c in contas] + [conta.registro()]
                historico_json.salvar(self.caminho, registros, anterior)
        except OSError as erro:
            raise ErroDeInfraestrutura('Falha ao persistir a conta. Consulte o cadastro.') from erro

    def ativar(self, reserva):
        """Publica a conta apenas depois de o histórico confirmar o UUID reservado."""
        ativa = replace(reserva, nome_pendente=None)
        try:
            with trava_de_arquivo(str(self.caminho) + '.lock', esperar=True):
                contas, anterior = self._ler()
                for indice, conta in enumerate(contas):
                    if conta == ativa:
                        return
                    if conta == reserva:
                        contas[indice] = ativa
                        historico_json.salvar(self.caminho, [c.registro() for c in contas], anterior)
                        return
                raise ErroDeInfraestrutura('A reserva de cadastro mudou durante a confirmação.')
        except OSError as erro:
            raise ErroDeInfraestrutura('Não foi possível confirmar a ativação da conta.') from erro


class AutenticacaoService:
    def __init__(self, contas, estacionamento, *, demonstracao=False):
        self.contas = contas
        self._estacionamento = estacionamento
        self._demonstracao = demonstracao
        self._hash_auxiliar = generate_password_hash(uuid4().hex, method='scrypt:32768:8:1')

    def _permitida(self, usuario, papel):
        return usuario != MASTER_DEMO or (self._demonstracao and papel == PapelAcesso.GESTAO)

    def contexto(self, conta_id, vinculos, *, titular_demo=None):
        principal = self.contas.por_id(conta_id)
        if principal is None or not self._permitida(principal.usuario, principal.papel):
            return None
        pessoal = None
        if principal.papel == PapelAcesso.GESTAO and conta_id in vinculos:
            candidata = self.contas.por_id(vinculos[conta_id])
            if (candidata and candidata.papel == PapelAcesso.CLIENTE and candidata.cliente_id
                    and candidata.usuario != MASTER_DEMO):
                pessoal = candidata
        if principal.usuario == MASTER_DEMO:
            if pessoal is None or pessoal.usuario != 'cliente.demo' or pessoal.cliente_id != titular_demo:
                return None
        return ContextoAcesso(principal, pessoal)

    def provisionar(self, usuario, senha, papel, cliente_id=None):
        usuario = normalizar_usuario(usuario)
        papel = PapelAcesso(papel)
        if not self._permitida(usuario, papel):
            raise ValueError('master.demo é uma conta de Gestão reservada à demonstração isolada.')
        if papel == PapelAcesso.CLIENTE:
            cliente_id = self._estacionamento.buscar_cliente(cliente_id)['identificador']
        elif cliente_id is not None:
            raise ValueError('A conta de Gestão não recebe um cliente.')
        identidade = Identidade(str(uuid4()), usuario, papel, cliente_id)
        self.contas.adicionar(ContaUsuario.criar(identidade, senha))
        return identidade

    def cadastrar_pessoal(self, nome, usuario, senha, confirmacao):
        usuario = normalizar_usuario(usuario)
        if usuario in USUARIOS_DEMO:
            raise ValueError('Esse nome de usuário está reservado. Escolha outro.')
        if not isinstance(nome, str) or len(nome) > 120:
            raise ValueError('Informe um nome de até 120 caracteres.')
        if senha != confirmacao:
            raise ValueError('A confirmação deve ser igual à senha.')
        cliente = ClienteComum(nome)
        identidade = Identidade(str(uuid4()), usuario, PapelAcesso.CLIENTE, cliente.identificador)
        reserva = ContaUsuario.criar(identidade, senha, nome_pendente=cliente.nome)
        self.contas.adicionar(reserva)
        self._concluir_cadastro(reserva)
        return identidade

    def _concluir_cadastro(self, reserva):
        cliente = ClienteComum(reserva.nome_pendente, identificador=reserva.identidade.cliente_id)
        self._estacionamento.confirmar_cadastro_pessoal(cliente)
        self.contas.ativar(reserva)

    def autenticar(self, usuario, senha):
        try:
            nome = normalizar_usuario(usuario)
        except ValueError:
            nome = ''
        conta = self.contas.por_usuario(nome)
        if not isinstance(senha, str) or len(senha) > 256:
            return None
        valido = check_password_hash(conta.senha_hash if conta else self._hash_auxiliar, senha)
        if conta and valido and self._permitida(nome, conta.identidade.papel):
            if conta.nome_pendente is not None:
                self._concluir_cadastro(conta)
            return conta.identidade
        return None
