"""Regras do inicializador Android exercitáveis com adaptadores controlados."""
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

import iniciar_move
from persistence import ambiente_termux
from web.__main__ import abrir_navegador
from web.config import chave_persistida


class TermuxTests(TestCase):
    def setUp(self):
        self.pasta = Path(self.enterContext(TemporaryDirectory())).resolve()
        self.prefixo = self.pasta / 'files/usr'
        self.raiz = self.pasta / 'files/home/MOVE acadêmico'
        self.prefixo.mkdir(parents=True)
        self.raiz.mkdir(parents=True)

    def test_aceita_android_15_16_e_rejeita_sdk_anterior_invalido_ou_sem_termux(self):
        with patch.object(ambiente_termux, 'prefixo_termux', return_value=None):
            with self.assertRaisesRegex(ValueError, 'nativo'):
                ambiente_termux.conferir_android(self.raiz)
        with patch.object(ambiente_termux, 'prefixo_termux', return_value=self.prefixo):
            for nivel in ('35', '36', '37', '34', '', 'indefinido'):
                with self.subTest(nivel=nivel), patch('subprocess.check_output', return_value=nivel):
                    if nivel in ('35', '36', '37'):
                        ambiente_termux.conferir_android(self.raiz)
                    else:
                        with self.assertRaisesRegex(ValueError, 'API 35'):
                            ambiente_termux.conferir_android(self.raiz)

    def test_caminho_compartilhado_nao_recebe_dados_ou_venv(self):
        externo = self.pasta / 'armazenamento compartilhado'
        externo.mkdir()
        with patch.object(ambiente_termux, 'prefixo_termux', return_value=self.prefixo):
            self.assertEqual(ambiente_termux.caminho_interno(self.raiz), self.raiz)
            with self.assertRaisesRegex(ValueError, 'armazenamento interno'):
                ambiente_termux.caminho_interno(externo)
            if os.name == 'posix':
                (self.raiz / '.venv').symlink_to(externo, target_is_directory=True)
                with patch('subprocess.check_output', return_value='35'), self.assertRaisesRegex(ValueError, 'interno'):
                    ambiente_termux.conferir_android(self.raiz)
        self.assertEqual(list(externo.iterdir()), [])

    def test_chave_atomica_reabre_sem_link_fisico_e_preserva_falha(self):
        chave = self.raiz / 'sessao.key'
        with patch.object(os, 'link', side_effect=AssertionError('link indisponível'), create=True):
            with patch('os.fsync', side_effect=OSError('disco')), self.assertRaises(OSError):
                chave_persistida(chave)
            self.assertFalse(chave.exists())
            self.assertEqual(list(self.raiz.glob('*.tmp')), [])
            primeira = chave_persistida(chave)
            self.assertEqual(len(primeira), 32)
            self.assertEqual(chave_persistida(chave), primeira)

    def test_abridor_do_android_e_endereco_manual_sem_aplicativo_auxiliar(self):
        url = 'http://127.0.0.1:5001/entrar'
        with patch('web.__main__.prefixo_termux', return_value=self.prefixo), patch('subprocess.run') as abrir:
            with patch('builtins.print') as mensagem:
                abrir_navegador(url)
                mensagem.assert_called_once()
            abrir.assert_not_called()
            abridor = self.prefixo / 'bin/termux-open-url'
            abridor.parent.mkdir()
            abridor.touch()
            abrir.return_value.returncode = 0
            abrir_navegador(url)
            abrir.assert_called_once_with([str(abridor), url], check=False)

    def test_preparo_termux_seleciona_fonte_nativa_e_reuso_dispensa_instalacao(self):
        # A simulação só inspeciona a escolha de pacotes. A ABI é testada no aparelho.
        requisitos = self.raiz / 'requirements.txt'
        requisitos.write_text('MarkupSafe==3.0.4\n', encoding='utf-8')
        with patch.object(iniciar_move, 'AMBIENTE', Path(sys.prefix).resolve()), \
                patch.object(iniciar_move, 'RAIZ', self.raiz), \
                patch.object(iniciar_move, 'prefixo_termux', return_value=self.prefixo), \
                patch('subprocess.run', return_value=subprocess.CompletedProcess([], 0)) as pip:
            for instalada in ('3.0.3', '3.0.4'):
                pip.reset_mock()
                with patch('importlib.metadata.version', return_value=instalada):
                    iniciar_move.conferir_pacotes()
                instalacoes = [chamada.args[0] for chamada in pip.call_args_list if 'install' in chamada.args[0]]
                self.assertEqual(len(instalacoes), int(instalada != '3.0.4'))
                if instalacoes:
                    self.assertIn('--no-binary=MarkupSafe', instalacoes[0])
