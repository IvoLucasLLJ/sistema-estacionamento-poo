"""Instalação atômica de um cenário fictício, separado da operação do estacionamento."""
import json
from getpass import GetPassWarning
import os
import stat
import sys
import tempfile
import unicodedata
import warnings
from pathlib import Path
from uuid import UUID

from persistence import privacidade
from persistence.caminhos import RAIZ_MOVE, caminho_local, historico_local
from persistence.exclusividade import EscritorLocal
from service.estacionamento_service import EstacionamentoService
from web import create_app
from web.contas import MASTER_DEMO


def configuracao(pasta):
    return dict(DEMONSTRACAO=True, DADOS=pasta, HISTORICO=pasta / 'historico.json', CONTAS=pasta / 'contas.json',
                SECRET_KEY=None, SESSION_COOKIE_SECURE=False, SESSION_COOKIE_NAME='move_demo_session')


def criar_cenario(servico):
    lia = servico.cadastrar_cliente('vip', 'Lia Vale')['identificador']
    caio = servico.cadastrar_cliente('comum', 'Caio Reis')['identificador']
    noa = servico.cadastrar_cliente('mensalista', 'Noa Reis')['identificador']
    servico.cadastrar_cliente('comum', 'Iara Luz')
    for tipo, placa, modelo, titular in (
            ('carro', 'AV1', 'Atlas', lia), ('moto', 'AM2', 'Brisa', lia),
            ('caminhao', 'CB3', 'Serra', caio), ('moto', 'NM4', 'Lua', noa)):
        servico.cadastrar_veiculo(tipo, placa, modelo)
        servico.vincular_veiculo(placa, titular)
    for placa, vaga, titular in [('CB3', 8, caio), ('NM4', 1, noa)]:
        servico.iniciar_estadia(placa, vaga, titular)
        cotacao = servico.consultar_cobranca(placa, '2')
        if cotacao['valor_centavos']:
            servico.confirmar_pagamento(placa, '2', cotacao, confirmado=True)
        servico.concluir_saida(placa, '2', cotacao)
    for placa, vaga, titular in [('AV1', 2, lia), ('AM2', 5, lia), ('NM4', 1, noa)]:
        servico.iniciar_estadia(placa, vaga, titular)
    return lia


def verificar_separacao(pasta):
    dados = caminho_local(os.environ.get('MOVE_DADOS', 'instance'))
    contas = caminho_local(os.environ.get('MOVE_CONTAS') or dados / 'contas.json')
    # APFS pode tratar caixa e grafias Unicode equivalentes como o mesmo nome.
    def identidade(caminho):
        return Path(unicodedata.normalize('NFC', str(caminho.resolve())).casefold())
    if _redireciona(pasta) or any(identidade(p).is_relative_to(identidade(pasta))
                                for p in (historico_local(), dados / 'sessao.key', dados / 'sessoes.json', dados / 'sessoes.json.lock', contas)):
        raise ValueError('A demonstração coincide com um caminho operacional. Confira as variáveis MOVE e a pasta de demonstração.')


def _redireciona(caminho):
    if caminho.is_symlink():
        return True
    if os.name == 'nt' and os.path.lexists(caminho):
        return bool(caminho.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    return False


def preparar_demonstracao():
    pasta = RAIZ_MOVE / '.move-demonstracao'
    verificar_separacao(pasta)
    reserva = EscritorLocal(RAIZ_MOVE / '.move-cenario')
    reserva.abrir()
    try:
        if not pasta.exists():
            with tempfile.TemporaryDirectory(dir=RAIZ_MOVE, prefix='.move-cenario-') as nome:
                # Publicar o subdiretório completo permite remover o temporário mesmo após o rename.
                pronto = Path(nome) / 'pronto'
                privacidade.criar_pasta_privada(pronto)
                app = create_app(configuracao(pronto))
                lia = criar_cenario(app.extensions['estacionamento'])
                with (pronto / 'contas.json').open('x', encoding='utf-8') as arquivo:
                    arquivo.write('[]')
                (pronto / 'cenario.json').write_text(json.dumps(dict(versao=1, titular=lia)), encoding='utf-8')
                pronto.rename(pasta)
        if os.name == 'nt':
            privacidade.conferir_acl(pasta)
        elif pasta.stat().st_mode & 0o077 or pasta.stat().st_uid != os.getuid():
            raise PermissionError(f'Confira o proprietário e as permissões de {pasta}.')
        if not pasta.is_dir():
            raise ValueError(f'Pasta de demonstração inválida. Confira o proprietário e as permissões de {pasta}.')
        for nome in ('cenario.json', 'historico.json', 'contas.json', 'sessao.key', 'historico.json.lock', 'contas.json.lock', 'sessao.key.lock',
                     'sessoes.json', 'sessoes.json.lock'):
            arquivo = pasta / nome
            if (nome.endswith('.lock') or nome == 'sessoes.json') and not os.path.lexists(arquivo):
                continue
            modo = arquivo.lstat()
            if not stat.S_ISREG(modo.st_mode) or _redireciona(arquivo) or modo.st_nlink != 1:
                raise ValueError(f'Arquivo de demonstração inválido: {nome}. A pasta foi preservada.')
            if os.name == 'nt':
                privacidade.conferir_acl(arquivo)
            elif modo.st_uid != os.getuid():
                raise ValueError(f'Arquivo de demonstração inválido: {nome}. A pasta foi preservada.')
        info = json.loads((pasta / 'cenario.json').read_bytes())
        if not isinstance(info, dict) or info.get('versao') != 1 or not isinstance(info.get('titular'), str):
            raise ValueError('Identificação do cenário inválida. A pasta foi preservada.')
        return configuracao(pasta), str(UUID(info['titular']))
    finally:
        reserva.fechar()


def provisionar_demonstracao(app, titular):
    if not app.config['DEMONSTRACAO']:
        raise ValueError('O provisionamento demonstrativo exige o ambiente isolado.')
    app.extensions['estacionamento'].buscar_cliente(titular)
    contas = app.extensions['autenticacao'].contas
    for usuario, papel, cliente_id in [('gestao.demo', 'gestao', None), ('cliente.demo', 'cliente', titular),
                                       (MASTER_DEMO, 'gestao', None)]:
        conta = contas.por_usuario(usuario)
        if conta is not None:
            if conta.identidade.papel != papel or conta.identidade.cliente_id != cliente_id:
                raise ValueError(f'A conta {usuario} tem outro vínculo. O cadastro foi preservado.')
            continue
        if not sys.stdin.isatty():
            raise ValueError(f'A conta {usuario} aguarda provisionamento. Abra o inicializador em um terminal interativo.')
        print(f'Crie uma senha exclusiva de 12 a 256 caracteres para {usuario}. A digitação fica oculta.', flush=True)
        argumentos = ['criar-conta', '--usuario', usuario, '--papel', papel]
        if cliente_id:
            argumentos.extend(['--cliente-id', cliente_id])
        with app.app_context(), warnings.catch_warnings():
            warnings.simplefilter('error', GetPassWarning)
            try:
                app.cli.main(args=argumentos, standalone_mode=False)
            except GetPassWarning as erro:
                raise ValueError('Este terminal não consegue ocultar a senha. Use um terminal interativo.') from erro
    gestor = contas.por_usuario('gestao.demo').identidade
    master = contas.por_usuario(MASTER_DEMO).identidade
    pessoal = contas.por_usuario('cliente.demo').identidade
    app.config['TITULAR_DEMO'] = titular
    app.config['VINCULOS_PORTAIS'] = {gestor.id: pessoal.id, master.id: pessoal.id}
