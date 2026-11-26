"""Operações do titular, com persistência temporária e os mesmos serviços da Gestão."""
import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from secrets import token_urlsafe
from tempfile import TemporaryDirectory
from threading import Barrier
from unittest import TestCase
from uuid import uuid4

from service.estacionamento_service import ErroDeInfraestrutura, ErroDeNegocio, EstacionamentoService
from web import create_app


class AutosservicoTests(TestCase):
    def setUp(self):
        raiz = Path(self.enterContext(TemporaryDirectory()))
        self.arquivo = raiz / 'historico.json'
        self.s = EstacionamentoService(self.arquivo)
        self.a = self.s.cadastrar_cliente('comum', 'Alex Demo')['identificador']
        self.b = self.s.cadastrar_cliente('comum', 'Alex Demo')['identificador']

    def test_frota_atomica_sem_reivindicar_placa_preexistente(self):
        self.s.cadastrar_veiculo_do_cliente(self.a, 'carro', 'car-01', 'Aurora')
        self.s.cadastrar_veiculo_do_cliente(self.a, 'moto', 'moto02', 'Lua')
        antes = self.arquivo.read_bytes()
        for titular, placa in [(self.b, 'CAR01'), (str(uuid4()), 'NOVO')]:
            with self.assertRaises(ErroDeNegocio):
                self.s.cadastrar_veiculo_do_cliente(titular, 'carro', placa, 'Teste')
        self.assertEqual(self.arquivo.read_bytes(), antes)
        leitor = EstacionamentoService(self.arquivo)
        self.assertEqual([v['placa'] for v in leitor.veiculos_do_cliente(self.a)], ['CAR01', 'MOTO02'])
        self.assertEqual(leitor.veiculos_do_cliente(self.b), [])

    def test_reserva_disputada_cancelamento_pelo_titular_e_reenvio(self):
        pares = [(self.a, 'CAR1'), (self.b, 'CAR2')]
        for titular, placa in pares:
            self.s.cadastrar_veiculo_do_cliente(titular, 'carro', placa, 'Modelo')
        barreira = Barrier(2)
        def tentar(par):
            s = EstacionamentoService(self.arquivo)
            barreira.wait(timeout=10)
            try:
                s.reservar_vaga(*par, 2)
            except ErroDeNegocio:
                return False
            return True
        with ThreadPoolExecutor(max_workers=2) as pool:
            resultados = list(pool.map(tentar, pares))
        self.assertCountEqual(resultados, [True, False])
        dono, placa = pares[resultados.index(True)]
        outro, _ = pares[resultados.index(False)]
        self.assertEqual(self.s.consultar_ocupacao(), dict(livres=199, ocupadas=0, total=200))
        self.assertEqual(self.s.consultar_ocupacao(titular=outro)['minhas_reservas'], [])
        reserva = self.s.consultar_ocupacao(titular=dono)['minhas_reservas'][0]['id']
        with self.assertRaises(ErroDeNegocio):
            self.s.cancelar_reserva(outro, 2, reserva)
        with self.assertRaises(ErroDeNegocio):
            self.s.reservar_vaga(outro, placa, 3)
        self.s.cancelar_reserva(dono, 2, reserva)
        self.s.reservar_vaga(dono, placa, 2)
        with self.assertRaises(ErroDeNegocio):
            self.s.cancelar_reserva(dono, 2, reserva)
        self.assertEqual(self.s.consultar_ocupacao()['livres'], 199)

    def test_entrada_consome_reserva_do_veiculo_e_preserva_ocupacao_real(self):
        for titular, placa in [(self.a, 'M1'), (self.b, 'M2')]:
            self.s.cadastrar_veiculo_do_cliente(titular, 'moto', placa, 'Lua')
        self.s.reservar_vaga(self.a, 'M1', 2)
        for titular, placa, vaga in [(self.b, 'M2', 2), (self.a, 'M1', 3)]:
            with self.assertRaises(ErroDeNegocio):
                self.s.iniciar_estadia(placa, vaga, titular)
        with self.assertRaises(ErroDeNegocio):
            self.s.reservar_vaga(self.a, 'M1', 3)
        self.s.iniciar_estadia('M1', 2, self.a)
        leitor = EstacionamentoService(self.arquivo)
        self.assertEqual(leitor.consultar_ocupacao(), dict(livres=199, ocupadas=1, total=200))
        self.assertEqual(leitor.consultar_ocupacao(titular=self.a)['minhas_reservas'], [])
        with self.assertRaises(ErroDeNegocio):
            leitor.reservar_vaga(self.a, 'M1', 3)
        with self.assertRaises(ErroDeNegocio):
            leitor.reservar_vaga(self.b, 'M2', 2)

    def test_categorias_progressivas_preservam_estadias_e_identidade(self):
        for placa in ('COM', 'VIP', 'MEN'):
            self.s.cadastrar_veiculo_do_cliente(self.a, 'carro', placa, 'Atlas')
        self.s.iniciar_estadia('COM', 1, self.a)
        self.s.mudar_categoria(self.a, 'comum', 'vip')
        self.s.iniciar_estadia('VIP', 2, self.a)
        self.s.mudar_categoria(self.a, 'vip', 'mensalista')
        self.s.iniciar_estadia('MEN', 3, self.a)
        self.s.mudar_categoria(self.a, 'mensalista', 'comum')
        self.s.mudar_categoria(self.b, 'comum', 'mensalista')
        leitor = EstacionamentoService(self.arquivo)
        self.assertEqual([m['valor_centavos'] for m in leitor.mudancas_de_categoria(self.a)], [0, 25000, 25000])
        self.assertEqual(leitor.mudancas_de_categoria(self.b)[0]['valor_centavos'], 50000)
        self.assertEqual(leitor.consultar_faturamento()['centavos'], 0)
        for placa, valor in [('COM', 1225), ('VIP', 613), ('MEN', 0)]:
            with self.subTest(placa=placa):
                cotacao = leitor.consultar_cobranca(placa, '1.225')
                self.assertEqual(cotacao['valor_centavos'], valor)
                if valor:
                    leitor.confirmar_pagamento(placa, '1.225', cotacao, confirmado=True)
                leitor.concluir_saida(placa, '1.225', cotacao)
        self.assertEqual(leitor.consultar_faturamento()['centavos'], 1838)
        self.assertEqual(leitor.cliente_do_veiculo('MEN')['identificador'], self.a)

    def test_reconstrucao_recusa_recibo_inconsistente(self):
        self.s.mudar_categoria(self.a, 'comum', 'vip')
        eventos = json.loads(self.arquivo.read_text(encoding='utf-8'))
        eventos[-1]['valor_centavos'] = 1
        self.arquivo.write_text(json.dumps(eventos), encoding='utf-8')
        antes = self.arquivo.read_bytes()
        with self.assertRaises(ErroDeInfraestrutura):
            self.s.buscar_cliente(self.a)
        self.assertEqual(self.arquivo.read_bytes(), antes)

    def test_jornada_http_nova_conta_frota_reserva_e_compra(self):
        app = create_app(dict(TESTING=True, DADOS=self.arquivo.parent, HISTORICO=self.arquivo,
                              CONTAS=self.arquivo.parent / 'contas.json'))
        self.addCleanup(app.extensions['escritor'].fechar)
        http = app.test_client()
        def campo(url, nome):
            return re.search(f'name="{nome}" value="([^"]+)"', http.get(url).text)[1]
        def post(url, **dados):
            with http.session_transaction() as sessao:
                csrf = sessao['csrf']
            return http.post(url, data=dict(csrf_token=csrf, **dados))
        senha = token_urlsafe(24)
        resposta = post('/criar-conta', revisao=campo('/criar-conta', 'revisao'), nome='Bia Demo',
                        usuario='bia', senha=senha, confirmacao=senha, cadastrar_veiculos='sim')
        self.assertEqual(resposta.location, '/cliente/veiculos#novo-veiculo')
        titular = app.extensions['autenticacao'].contas.por_usuario('bia').identidade.cliente_id
        for placa in ('BIA1', 'BIA2'):
            self.assertEqual(post('/cliente/veiculos', tipo='moto', placa=placa, modelo='Lua').status_code, 303)
        self.assertEqual(len(self.s.veiculos_do_cliente(titular)), 2)
        self.assertEqual(http.post('/cliente/veiculos', data={}).status_code, 400)
        self.assertEqual(http.post('/cliente/tarifas/vip', data={}).status_code, 400)
        self.assertEqual(http.get('/gestao/').status_code, 403)
        res = '/cliente/reservas/3'
        self.assertEqual(post(res, revisao=campo(res, 'revisao'), placa='BIA2').status_code, 303)
        self.assertIn('Minhas reservas', http.get('/cliente/disponibilidade').text)
        id_res = self.s.consultar_ocupacao(titular=titular)['minhas_reservas'][0]['id']
        self.assertEqual(post(f'{res}/{id_res}/cancelar').status_code, 303)
        vip, mensal = '/cliente/tarifas/vip', '/cliente/tarifas/mensalista'
        antiga = campo(mensal, 'revisao')
        self.assertIn('R$ 500,00', http.get(mensal).text)
        revisao = campo(vip, 'revisao')
        self.assertEqual(post(vip, revisao=revisao).status_code, 303)
        self.assertEqual(post(vip, revisao=revisao).status_code, 409)
        self.assertEqual(post(mensal, revisao=antiga).status_code, 409)
        self.assertIn('R$ 250,00', http.get(mensal).text)
        self.assertEqual(post(mensal, revisao=campo(mensal, 'revisao')).status_code, 303)
        self.assertIn('Minhas mudanças de categoria', http.get('/cliente/tarifas').text)
        self.assertEqual(self.s.buscar_cliente(titular)['categoria'], 'mensalista')
