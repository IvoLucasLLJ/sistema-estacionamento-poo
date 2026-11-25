"""Publicação de arquivos privados respeitando modo POSIX ou DACL do Windows."""
import os
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile


if os.name == 'nt':
    import ctypes
    import msvcrt
    from ctypes import wintypes
    from uuid import uuid4

    import pywintypes
    import win32api
    import win32con
    import win32file
    import win32security as seguranca

    class _FileRenameInfo(ctypes.Structure):
        _fields_ = [('Flags', wintypes.DWORD), ('RootDirectory', wintypes.HANDLE),
                    ('FileNameLength', wintypes.DWORD), ('FileName', wintypes.WCHAR * 1)]

    def _substituir_com_leitores(origem, destino):
        # FileRenameInfoEx permite que handles já abertos continuem lendo a versão anterior.
        nome = os.path.abspath(destino).encode('utf-16-le')
        tamanho = max(ctypes.sizeof(_FileRenameInfo), _FileRenameInfo.FileName.offset + len(nome))
        buffer = ctypes.create_string_buffer(tamanho)
        info = _FileRenameInfo.from_buffer(buffer)
        info.Flags = 0x1 | 0x2  # REPLACE_IF_EXISTS | POSIX_SEMANTICS
        info.FileNameLength = len(nome)
        ctypes.memmove(ctypes.addressof(buffer) + _FileRenameInfo.FileName.offset, nome, len(nome))
        renomear = ctypes.WinDLL('kernel32', use_last_error=True).SetFileInformationByHandle
        renomear.argtypes = (wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD)
        renomear.restype = wintypes.BOOL
        handle = win32file.CreateFile(str(origem), win32con.DELETE, 0, None,
                                      win32con.OPEN_EXISTING, win32con.FILE_ATTRIBUTE_NORMAL, None)
        try:
            if not renomear(int(handle), 22, buffer, tamanho):  # FileRenameInfoEx
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            handle.Close()

    def _fluxo(handle, escrita):
        flags = os.O_WRONLY if escrita else os.O_RDONLY
        fd = msvcrt.open_osfhandle(int(handle), flags | os.O_BINARY)
        handle.Detach()  # O descritor da CRT passa a ser o único dono do handle.
        return os.fdopen(fd, 'wb' if escrita else 'rb')

    def _sid_atual():
        token = seguranca.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_QUERY)
        try:
            return seguranca.GetTokenInformation(token, seguranca.TokenUser)[0]
        finally:
            token.Close()

    def _atributos_privados():
        # DACL protegida desde a criação, inclusive para os arquivos filhos.
        sid = seguranca.ConvertSidToStringSid(_sid_atual())
        sddl = f'D:P(A;OICI;FA;;;{sid})(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)'
        atributos = pywintypes.SECURITY_ATTRIBUTES()
        atributos.SECURITY_DESCRIPTOR = seguranca.ConvertStringSecurityDescriptorToSecurityDescriptor(sddl, 1)
        return atributos

    def conferir_acl(caminho):
        try:
            sd = seguranca.GetNamedSecurityInfo(str(caminho), seguranca.SE_FILE_OBJECT,
                                                seguranca.OWNER_SECURITY_INFORMATION | seguranca.DACL_SECURITY_INFORMATION)
            permitidos = {seguranca.ConvertSidToStringSid(_sid_atual()), 'S-1-5-32-544', 'S-1-5-18'}
            dono = seguranca.ConvertSidToStringSid(sd.GetSecurityDescriptorOwner())
            acl = sd.GetSecurityDescriptorDacl()
            if dono in permitidos and acl is not None:
                for indice in range(acl.GetAceCount()):
                    cabecalho, _, *dados = acl.GetAce(indice)
                    if cabecalho[0] == seguranca.ACCESS_DENIED_ACE_TYPE:
                        continue
                    if cabecalho[0] != seguranca.ACCESS_ALLOWED_ACE_TYPE:
                        break
                    sid = seguranca.ConvertSidToStringSid(dados[-1])
                    # OWNER RIGHTS restringe-se ao dono já conferido.
                    if sid not in permitidos and sid != 'S-1-3-4':
                        break
                else:
                    return
        except pywintypes.error as erro:
            raise OSError(f'Não foi possível verificar as permissões de {caminho}.') from erro
        raise PermissionError(f'Use uma pasta privada NTFS do seu usuário. Confira as permissões de {caminho}.')


def criar_pasta_privada(pasta):
    if os.name != 'nt':
        pasta.mkdir(mode=0o700, parents=True, exist_ok=True)
        return
    pasta.parent.mkdir(parents=True, exist_ok=True)
    try:
        win32file.CreateDirectory(str(pasta), _atributos_privados())
    except pywintypes.error as erro:
        if erro.winerror != 183:  # ERROR_ALREADY_EXISTS
            raise OSError(f'Não foi possível criar a pasta privada {pasta}.') from erro
    conferir_acl(pasta)


@contextmanager
def temporario_privado(destino):
    """Entrega caminho e arquivo abertos. Quem publica decide quando remover o temporário."""
    if os.name != 'nt':
        with NamedTemporaryFile(mode='wb', dir=destino.parent, prefix=destino.name + '.',
                                suffix='.tmp', delete=False) as saida:
            yield Path(saida.name), saida
        return
    caminho = destino.with_name(f'{destino.name}.{uuid4().hex}.tmp')
    try:
        handle = win32file.CreateFile(str(caminho), win32con.GENERIC_WRITE, 0, _atributos_privados(),
                                      win32con.CREATE_NEW, win32con.FILE_ATTRIBUTE_NORMAL, None)
    except pywintypes.error as erro:
        raise OSError(f'Não foi possível criar um arquivo privado em {destino.parent}.') from erro
    with _fluxo(handle, escrita=True) as saida:
        yield caminho, saida


def substituir_arquivo(origem, destino):
    try:
        os.replace(origem, destino)
    except PermissionError as erro:
        if os.name != 'nt' or getattr(erro, 'winerror', None) != 5:
            raise
        _substituir_com_leitores(origem, destino)


def abrir_leitura(caminho):
    if os.name != 'nt':
        return caminho.open('rb')
    # Um leitor mantém sua versão aberta e permite o replace atômico por outro processo.
    compartilhar = win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE
    try:
        handle = win32file.CreateFile(str(caminho), win32con.GENERIC_READ, compartilhar, None,
                                      win32con.OPEN_EXISTING, win32con.FILE_ATTRIBUTE_NORMAL, None)
    except pywintypes.error as erro:
        if erro.winerror in (2, 3):
            raise FileNotFoundError(str(caminho)) from erro
        raise OSError(f'Falha na leitura de {caminho}.') from erro
    return _fluxo(handle, escrita=False)
