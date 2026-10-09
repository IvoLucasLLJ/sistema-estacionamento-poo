import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from controller.controller import Controller
from model.carro import Carro
from model.moto import Moto
from model.caminhao import Caminhao
from model.veiculo import Veiculo
from view.ui_texto import menu


class NucleoTests(unittest.TestCase):
    def setUp(self):
        self.ctrl = Controller()
        self.est = self.ctrl.estacionamento

    def test_fluxo_completo_e_polimorfismo(self):
        for tipo, classe, vaga, tarifa in (
            ('carro', Carro, 1, 20),
            ('moto', Moto, 5, 10),
            ('caminhao', Caminhao, 10, 40),
        ):
            with self.subTest(tipo=tipo):
                self.ctrl.estacionar_veiculo(tipo, f'ABC{vaga:04}', 'Modelo', vaga)
                self.assertIsInstance(self.est.vagas[vaga - 1].veiculo, classe)
                self.assertIsInstance(self.est.vagas[vaga - 1].veiculo, Veiculo)
                self.assertEqual(self.ctrl.relatorio()['ocupadas'], 1)
                self.assertEqual(self.ctrl.retirar_veiculo(vaga, 2), tarifa)
                self.assertFalse(self.est.vagas[vaga - 1].ocupada)
                self.assertIsNone(self.est.vagas[vaga - 1].veiculo)
        self.assertEqual(self.ctrl.relatorio(), {
            'ocupadas': 0, 'livres': 10, 'faturamento': 70,
        })
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / 'historico.json'
            self.est.salvar_historico(arquivo)
            dados = json.loads(arquivo.read_text(encoding='utf-8'))
        self.assertEqual(dados, self.est.historico)
        self.assertEqual(len(dados), 6)
        for entrada, saida in zip(dados[::2], dados[1::2]):
            self.assertEqual(entrada['horario_entrada'], saida['horario_entrada'])
            self.assertGreaterEqual(saida['horario_saida'], entrada['horario_entrada'])
            self.assertEqual(entrada['tipo'], saida['tipo'])

    def test_vagas_invalidas_na_entrada_e_saida(self):
        for vaga in (0, -1, 11, 1.5, '1', None, True):
            with self.subTest(vaga=vaga):
                with self.assertRaises(ValueError):
                    self.ctrl.estacionar_veiculo('carro', 'ABC1234', 'Modelo', vaga)
                with self.assertRaises(ValueError):
                    self.ctrl.retirar_veiculo(vaga, 1)
        self.assertEqual(self.ctrl.relatorio()['ocupadas'], 0)
        self.assertEqual(self.est.historico, [])

    def test_duplicidade_ocupacao_e_reentrada(self):
        self.ctrl.estacionar_veiculo(' Carro ', ' abc-1234 ', 'Modelo', 1)
        with self.assertRaises(ValueError):
            self.ctrl.estacionar_veiculo('moto', 'ABC1234', 'Modelo', 2)
        with self.assertRaises(ValueError):
            self.ctrl.estacionar_veiculo('moto', 'DEF5678', 'Modelo', 1)
        self.assertEqual(self.ctrl.relatorio()['ocupadas'], 1)
        self.assertEqual(len(self.est.historico), 1)
        self.ctrl.retirar_veiculo(1, 1)
        self.ctrl.estacionar_veiculo('carro', 'ABC1234', 'Modelo', 2)
        self.assertEqual(self.ctrl.retirar_veiculo(2, 0.5), 5)
        self.assertEqual(self.est.historico[-1]['horario_entrada'],
                         self.est.historico[-2]['horario_entrada'])

    def test_horas_invalidas_preservam_ocupacao(self):
        self.ctrl.estacionar_veiculo('carro', 'ABC1234', 'Modelo', 1)
        for horas in (-1, float('nan'), float('inf'), 1e308, 'duas', None, True):
            with self.subTest(horas=horas), self.assertRaises(ValueError):
                self.ctrl.retirar_veiculo(1, horas)
            self.assertTrue(self.est.vagas[0].ocupada)
            self.assertEqual(len(self.est.historico), 1)
        self.assertEqual(self.ctrl.retirar_veiculo(1, 0), 0)
        with self.assertRaises(ValueError):
            self.ctrl.retirar_veiculo(1, 1)

    def test_dados_invalidos(self):
        for tipo, placa, modelo in (
            ('onibus', 'ABC1234', 'Modelo'), ('carro', ' ', 'Modelo'),
            ('carro', '---', 'Modelo'), ('carro', 'ABC1234', ' '),
        ):
            with self.subTest(tipo=tipo, placa=placa, modelo=modelo):
                with self.assertRaises(ValueError):
                    self.ctrl.estacionar_veiculo(tipo, placa, modelo, 1)
        self.assertEqual(self.est.historico, [])

    def test_menu_continua_apos_erros(self):
        respostas = [
            'invalida',
            '1', 'carro', 'ABC1234', 'Modelo', 'abc',
            '1', 'carro', 'ABC1234', 'Modelo', '10',
            '2', 'abc',
            '2', '10', 'abc',
            '2', '10', '-1',
            '2', '10', '1,5',
            '3', '4',
        ]
        saida = io.StringIO()
        with patch('builtins.input', side_effect=respostas), \
                patch('view.ui_texto.Controller', return_value=self.ctrl), \
                patch.object(self.ctrl, 'salvar') as salvar, redirect_stdout(saida):
            menu()
        salvar.assert_called_once_with()
        self.assertIn('Tarifa: R$ 15.00', saida.getvalue())
        self.assertIn('Vagas ocupadas: 0, Vagas livres: 10', saida.getvalue())
        self.assertEqual(self.ctrl.relatorio()['faturamento'], 15)

    def test_menu_permite_tentar_salvar_novamente(self):
        with patch('builtins.input', side_effect=['4', '4']), \
                patch.object(Controller, 'salvar', side_effect=[OSError('Falha'), None]) as salvar, \
                redirect_stdout(io.StringIO()) as saida:
            menu()
        self.assertEqual(salvar.call_count, 2)
        self.assertIn('Não foi possível salvar', saida.getvalue())

    def test_controller_salva_no_destino_padrao(self):
        with patch.object(self.ctrl.repository, 'salvar') as salvar:
            self.ctrl.salvar()
        salvar.assert_called_once_with(self.est)


if __name__ == '__main__':
    unittest.main()
