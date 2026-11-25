"""Identidade de acesso local, independente das categorias comerciais."""
import re
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from uuid import UUID, uuid4

from werkzeug.security import check_password_hash, generate_password_hash

from persistence import historico_json
from persistence.exclusividade import trava_de_arquivo
from service.estacionamento_service import ErroDeInfraestrutura


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
class ContaUsuario:
    identidade: Identidade
    senha_hash: str = field(repr=False)

    @classmethod
    def do_registro(cls, registro):
        if not isinstance(registro, dict) or registro.keys() != {'id', 'usuario', 'papel', 'cliente_id', 'senha_hash'}:
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
        return cls(identidade, protegido)

    def registro(self):
        return {**asdict(self.identidade), 'senha_hash': self.senha_hash}


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
        return next((c.identidade for c in self._ler()[0] if c.identidade.id == identificador), None)

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


class AutenticacaoService:
    def __init__(self, contas, estacionamento):
        self.contas = contas
        self._estacionamento = estacionamento
        self._hash_auxiliar = generate_password_hash(uuid4().hex, method='scrypt:32768:8:1')

    def provisionar(self, usuario, senha, papel, cliente_id=None):
        usuario = normalizar_usuario(usuario)
        papel = PapelAcesso(papel)
        if not isinstance(senha, str) or not 12 <= len(senha) <= 256:
            raise ValueError('Use uma senha de 12 a 256 caracteres.')
        if papel == PapelAcesso.CLIENTE:
            cliente_id = self._estacionamento.buscar_cliente(cliente_id)['identificador']
        elif cliente_id is not None:
            raise ValueError('A conta de Gestão não recebe um cliente.')
        identidade = Identidade(str(uuid4()), usuario, papel, cliente_id)
        self.contas.adicionar(ContaUsuario(identidade, generate_password_hash(senha, method='scrypt:32768:8:1')))
        return identidade

    def autenticar(self, usuario, senha):
        try:
            nome = normalizar_usuario(usuario)
        except ValueError:
            nome = ''
        conta = self.contas.por_usuario(nome)
        if not isinstance(senha, str) or len(senha) > 256:
            return None
        valido = check_password_hash(conta.senha_hash if conta else self._hash_auxiliar, senha)
        return conta.identidade if conta and valido else None
