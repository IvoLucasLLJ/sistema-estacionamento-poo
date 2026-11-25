"""Regressões de execução fora da raiz e de identidade dos bytes do JSON."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from persistence import historico_json
from view.ui_texto import menu
from web import create_app


class PortabilidadeTests(TestCase):
    def test_configuracao_relativa_compartilhada_pelo_servidor_e_terminal(self):
        raiz = Path(self.enterContext(TemporaryDirectory())).resolve()
        dados = raiz / 'Dados privados'
        self.enterContext(patch('persistence.caminhos.RAIZ_MOVE', raiz))
        self.enterContext(patch.dict(os.environ, MOVE_DADOS='Dados privados',
                                     MOVE_CONTAS='Dados privados/contas.json',
                                     MOVE_HISTORICO='Dados privados/histórico.json'))
        app = create_app({'SECRET_KEY': None})
        self.assertEqual(app.config['DADOS'], dados)
        self.assertEqual(app.config['CONTAS'], dados / 'contas.json')
        self.assertEqual(app.config['HISTORICO'], dados / 'histórico.json')
        self.assertTrue((dados / 'sessao.key').is_file())
        with (patch('view.ui_texto.Controller') as construir,
              patch('builtins.input', return_value='4'), patch('builtins.print')):
            menu()
        construir.assert_called_once_with(app.config['HISTORICO'])

    def test_terminal_aberto_de_outra_pasta_reserva_e_usa_o_historico_da_copia(self):
        raiz = Path(self.enterContext(TemporaryDirectory()))
        copia = raiz / 'MOVE portátil'
        copia.mkdir()
        origem = Path(__file__).resolve().parents[1]
        shutil.copy2(origem / 'main.py', copia)
        for pasta in ('controller', 'model', 'persistence', 'repository', 'view'):
            shutil.copytree(origem / pasta, copia / pasta, ignore=shutil.ignore_patterns('__pycache__'))
        env = {k: v for k, v in os.environ.items() if k not in ('MOVE_HISTORICO', 'PYTHONPATH')}
        env['PYTHONIOENCODING'] = 'utf-8'

        def executar(entrada):
            return subprocess.run([sys.executable, '-B', str(copia / 'main.py')], cwd=raiz, env=env,
                                  input=entrada, capture_output=True, encoding='utf-8', timeout=10)

        primeiro = executar('5\ncarro\nA1\nIpê\n4\n')
        self.assertEqual(primeiro.returncode, 0, primeiro.stderr)
        arquivo = copia / 'historico.json'
        self.assertEqual(json.loads(arquivo.read_bytes())[0]['modelo'], 'Ipê')
        self.assertTrue((copia / 'historico.json.lock').exists())
        self.assertFalse((raiz / 'historico.json').exists())
        self.assertFalse((raiz / 'historico.json.lock').exists())
        original = arquivo.read_bytes()
        interrompido = executar('')
        self.assertNotEqual(interrompido.returncode, 0)
        self.assertIn('Terminal interrompido', interrompido.stderr)
        self.assertEqual(arquivo.read_bytes(), original)
        self.assertEqual(executar('4\n').returncode, 0)

    def test_bytes_confirmados_conferem_com_disco_em_duas_gravacoes(self):
        pasta = Path(self.enterContext(TemporaryDirectory()))
        arquivo = pasta / 'histórico Íris.json'
        registros = [{'nome': 'Íris 林'}]
        antigo = '[\r\n]'.encode('utf-8')
        arquivo.write_bytes(antigo)
        _, versao = historico_json.ler(arquivo)
        self.assertEqual(versao, antigo)
        gravado = historico_json.salvar(arquivo, registros, versao)
        self.assertEqual(gravado, arquivo.read_bytes())
        self.assertIn('Íris 林'.encode(), gravado)
        novo = historico_json.salvar(arquivo, registros * 2, gravado)
        self.assertEqual(historico_json.ler(arquivo), (registros * 2, novo))
