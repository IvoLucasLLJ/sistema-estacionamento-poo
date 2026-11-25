"""Prepara a venv local com a biblioteca padrão e entrega o terminal ao servidor."""
import os
import subprocess
import stat
import sys
from importlib import metadata
from pathlib import Path


RAIZ = Path(__file__).resolve().parent
AMBIENTE = RAIZ / '.venv'
PYTHON = AMBIENTE / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
# Os inicializadores usam -I. Somente a raiz desta instalação fornece módulos locais.
sys.path.insert(0, str(RAIZ))
from persistence.ambiente_termux import conferir_android, prefixo_termux
from persistence.exclusividade import HistoricoEmUso, trava_de_arquivo
RECUPERAR = ('A .venv não é utilizável nesta instalação. Com o MOVE encerrado, '
             'renomeie a pasta .venv para preservá-la e abra o inicializador novamente.')


def verificar_python():
    if (sys.platform not in ('linux', 'darwin', 'win32') and not prefixo_termux()) or not (3, 11) <= sys.version_info[:2] <= (3, 14):
        raise ValueError('Utilize Python 3.14 ou 3.12 nativo em Linux, macOS, Windows ou Termux. 3.11 e 3.13 têm avaliação apenas estática.')
    if sys.platform == 'darwin':
        traducao = subprocess.run(['/usr/sbin/sysctl', '-in', 'sysctl.proc_translated'],
                                  capture_output=True, text=True)
        if traducao.stdout.strip() == '1':
            raise ValueError('Este Python está sob Rosetta. Abra o MOVE com um Python nativo do Apple Silicon.')
    try:
        import venv
        from hashlib import scrypt
        if prefixo_termux():
            scrypt(b'MOVE', salt=b'verificacao', n=16, r=1, p=1, dklen=16)
    except ImportError as erro:
        raise ValueError(f'Falta um recurso de Python ({erro.name}). Use uma instalação com venv, scrypt e suporte a travas nativas.') from erro


def conferir_pacotes():
    if Path(sys.prefix).resolve() != AMBIENTE or sys.prefix == sys.base_prefix:
        raise ValueError(RECUPERAR)
    try:
        import pip
    except ImportError as erro:
        raise ValueError('Falta pip na .venv. ' + RECUPERAR) from erro
    if not Path(pip.__file__).resolve().is_relative_to(AMBIENTE):
        raise ValueError(RECUPERAR)
    if sys.version_info[:2] in ((3, 11), (3, 13)):
        print('Esta versão do Python recebeu apenas avaliação estática. As versões testadas são 3.12.3 e 3.14.4.')

    requisitos = RAIZ / 'requirements.txt'
    faltantes = []
    for linha in requisitos.read_text(encoding='utf-8').splitlines():
        pin, separador, marcador = linha.partition(';')
        if separador:
            if marcador.strip() != 'sys_platform == "win32"':
                raise ValueError('Marcador de plataforma desconhecido em requirements.txt.')
            if sys.platform != 'win32':
                continue
        nome, exigida = pin.strip().split('==')
        try:
            if metadata.version(nome) == exigida:
                continue
        except metadata.PackageNotFoundError:
            pass
        faltantes.append(linha)
    # Evita que opções de usuário desviem a instalação para fora da venv.
    env = {k: v for k, v in os.environ.items() if not k.startswith('PIP_')}
    for opcao in ('PIP_NO_INDEX', 'PIP_FIND_LINKS', 'PIP_INDEX_URL', 'PIP_CERT'):
        if opcao in os.environ:
            env[opcao] = os.environ[opcao]
    env.update(PIP_CONFIG_FILE=os.devnull, PIP_DISABLE_PIP_VERSION_CHECK='1', PIP_REQUIRE_VIRTUALENV='1')
    comando = [sys.executable, '-IB', '-m', 'pip']
    if faltantes:
        print('Instalando as dependências fixadas do MOVE…', flush=True)
        # O Python do Termux é vinculado à Bionic. Compile a distribuição fonte com o seu ABI.
        fonte_nativa = ['--no-binary=MarkupSafe'] if prefixo_termux() else []
        if subprocess.run([*comando, 'install', *fonte_nativa, '-r', str(requisitos)], env=env).returncode:
            raise ValueError('A instalação falhou. Confira a conexão ou a fonte dos pacotes e tente novamente.')
    if subprocess.run([*comando, 'check'], env=env).returncode:
        raise ValueError('Há dependências incompatíveis. ' + RECUPERAR)
    try:
        import flask
        import werkzeug.security
        if os.name == 'nt':
            import win32security
        # Uma venv copiada pode ter metadados corretos e o binário de outra arquitetura.
        arquivos = metadata.files('MarkupSafe') or ()
        if any(p.name.startswith('_speedups.') and p.suffix in ('.so', '.pyd') for p in arquivos):
            import markupsafe._speedups
    except (ImportError, OSError) as erro:
        raise ValueError('Os pacotes estão incompletos ou incompatíveis com este Python. ' + RECUPERAR) from erro


def preparar():
    with trava_de_arquivo(RAIZ / '.move-preparo.lock'):
        if not AMBIENTE.exists() and not AMBIENTE.is_symlink():
            print('Criando o ambiente virtual do MOVE…', flush=True)
            if subprocess.run([sys.executable, '-IB', '-m', 'venv', str(AMBIENTE)]).returncode:
                raise ValueError('Falha ao criar a .venv. Verifique venv, ensurepip e a permissão da pasta. ' + RECUPERAR)
        cfg = AMBIENTE / 'pyvenv.cfg'
        if (AMBIENTE.is_symlink() or (os.name == 'nt' and AMBIENTE.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
                or not cfg.is_file() or not PYTHON.is_file()):
            raise ValueError(RECUPERAR)
        dados = dict(linha.split(' = ', 1) for linha in cfg.read_text(encoding='utf-8').splitlines() if ' = ' in linha)
        if dados.get('include-system-site-packages', '').lower() != 'false':
            raise ValueError(RECUPERAR)
        if 'command' in dados and not os.path.normcase(dados['command']).endswith(' ' + os.path.normcase(AMBIENTE)):
            raise ValueError(RECUPERAR)
        try:
            resultado = subprocess.run([str(PYTHON), '-IB', __file__, '--conferir-venv'])
        except OSError as erro:
            raise ValueError(RECUPERAR) from erro
        if resultado.returncode:
            raise SystemExit(resultado.returncode)


def main():
    if sys.argv[1:2] == ['--termux']:
        del sys.argv[1]
        conferir_android(RAIZ)
    elif prefixo_termux():
        conferir_android(RAIZ)
    verificar_python()
    if sys.argv[1:] == ['--conferir-venv']:
        conferir_pacotes()
        return
    os.chdir(RAIZ)
    preparar()
    # O servidor substitui o preparador e recebe Ctrl+C diretamente.
    ambiente = os.environ.copy()
    for chave in ('PYTHONPATH', 'PYTHONHOME', 'FLASK_DEBUG', 'WERKZEUG_RUN_MAIN', 'WERKZEUG_SERVER_FD'):
        ambiente.pop(chave, None)
    comando = [str(PYTHON), '-B', '-m', 'web', '--demonstracao', *sys.argv[1:]]
    if os.name == 'nt':
        # O console distribui Ctrl+C aos dois processos. O filho encerra o Flask e libera a trava.
        with subprocess.Popen(comando, env=ambiente) as processo:
            while True:
                try:
                    raise SystemExit(processo.wait())
                except KeyboardInterrupt:
                    continue
    os.execve(PYTHON, comando, ambiente)


if __name__ == '__main__':
    try:
        main()
    except HistoricoEmUso:
        sys.exit('Outra preparação do MOVE está em andamento. Aguarde o término.')
    except (OSError, ValueError, subprocess.CalledProcessError) as erro:
        sys.exit(f'Preparação interrompida. {erro}')
    except KeyboardInterrupt:
        sys.exit('Preparação interrompida pelo usuário.')
