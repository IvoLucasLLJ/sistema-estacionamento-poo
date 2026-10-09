import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from controller.controller import Controller
from model.carro import Carro
from model.moto import Moto
from model.caminhao import Caminhao
from model.estacionamento import Estacionamento
from repository.estacionamento_repository import EstacionamentoRepository


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.arquivo = Path(self.pasta.name) / 'historico.json'
        self.repo = EstacionamentoRepository(self.arquivo)

    def test_controller_injeta_repository_sem_usar_adaptadores(self):
        est = Estacionamento()
        repo = Mock()
        repo.carregar.return_value = est
        with patch.object(Estacionamento, 'carregar_historico', side_effect=AssertionError), \
                patch.object(Estacionamento, 'salvar_historico', side_effect=AssertionError):
            ctrl = Controller(repository=repo)
            ctrl.cadastrar_veiculo('carro', 'ABC1234', 'Onix')
            ctrl.salvar()
        repo.carregar.assert_called_once_with()
        repo.salvar.assert_called_once_with(est)
        self.assertIs(ctrl.buscar_veiculo('ABC1234'), est.veiculos[0])

    def test_reconstroi_subclasses_e_identidade_dos_cadastros(self):
        est = self.repo.carregar()
        for numero, classe in enumerate((Carro, Moto, Caminhao), 1):
            veiculo = classe(f'ABC{numero}', f'Modelo {numero}')
            est.cadastrar_veiculo(veiculo)
            est.estacionar_cadastrado(veiculo.placa, numero)
        original = est.historico
        self.repo.salvar(est)
        novo = EstacionamentoRepository(self.arquivo).carregar()
        self.assertEqual(novo.historico, original)
        for numero, classe in enumerate((Carro, Moto, Caminhao), 1):
            veiculo = novo.buscar_veiculo(f'ABC{numero}')
            self.assertIsInstance(veiculo, classe)
            self.assertIs(novo.vagas[numero - 1].veiculo, veiculo)
        self.assertEqual(novo.retirar_por_placa('ABC3', 2), 40)
        self.assertIsInstance(novo.buscar_veiculo('ABC3'), Caminhao)

    def test_duas_sessoes_detectam_conflito(self):
        self.repo.salvar(self.repo.carregar())
        outra = EstacionamentoRepository(self.arquivo)
        antigo = outra.carregar()
        novo = self.repo.carregar()
        novo.cadastrar_veiculo(Carro('ABC1234', 'Onix'))
        self.repo.salvar(novo)
        bytes_originais = self.arquivo.read_bytes()
        with self.assertRaises(OSError):
            outra.salvar(antigo)
        self.assertEqual(self.arquivo.read_bytes(), bytes_originais)

    def test_falha_permite_repetir_gravacao(self):
        self.arquivo.write_text('[]', encoding='utf-8')
        est = self.repo.carregar()
        est.cadastrar_veiculo(Carro('ABC1234', 'Onix'))
        with patch('persistence.historico_json.os.replace', side_effect=OSError('falha')):
            with self.assertRaises(OSError):
                self.repo.salvar(est)
        self.assertEqual(self.arquivo.read_text(), '[]')
        self.assertEqual(list(Path(self.pasta.name).iterdir()), [self.arquivo])
        self.repo.salvar(est)
        self.repo.salvar(est)
        self.assertEqual(self.repo.carregar().historico, est.historico)

    def test_reconstrucao_independe_de_arquivo_e_isola_dados(self):
        est = Estacionamento()
        est.estacionar(Carro('ABC1234', 'Onix'), 1)
        dados = est.historico
        dados[0]['extra'] = {'origem': 'teste'}
        with patch('persistence.historico_json.ler', side_effect=AssertionError):
            novo = Estacionamento.reconstruir(dados)
        dados[0]['extra']['origem'] = 'alterada'
        self.assertEqual(novo.historico[0]['extra']['origem'], 'teste')
        self.assertEqual(novo.historico[0]['horario_entrada'], est.historico[0]['horario_entrada'])

    def test_rejeita_tipo_desconhecido_e_nao_apaga_arquivo(self):
        est = Estacionamento()
        est.estacionar(Carro('ABC1234', 'Onix'), 1)
        dados = est.historico
        dados[0]['tipo'] = 'onibus'
        conteudo = json.dumps(dados).encode()
        self.arquivo.write_bytes(conteudo)
        with self.assertRaises(ValueError):
            self.repo.carregar()
        with self.assertRaises(OSError):
            self.repo.salvar(Estacionamento())
        self.assertEqual(self.arquivo.read_bytes(), conteudo)

    def test_adaptador_legado_reutiliza_destino_carregado(self):
        self.repo.salvar(self.repo.carregar())
        est = Estacionamento.carregar_historico(self.arquivo)
        est.cadastrar_veiculo(Carro('ABC1234', 'Onix'))
        est.salvar_historico()
        est.salvar_historico()
        self.assertEqual(self.repo.carregar().historico, est.historico)

    def test_repository_sem_leitura_nao_sobrescreve_destino_existente(self):
        self.arquivo.write_text('[]', encoding='utf-8')
        with self.assertRaises(OSError):
            self.repo.salvar(Estacionamento())
        self.assertEqual(self.arquivo.read_text(), '[]')


if __name__ == '__main__':
    unittest.main()
