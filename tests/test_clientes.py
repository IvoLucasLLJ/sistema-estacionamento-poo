import unittest

from model.cliente import Cliente
from model.cliente_comum import ClienteComum
from model.cliente_mensalista import ClienteMensalista
from model.cliente_vip import ClienteVIP


class ClientesTests(unittest.TestCase):
    def test_cliente_abstrato_nao_pode_ser_instanciado(self):
        with self.assertRaises(TypeError):
            Cliente()

    def test_categorias_herdam_de_cliente(self):
        for classe in (ClienteComum, ClienteVIP, ClienteMensalista):
            with self.subTest(classe=classe):
                self.assertTrue(issubclass(classe, Cliente))

    def test_cobranca_polimorfica_por_tarifa_base(self):
        clientes = (ClienteComum(), ClienteVIP(), ClienteMensalista())
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
        for cliente in (ClienteComum(), ClienteVIP(), ClienteMensalista()):
            for tarifa_base in invalidas:
                with self.subTest(cliente=type(cliente).__name__, tarifa_base=tarifa_base):
                    with self.assertRaises(ValueError):
                        cliente.calcular_cobranca(tarifa_base)
