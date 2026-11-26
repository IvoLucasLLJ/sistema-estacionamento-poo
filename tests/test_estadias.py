import json
import tempfile
import unittest
from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from controller.controller import Controller


class EstadiasTests(unittest.TestCase):
    def setUp(self):
        pasta = self.enterContext(tempfile.TemporaryDirectory())
        self.arquivo = Path(pasta) / 'historico.json'
        self.ctrl = Controller(self.arquivo)

    def vincular(self, categoria='vip', tipo='carro', placa='ABC1234'):
        cliente = self.ctrl.cadastrar_cliente(categoria, 'Ana')
        self.ctrl.cadastrar_veiculo(tipo, placa, 'Modelo')
        self.ctrl.vincular_veiculo(placa, cliente.identificador)
        return cliente

    def entrar(self, categoria='vip', tipo='carro'):
        cliente = self.vincular(categoria, tipo)
        self.ctrl.iniciar_estadia('ABC1234', 1, cliente.identificador)
        return cliente

    def test_vinculos_e_consultas_apos_recarga(self):
        cliente = self.vincular(placa=' abc-1234 ')
        segundo = self.ctrl.cadastrar_veiculo('moto', 'DEF5678', 'Biz')
        self.assertIsNone(self.ctrl.cliente_do_veiculo(segundo.placa))
        self.ctrl.vincular_veiculo(segundo.placa, cliente.identificador)
        self.ctrl.salvar()
        ctrl = Controller(self.arquivo)
        self.assertIs(ctrl.cliente_do_veiculo('abc-1234'), ctrl.buscar_cliente(cliente.identificador))
        self.assertEqual(ctrl.veiculos_do_cliente(cliente.identificador),
                         (ctrl.buscar_veiculo('ABC1234'), ctrl.buscar_veiculo('DEF5678')))

    def test_rejeita_vinculos_invalidos_e_conflitantes(self):
        cliente = self.vincular()
        outro = self.ctrl.cadastrar_cliente('comum', 'Bia')
        anterior = self.ctrl.estacionamento.historico
        for placa, dono in [('ABC1234', cliente.identificador), ('ABC1234', outro.identificador),
                            ('OUTRA', cliente.identificador), ('ABC1234', 'invalido'),
                            ('ABC1234', '01111111-2222-4333-8444-555555555555')]:
            with self.subTest(placa=placa, dono=dono), self.assertRaises(ValueError):
                self.ctrl.vincular_veiculo(placa, dono)
        with self.assertRaises(ValueError):
            self.ctrl.iniciar_estadia('ABC1234', 1, outro.identificador)
        with self.assertRaises(ValueError):
            self.ctrl.cliente_do_veiculo('OUTRA')
        with self.assertRaises(ValueError):
            self.ctrl.veiculos_do_cliente('invalido')
        self.assertEqual(self.ctrl.estacionamento.historico, anterior)

    def test_vinculo_bloqueado_durante_estadia_legada(self):
        self.ctrl.estacionar_veiculo('moto', 'ABC1234', 'Biz', 1)
        cliente = self.ctrl.cadastrar_cliente('vip', 'Ana')
        with self.assertRaises(ValueError):
            self.ctrl.vincular_veiculo('ABC1234', cliente.identificador)
        self.assertEqual(self.ctrl.retirar_veiculo(1, 2), 10)
        self.ctrl.vincular_veiculo('ABC1234', cliente.identificador)

    def test_nove_combinacoes_com_saida_e_recarga(self):
        resultados = {'carro': (20, 10, 0), 'moto': (10, 5, 0), 'caminhao': (40, 20, 0)}
        for tipo, esperados in resultados.items():
            for categoria, esperado in zip(('comum', 'vip', 'mensalista'), esperados):
                with self.subTest(tipo=tipo, categoria=categoria):
                    placa = tipo + categoria
                    self.vincular(categoria, tipo, placa)
                    self.ctrl.estacionar_cadastrado(placa, 1)
                    self.ctrl.salvar()
                    self.ctrl = Controller(self.arquivo)
                    cobranca = self.ctrl.consultar_cobranca(placa, 2)
                    self.assertIsInstance(cobranca.valor_devido, Decimal)
                    self.assertEqual(cobranca.tarifa_base, esperados[0])
                    self.assertEqual(cobranca.valor_devido, esperado)
                    if esperado:
                        self.ctrl.confirmar_pagamento(cobranca, confirmado=True)
                    self.assertEqual(self.ctrl.concluir_saida(cobranca), esperado)
        self.ctrl.salvar()
        self.assertEqual(Controller(self.arquivo).relatorio(),
                         {'ocupadas': 0, 'livres': 200, 'faturamento': Decimal('105.00')})

    def test_decimais_desconto_antes_do_arredondamento(self):
        self.entrar()
        for horas, base, desconto, devido in (
            (1.225, '12.250', '6.125', '6.13'),
            (Decimal('0.0009'), '0.009', '0.0045', '0.00'),
            (Decimal('1.2249999999999999999999999999999999'),
             '12.249999999999999999999999999999999',
             '6.1249999999999999999999999999999995', '6.12'),
            (0, '0', '0', '0.00'),
        ):
            with self.subTest(horas=horas):
                c = self.ctrl.consultar_cobranca('ABC1234', horas)
                self.assertEqual((c.tarifa_base, c.desconto, c.valor_devido),
                                 tuple(map(Decimal, (base, desconto, devido))))

    def test_horas_invalidas_preservam_ocupacao(self):
        self.entrar()
        original = self.ctrl.estacionamento.historico
        for horas in (-1, True, False, float('inf'), float('nan'), Decimal('-Infinity'),
                      Decimal('sNaN'), '1.225', None, 1e308, 10**400):
            with self.subTest(horas=horas), self.assertRaises(ValueError):
                self.ctrl.consultar_cobranca('ABC1234', horas)
        self.assertEqual(self.ctrl.estacionamento.historico, original)
        self.assertEqual(self.ctrl.relatorio()['ocupadas'], 1)

    def test_consulta_recusa_cancelamento_e_api_antiga(self):
        self.vincular()
        self.ctrl.estacionar_veiculo('carro', 'abc-1234', 'Modelo', 1)
        original = self.ctrl.estacionamento.historico
        c = self.ctrl.consultar_cobranca('abc-1234', 2)
        for resposta in (False, None, 'cancelado', 'recusado', 1):
            with self.subTest(resposta=resposta), self.assertRaises(ValueError):
                self.ctrl.confirmar_pagamento(c, confirmado=resposta)
        with self.assertRaises(ValueError):
            self.ctrl.concluir_saida(c)
        with self.assertRaises(ValueError):
            self.ctrl.retirar_por_placa('ABC1234', 2)
        with self.assertRaises(ValueError):
            self.ctrl.retirar_veiculo(1, 2)
        self.assertEqual(self.ctrl.estacionamento.historico, original)
        self.assertEqual(self.ctrl.relatorio(), {'ocupadas': 1, 'livres': 199, 'faturamento': 0})

    def test_confirmacao_vinculada_a_estadia_e_ao_valor(self):
        self.entrar()
        c = self.ctrl.consultar_cobranca('ABC1234', Decimal('1.225'))
        zero = self.ctrl.consultar_cobranca('ABC1234', 0)
        with self.assertRaises(ValueError):
            self.ctrl.confirmar_pagamento(replace(c, valor_centavos=1), confirmado=True)
        self.ctrl.confirmar_pagamento(c, confirmado=True)
        self.assertEqual(self.ctrl.relatorio()['faturamento'], 0)
        self.ctrl.salvar()
        self.ctrl = Controller(self.arquivo)
        with self.assertRaises(ValueError):
            self.ctrl.confirmar_pagamento(c, confirmado=True)
        with self.assertRaises(ValueError):
            self.ctrl.concluir_saida(zero)
        self.assertEqual(self.ctrl.concluir_saida(c), Decimal('6.13'))
        with self.assertRaises(ValueError):
            self.ctrl.concluir_saida(c)
        self.ctrl.estacionar_cadastrado('ABC1234', 1)
        with self.assertRaises(ValueError):
            self.ctrl.confirmar_pagamento(c, confirmado=True)
        self.assertEqual(self.ctrl.relatorio()['faturamento'], Decimal('6.13'))

    def test_vaga_exposta_nao_libera_estadia_fora_da_conclusao(self):
        self.entrar()
        vaga = self.ctrl.estacionamento.vagas[0]
        consulta = self.ctrl.consultar_cobranca('ABC1234', 2)
        with self.assertRaises(ValueError):
            vaga.liberar()
        self.ctrl.confirmar_pagamento(consulta, confirmado=True)
        with self.assertRaises(ValueError):
            vaga.liberar()
        self.assertTrue(vaga.ocupada)
        self.assertEqual(self.ctrl.relatorio()['faturamento'], 0)
        self.ctrl.concluir_saida(consulta)
        self.assertFalse(vaga.ocupada)

    def test_historico_misto_preserva_valor_fracionario_legado(self):
        self.ctrl.estacionar_veiculo('carro', 'ANTIGA', 'Modelo', 2)
        valor = self.ctrl.retirar_veiculo(2, 0.0125)
        legado = self.ctrl.estacionamento.historico
        self.entrar('comum')
        c = self.ctrl.consultar_cobranca('ABC1234', 1)
        self.ctrl.confirmar_pagamento(c, confirmado=True)
        self.ctrl.concluir_saida(c)
        self.ctrl.salvar()
        novo = Controller(self.arquivo)
        self.assertEqual(novo.estacionamento.historico[:2], legado)
        self.assertEqual(valor, 0.125)
        self.assertEqual(novo.relatorio()['faturamento'], Decimal('10.125'))
        self.assertIsNone(novo.cliente_do_veiculo('ANTIGA'))

    def test_reabre_pagamento_sem_depender_da_consulta_da_sessao_anterior(self):
        self.entrar()
        self.assertIsNone(self.ctrl.consultar_pagamento('ABC1234'))
        self.ctrl.confirmar_pagamento(self.ctrl.consultar_cobranca('ABC1234', 1.225),
                                     confirmado=True)
        self.ctrl.salvar()
        novo = Controller(self.arquivo)
        pago = novo.consultar_pagamento('abc-1234')
        self.assertEqual((pago.horas, pago.valor_devido), (Decimal('1.225'), Decimal('6.13')))
        with self.assertRaises(ValueError):
            novo.consultar_cobranca('ABC1234', 3)
        self.assertEqual(novo.concluir_saida(pago), Decimal('6.13'))

    def test_valor_zero_dispensa_confirmacao_e_recupera_isencao(self):
        self.entrar('comum')
        consulta = self.ctrl.consultar_cobranca('ABC1234', 0)
        with self.assertRaises(ValueError):
            self.ctrl.confirmar_pagamento(consulta, confirmado=True)
        self.assertEqual(self.ctrl.concluir_saida(consulta), Decimal('0.00'))
        self.ctrl.salvar()
        novo = Controller(self.arquivo)
        saida = novo.estacionamento.historico[-1]
        self.assertEqual((saida['pagamento'], saida['valor_centavos']), ('isento', 0))
        self.assertIsInstance(novo.relatorio()['faturamento'], Decimal)
        self.assertEqual(novo.relatorio()['livres'], 200)

    def test_falha_ao_salvar_saida_preserva_pagamento_e_permite_repetir(self):
        self.entrar()
        c = self.ctrl.consultar_cobranca('ABC1234', 2)
        self.ctrl.confirmar_pagamento(c, confirmado=True)
        self.ctrl.salvar()
        anterior = self.arquivo.read_bytes()
        self.ctrl.concluir_saida(c)
        with patch('persistence.historico_json.os.replace', side_effect=OSError('Falha simulada')):
            with self.assertRaises(OSError):
                self.ctrl.salvar()
        self.assertEqual(self.arquivo.read_bytes(), anterior)
        recuperado = Controller(self.arquivo)
        self.assertEqual(recuperado.relatorio()['ocupadas'], 1)
        self.assertEqual(recuperado.concluir_saida(c), Decimal('10.00'))
        self.ctrl.salvar()
        self.assertEqual(Controller(self.arquivo).relatorio()['faturamento'], 10)

    def test_saida_antiga_nao_encerra_segunda_estadia_da_mesma_placa(self):
        self.entrar()
        for _ in range(2):
            c = self.ctrl.consultar_cobranca('ABC1234', 2)
            self.ctrl.confirmar_pagamento(c, confirmado=True)
            self.ctrl.concluir_saida(c)
            self.ctrl.estacionar_cadastrado('ABC1234', 1)
        eventos = self.ctrl.estacionamento.historico[:-1]
        saidas = [e for e in eventos if e['acao'] == 'saida_cliente']
        self.assertNotEqual(saidas[0]['estadia_id'], saidas[1]['estadia_id'])
        eventos[-1] = saidas[0]
        with self.assertRaises(ValueError):
            self.ctrl.estacionamento.reconstruir(eventos)

    def test_saida_com_valor_legado_e_centavos_conflitantes_e_rejeitada(self):
        self.ctrl.estacionar_veiculo('carro', 'ANTIGA', 'Modelo', 2)
        self.ctrl.retirar_veiculo(2, 1)
        eventos = self.ctrl.estacionamento.historico
        eventos[-1]['valor_centavos'] = 1
        with self.assertRaises(ValueError):
            self.ctrl.estacionamento.reconstruir(eventos)

    def test_eventos_incompletos_adulterados_e_fora_de_ordem(self):
        self.entrar()
        c = self.ctrl.consultar_cobranca('ABC1234', 1.225)
        self.ctrl.confirmar_pagamento(c, confirmado=True)
        self.ctrl.concluir_saida(c)
        eventos = self.ctrl.estacionamento.historico
        self.assertEqual([e['acao'] for e in eventos[2:]],
                         ['vinculo', 'entrada_cliente', 'pagamento_confirmado', 'saida_cliente'])
        casos = []
        for indice in range(2, len(eventos)):
            for campo in eventos[indice]:
                dados = deepcopy(eventos)
                del dados[indice][campo]
                casos.append((f'{indice} sem {campo}', dados))
        for indice, campo, valor in (
            (2, 'cliente_id', 'inexistente'), (2, 'placa', 'OUTRA'),
            (3, 'categoria', 'mensalista'), (3, 'acao', 'entrada'), (3, 'vaga', True),
            (4, 'valor_centavos', 612), (4, 'estadia_id', 9999),
            (5, 'desconto', '0'), (5, 'horas', '2'), (5, 'tarifa_base', '0'),
            (5, 'valor_centavos', True), (5, 'valor_centavos', 613.0),
            (5, 'pagamento', 'isento'), (5, 'horario_saida', '2001-01-01T00:00:00+00:00'),
            (5, 'cliente_id', 'inexistente'), (5, 'valor', 999), (5, 'categoria', 'comum'),
        ):
            dados = deepcopy(eventos)
            dados[indice][campo] = valor
            casos.append((f'{indice} {campo}={valor}', dados))
        casos.extend([('sem pagamento', eventos[:4] + eventos[5:]),
                      ('duas saidas', eventos + [eventos[-1]]),
                      ('duas confirmacoes', eventos[:5] + eventos[4:]),
                      ('sem vinculo', eventos[:2] + eventos[3:]),
                      ('vinculo duplicado', eventos[:3] + eventos[2:])])
        saida_legada = {k: eventos[-1][k] for k in
                        ('placa', 'vaga', 'horario_entrada', 'horario_saida')}
        saida_legada.update(acao='saida', horas=1.225, tipo='carro', modelo='Modelo', valor=12.25)
        casos.append(('saida legada sobre entrada vinculada', eventos[:4] + [saida_legada]))
        for caso, dados in casos:
            with self.subTest(caso=caso):
                original = json.dumps(dados).encode()
                self.arquivo.write_bytes(original)
                with self.assertRaises(ValueError):
                    Controller(self.arquivo)
                self.assertEqual(self.arquivo.read_bytes(), original)
