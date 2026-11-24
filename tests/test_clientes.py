import unittest
from uuid import UUID

from model.cliente import Cliente
from model.cliente_comum import ClienteComum
from model.cliente_mensalista import ClienteMensalista
from model.cliente_vip import ClienteVIP


class ClientesTests(unittest.TestCase):
    def test_cliente_abstrato_nao_pode_ser_instanciado(self):
        with self.assertRaises(TypeError):
            Cliente('Ana')

    def test_categorias_herdam_de_cliente(self):
        for classe in (ClienteComum, ClienteVIP, ClienteMensalista):
            with self.subTest(classe=classe):
                self.assertTrue(issubclass(classe, Cliente))

    def test_cobranca_polimorfica_por_tarifa_base(self):
        clientes = (ClienteComum('Ana'), ClienteVIP('Bia'), ClienteMensalista('Caio'))
        for tarifa_base, esperados in (
            (20, (20, 10, 0)),
            (10, (10, 5, 0)),
            (40, (40, 20, 0)),
            (0, (0, 0, 0)),
            (12.25, (12.25, 6.125, 0)),
        ):
            with self.subTest(tarifa_base=tarifa_base):
                cobrancas = tuple(cliente.calcular_cobranca(tarifa_base) for cliente in clientes)
                self.assertEqual(cobrancas, esperados)

    def test_todas_as_categorias_rejeitam_tarifas_invalidas(self):
        invalidas = (None, '20', True, False, -1, -0.25, float('nan'),
                     float('inf'), float('-inf'), 10**400)
        for cliente in (ClienteComum('Ana'), ClienteVIP('Bia'), ClienteMensalista('Caio')):
            for tarifa_base in invalidas:
                with self.subTest(cliente=type(cliente).__name__, tarifa_base=tarifa_base):
                    with self.assertRaises(ValueError):
                        cliente.calcular_cobranca(tarifa_base)

    def test_construtor_herdado_e_propriedades_de_leitura(self):
        for classe, categoria in ((ClienteComum, 'comum'), (ClienteVIP, 'vip'),
                                  (ClienteMensalista, 'mensalista')):
            with self.subTest(categoria=categoria):
                cliente = classe('  Ana Maria  ')
                self.assertEqual(UUID(cliente.identificador).version, 4)
                self.assertEqual(cliente.nome, 'Ana Maria')
                self.assertEqual(cliente.categoria, categoria)
                for atributo in ('identificador', 'nome', 'categoria'):
                    with self.assertRaises(AttributeError):
                        setattr(cliente, atributo, 'outro')

    def test_nome_obrigatorio_e_identificador_valido(self):
        for nome in ('', '   ', None, 123):
            with self.subTest(nome=nome), self.assertRaises(ValueError):
                ClienteVIP(nome)
        for identificador in ('', 'sem-uuid', 123, None):
            with self.subTest(identificador=identificador), self.assertRaises(ValueError):
                ClienteComum('Ana', identificador=identificador)
