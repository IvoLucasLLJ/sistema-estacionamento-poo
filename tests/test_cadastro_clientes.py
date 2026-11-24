import json
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from controller.controller import Controller
from model.cliente_comum import ClienteComum
from model.cliente_mensalista import ClienteMensalista
from model.cliente_vip import ClienteVIP
from model.estacionamento import Estacionamento
from repository.estacionamento_repository import EstacionamentoRepository


class CadastroClientesTests(unittest.TestCase):
    def test_homonimos_busca_e_isolamento_da_listagem(self):
        est = Estacionamento()
        primeira = est.cadastrar_cliente(ClienteComum('Ana'))
        listagem_anterior = est.listar_clientes()
        segunda = est.cadastrar_cliente(ClienteComum('Ana'))
        self.assertNotEqual(primeira.identificador, segunda.identificador)
        self.assertEqual(listagem_anterior, (primeira,))
        self.assertEqual(est.listar_clientes(), (primeira, segunda))
        self.assertIs(est.buscar_cliente(primeira.identificador), primeira)
        self.assertIs(est.buscar_cliente(segunda.identificador), segunda)
        with self.assertRaises(TypeError):
            listagem_anterior[0] = segunda
        copia = est.historico
        copia[0]['nome'] = 'Outro'
        self.assertEqual(est.historico[0]['nome'], 'Ana')

    def test_cadastro_rejeitado_preserva_estado_e_eventos(self):
        class CategoriaNaoRegistrada(ClienteVIP):
            pass

        est = Estacionamento()
        cliente = est.cadastrar_cliente(ClienteVIP('Ana'))
        original = est.historico
        duplicado = ClienteMensalista('Outro', identificador=cliente.identificador.upper())
        for invalido in (cliente, duplicado, CategoriaNaoRegistrada('Bia'), object(), None):
            with self.subTest(invalido=invalido), self.assertRaises(ValueError):
                est.cadastrar_cliente(invalido)
        for identificador in (str(uuid4()), 'invalido', None):
            with self.subTest(identificador=identificador), self.assertRaises(ValueError):
                est.buscar_cliente(identificador)
        self.assertEqual(est.listar_clientes(), (cliente,))
        self.assertEqual(est.historico, original)


class PersistenciaClientesTests(unittest.TestCase):
    def setUp(self):
        pasta = self.enterContext(tempfile.TemporaryDirectory())
        self.arquivo = Path(pasta) / 'historico.json'

    def test_controller_salva_e_recupera_historico_misto(self):
        ctrl = Controller(self.arquivo)
        ctrl.estacionar_veiculo('carro', 'ABC1234', 'Onix', 1)
        categorias = (('comum', ClienteComum, 20), ('vip', ClienteVIP, 10),
                      ('mensalista', ClienteMensalista, 0))
        originais = []
        for categoria, classe, _ in categorias:
            cliente = ctrl.cadastrar_cliente(categoria, 'Ana')
            self.assertIs(type(cliente), classe)
            self.assertIs(ctrl.buscar_cliente(cliente.identificador), cliente)
            originais.append(cliente)
        self.assertEqual(ctrl.listar_clientes(), tuple(originais))
        with self.assertRaises(ValueError):
            ctrl.cadastrar_cliente('desconhecida', 'Ana')
        ctrl.salvar()

        eventos = json.loads(self.arquivo.read_text(encoding='utf-8'))
        self.assertEqual(
            [(e['acao'], e['identificador'], e['nome'], e['categoria']) for e in eventos[1:]],
            [('cadastro_cliente', c.identificador, c.nome, c.categoria) for c in originais],
        )
        novo = Controller(self.arquivo)
        self.assertEqual(len(novo.listar_clientes()), 3)
        for original, (categoria, classe, valor) in zip(originais, categorias):
            recuperado = novo.buscar_cliente(original.identificador)
            self.assertIs(type(recuperado), classe)
            self.assertEqual(recuperado.identificador, original.identificador)
            self.assertEqual((recuperado.nome, recuperado.categoria), ('Ana', categoria))
            self.assertEqual(recuperado.calcular_cobranca(20), valor)
        self.assertEqual(novo.retirar_por_placa('ABC1234', 2), 20)
        novo.salvar()
        final = Controller(self.arquivo)
        self.assertEqual(final.relatorio(), {'ocupadas': 0, 'livres': 10, 'faturamento': 20})
        self.assertEqual(final.estacionamento.historico[:-1], eventos)
        self.assertEqual(len(final.listar_clientes()), 3)

    def test_legado_sem_clientes_pode_receber_primeiro_cadastro(self):
        entrada = {'acao': 'entrada', 'placa': 'ABC1234', 'tipo': 'moto', 'vaga': 1,
                   'horario_entrada': '2025-03-10T08:00:00-03:00'}
        self.arquivo.write_text(json.dumps([entrada]), encoding='utf-8')
        ctrl = Controller(self.arquivo)
        self.assertEqual(ctrl.listar_clientes(), ())
        self.assertEqual(ctrl.buscar_veiculo('ABC1234').modelo, 'Modelo não registrado')
        cliente = ctrl.cadastrar_cliente('vip', 'Bia')
        ctrl.salvar()
        novo = Controller(self.arquivo)
        self.assertEqual(novo.estacionamento.historico[0], entrada)
        self.assertEqual(novo.listar_clientes(), (novo.buscar_cliente(cliente.identificador),))
        self.assertEqual(novo.retirar_por_placa('ABC1234', 1), 5)

    def test_eventos_invalidos_preservam_arquivo_e_ultima_carga_valida(self):
        valido = {'acao': 'cadastro_cliente', 'identificador': str(uuid4()),
                  'nome': 'Ana', 'categoria': 'vip'}
        self.arquivo.write_text(json.dumps([valido]), encoding='utf-8')
        repo = EstacionamentoRepository(self.arquivo)
        anterior = repo.carregar()
        segundo = dict(valido, identificador=str(uuid4()))
        invalidos = [dict(segundo, categoria='desconhecida'), dict(segundo, categoria=[]),
                     dict(segundo, nome=' '), dict(segundo, nome=None),
                     dict(segundo, nome=' Ana '),
                     dict(segundo, identificador=segundo['identificador'].replace('-', '')),
                     dict(segundo, identificador=None), dict(segundo, identificador='invalido'),
                     dict(valido, nome='Outro', categoria='comum')]
        for campo in ('identificador', 'nome', 'categoria'):
            invalidos.append({chave: valor for chave, valor in segundo.items() if chave != campo})
        for evento in invalidos:
            with self.subTest(evento=evento):
                original = json.dumps([valido, evento]).encode()
                self.arquivo.write_bytes(original)
                with self.assertRaises(ValueError):
                    repo.carregar()
                self.assertEqual(anterior.historico, [valido])
                with self.assertRaises(OSError):
                    repo.salvar(anterior)
                self.assertEqual(self.arquivo.read_bytes(), original)

    def test_reconstrucao_isola_campos_adicionais_do_evento(self):
        evento = {'acao': 'cadastro_cliente', 'identificador': str(uuid4()), 'nome': 'Ana',
                  'categoria': 'comum', 'extra': {'origem': 'teste'}}
        est = Estacionamento.reconstruir([evento])
        evento['extra']['origem'] = 'alterada'
        self.assertEqual(est.historico[0]['extra'], {'origem': 'teste'})
