"""Reconhece o Python nativo do Termux e a área privada deste aplicativo Android."""
import os
import subprocess
import sys
from pathlib import Path


GETPROP = Path('/system/bin/getprop')


def prefixo_termux():
    if os.name != 'posix' or not GETPROP.is_file():
        return None
    base = Path(sys.base_prefix).resolve()
    if base.parts[-3:] == ('com.termux', 'files', 'usr') and base.parts[:2] == ('/', 'data'):
        return base
    return None


def caminho_interno(caminho):
    prefixo = prefixo_termux()
    if prefixo and not Path(caminho).resolve().is_relative_to(prefixo.parent):
        raise ValueError('Mantenha projeto, venv, dados e travas no armazenamento interno do Termux, por exemplo em $HOME/MOVE.')
    return caminho


def conferir_android(raiz):
    prefixo = prefixo_termux()
    if prefixo is None:
        raise ValueError('Use o Python nativo do Termux no Android 15 ou superior.')
    sdk = subprocess.check_output([str(GETPROP), 'ro.build.version.sdk'], text=True).strip()
    if not sdk.isascii() or not sdk.isdecimal() or int(sdk) < 35:
        raise ValueError('O MOVE requer Android 15 ou superior (API 35+).')
    caminho_interno(raiz)
    caminho_interno(raiz / '.venv')
