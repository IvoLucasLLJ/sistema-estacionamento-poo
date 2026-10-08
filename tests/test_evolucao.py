import unittest

from model.veiculo import Veiculo
from model.carro import Carro
from model.moto import Moto
from model.caminhao import Caminhao
from model.estacionamento import Estacionamento
from model.vaga import Vaga


class EvolucaoTests(unittest.TestCase):
    def test_contrato_e_encapsulamento(self):
        with self.assertRaises(TypeError):
            Veiculo('ABC1234', 'Modelo')
        for classe, valor in ((Carro, 20), (Moto, 10), (Caminhao, 40)):
            veiculo = classe(' abc-1234 ', ' Modelo ')
            self.assertEqual(veiculo.placa, 'ABC1234')
            self.assertEqual(veiculo.calcular_tarifa(2), valor)
            for atributo in ('placa', 'modelo'):
                with self.assertRaises(AttributeError):
                    setattr(veiculo, atributo, 'Outro')
        vaga = Vaga(1)
        for atributo in ('numero', 'ocupada', 'veiculo'):
            with self.assertRaises(AttributeError):
                setattr(vaga, atributo, None)
        with self.assertRaises(ValueError):
            vaga.ocupar(object())
        est = Estacionamento()
        est.estacionar(Carro('ABC1234', 'Modelo'), 1)
        copia = est.historico
        copia[0]['placa'] = 'OUTRA'
        self.assertEqual(est.historico[0]['placa'], 'ABC1234')
        self.assertIsInstance(est.vagas, tuple)

    def test_cadastro_busca_entrada_retirada(self):
        from controller.controller import Controller
        ctrl = Controller()
        veiculo = ctrl.cadastrar_veiculo(' Carro ', ' abc-1234 ', 'Modelo')
        self.assertIs(ctrl.buscar_veiculo('ABC-1234'), veiculo)
        with self.assertRaises(ValueError):
            ctrl.cadastrar_veiculo('moto', 'ABC1234', 'Outro')
        with self.assertRaises(ValueError):
            ctrl.estacionar_cadastrado('DEF1234', 1)
        ctrl.estacionar_cadastrado('abc1234', 1)
        with self.assertRaises(ValueError):
            ctrl.estacionar_cadastrado('ABC1234', 2)
        with self.assertRaises(ValueError):
            ctrl.retirar_por_placa('DEF1234', 1)
        self.assertEqual(ctrl.retirar_por_placa('ABC-1234', 2), 20)
        with self.assertRaises(ValueError):
            ctrl.retirar_por_placa('ABC1234', 1)
        self.assertEqual(ctrl.relatorio(), {'ocupadas': 0, 'livres': 10, 'faturamento': 20})
        ctrl.estacionar_cadastrado('ABC1234', 10)
        self.assertIs(ctrl.estacionamento.vagas[9].veiculo, veiculo)

    def test_vagas_comuns_aceitam_todos_os_tipos(self):
        est = Estacionamento()
        for classe in (Carro, Moto, Caminhao):
            veiculo = classe(classe.__name__, 'Modelo')
            est.cadastrar_veiculo(veiculo)
            est.estacionar_cadastrado(veiculo.placa, 1)
            est.retirar_por_placa(veiculo.placa, 1)
        est.estacionar_cadastrado('CARRO', 1)
        with self.assertRaises(ValueError):
            est.estacionar_cadastrado('MOTO', 1)
        for numero in (0, 11, True):
            with self.assertRaises(ValueError):
                est.estacionar_cadastrado('MOTO', numero)

    def test_persistencia_duas_sessoes_e_json_ausente(self):
        import tempfile
        from pathlib import Path
        from controller.controller import Controller
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / 'historico.json'
            ctrl = Controller(arquivo)
            self.assertEqual(ctrl.estacionamento.historico, [])
            ctrl.cadastrar_veiculo('carro', 'ABC1234', 'Modelo')
            ctrl.cadastrar_veiculo('moto', 'DEF1234', 'Moto')
            ctrl.estacionar_cadastrado('ABC1234', 1)
            ctrl.retirar_por_placa('ABC1234', 2)
            ctrl.estacionar_cadastrado('DEF1234', 10)
            ctrl.salvar()
            original = ctrl.estacionamento.historico
            novo = Controller(arquivo)
            self.assertEqual(novo.estacionamento.historico, original)
            self.assertEqual(novo.buscar_veiculo('ABC1234').modelo, 'Modelo')
            self.assertEqual(novo.relatorio(), {'ocupadas': 1, 'livres': 9, 'faturamento': 20})
            self.assertEqual(novo.retirar_por_placa('DEF1234', 1), 5)
            novo.salvar()
            terceiro = Controller(arquivo)
            self.assertEqual(terceiro.relatorio()['faturamento'], 25)
            self.assertEqual(len(terceiro.estacionamento.historico), len(original) + 1)

    def test_json_corrompido_ou_inconsistente_preservado(self):
        import tempfile
        from pathlib import Path
        from controller.controller import Controller
        for texto in ('{', '{}', '[{}]', '[NaN]', '[{"acao":"desconhecida"}]'):
            with self.subTest(texto=texto), tempfile.TemporaryDirectory() as pasta:
                arquivo = Path(pasta) / 'historico.json'
                arquivo.write_text(texto, encoding='utf-8')
                with self.assertRaises(ValueError):
                    Controller(arquivo)
                self.assertEqual(arquivo.read_text(encoding='utf-8'), texto)

    def test_falha_gravacao_preserva_arquivo(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from controller.controller import Controller
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / 'historico.json'
            arquivo.write_text('[]', encoding='utf-8')
            ctrl = Controller(arquivo)
            ctrl.cadastrar_veiculo('carro', 'ABC1234', 'Modelo')
            with patch('persistence.historico_json.os.replace', side_effect=OSError('Falha')):
                with self.assertRaises(OSError):
                    ctrl.salvar()
            self.assertEqual(arquivo.read_text(), '[]')
            self.assertEqual(list(Path(pasta).iterdir()), [arquivo])

    def test_json_da_versao_anterior(self):
        import json
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / 'historico.json'
            est = Estacionamento()
            est.estacionar(Carro('ABC1234', 'Modelo'), 1)
            est.retirar(1, 2)
            dados = est.historico
            for evento in dados:
                del evento['modelo']
            arquivo.write_text(json.dumps(dados), encoding='utf-8')
            novo = Estacionamento.carregar_historico(arquivo)
            self.assertEqual(novo.historico, dados)
            self.assertEqual(novo.relatorio()['faturamento'], 20)
            self.assertEqual(novo.buscar_veiculo('ABC1234').modelo, 'Modelo não registrado')

    def test_menu_novo_fluxo_e_abertura_invalida(self):
        import io
        from contextlib import redirect_stdout
        from unittest.mock import patch
        from controller.controller import Controller
        from view.ui_texto import menu
        ctrl = Controller()
        respostas = ['5', 'carro', 'abc-1234', 'Modelo', '6', 'ABC1234', '1',
                     '3', '7', 'ABC1234', '2', '3', '4']
        with patch('builtins.input', side_effect=respostas), \
                patch('view.ui_texto.Controller', return_value=ctrl), \
                patch.object(ctrl, 'salvar'), redirect_stdout(io.StringIO()) as saida:
            menu()
        self.assertIn('Veículo ABC1234 cadastrado.', saida.getvalue())
        self.assertIn('Tarifa: R$ 20.00', saida.getvalue())
        self.assertEqual(ctrl.relatorio()['faturamento'], 20)
        with patch('view.ui_texto.Controller', side_effect=ValueError('Corrompido')), \
                patch('builtins.input') as entrada, redirect_stdout(io.StringIO()) as saida:
            menu()
        entrada.assert_not_called()
        self.assertIn('Não foi possível abrir', saida.getvalue())

    def test_alteracao_externa_nao_e_sobrescrita(self):
        import tempfile
        from pathlib import Path
        from controller.controller import Controller
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / 'historico.json'
            ctrl = Controller(arquivo)
            ctrl.salvar()
            arquivo.write_text('{corrompido', encoding='utf-8')
            with self.assertRaises(OSError):
                ctrl.salvar()
            self.assertEqual(arquivo.read_text(), '{corrompido')

    def test_eventos_invalidos_nao_modificam_json(self):
        import json
        import tempfile
        from copy import deepcopy
        from pathlib import Path
        est = Estacionamento()
        est.estacionar(Carro('ABC1234', 'Modelo'), 1)
        est.retirar(1, 1)
        original = est.historico
        casos = []
        for campo, valor in (('valor', -10), ('horas', -1), ('tipo', 'moto'),
                             ('vaga', 2), ('horario_saida', 'invalido'),
                             ('horario_entrada', 'invalido')):
            dados = deepcopy(original)
            dados[-1][campo] = valor
            casos.append(dados)
        casos.append([original[-1]])
        casos.append([original[0], original[0]])
        for dados in casos:
            with self.subTest(dados=dados), tempfile.TemporaryDirectory() as pasta:
                arquivo = Path(pasta) / 'historico.json'
                texto = json.dumps(dados)
                arquivo.write_text(texto, encoding='utf-8')
                with self.assertRaises(ValueError):
                    Estacionamento.carregar_historico(arquivo)
                self.assertEqual(arquivo.read_text(encoding='utf-8'), texto)
