"""Políticas do MOVE 2.0 exercitadas com o mesmo agregado utilizado pelo terminal e pelo Flask."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from model.carro import Carro
from model.cliente_comum import ClienteComum
from model.estacionamento import Estacionamento
from service.estacionamento_service import ErroDeNegocio, EstacionamentoService


class VagasInteligentesTests(TestCase):
    def setUp(self):
        self.arquivo = Path(self.enterContext(TemporaryDirectory())) / 'histórico.json'
        self.s = EstacionamentoService(self.arquivo)
        self.dono = self.s.cadastrar_cliente('vip', 'Pessoa fictícia')['identificador']
        self.outro = self.s.cadastrar_cliente('comum', 'Outra pessoa fictícia')['identificador']
        for placa, motor, dono in [('EV1', 'eletrica', self.dono), ('HB2', 'plugin', self.dono),
                                   ('ANT', 'desconhecida', self.dono), ('COM', 'convencional', self.outro)]:
            self.s.cadastrar_veiculo_do_cliente(dono, 'carro', placa, 'Modelo', motor)

    def conferir(self, dono, placa, grupo, meio, dias=1):
        return self.s.conferir_autorizacao(dono, placa, grupo, 'passageiro', meio,
                                           (date.today()+timedelta(days=dias)).isoformat())

    def invariante(self):
        vagas = EstacionamentoService(self.arquivo).consultar_vagas()
        contagem = Counter(v['estado'] for v in vagas)
        self.assertEqual(sum(contagem[k] for k in ('livre','reservada','ocupada')), 200)
        self.assertEqual(len({v['placa'] for v in vagas if v['ocupada']}), contagem['ocupada'])
        self.assertTrue(all(v['classificacao'] == 'comum' for v in vagas if v['vip']))
        self.assertEqual(sum(v['carregador'] is not None for v in vagas), 60)
        return contagem

    def test_cenario_isolado_reabre_sem_repopular_ou_confundir_beneficiarios(self):
        from web.cenario_inteligente import abrir, preparar

        pasta = self.arquivo.parent / 'demonstração independente'
        preparar(pasta)
        originais = {nome: (pasta / nome).read_bytes()
                     for nome in ('historico.json', 'contas.json', 'sessao.key', 'inteligente.json')}
        with self.assertRaisesRegex(ValueError, 'destino já existe'):
            preparar(pasta)
        app, lia = abrir(pasta)
        servico = app.extensions['estacionamento']
        self.assertEqual(len({a.pessoa for a in servico.autorizacoes(lia)}), 4)
        self.assertEqual(servico.consultar_ocupacao(), {'total': 200, 'livres': 194, 'ocupadas': 3})
        self.assertEqual(servico.indicadores()['eletricas'], 58)
        for nome, conteudo in originais.items():
            self.assertEqual((pasta / nome).read_bytes(), conteudo)

    def test_distribuicao_numeracao_limites_e_lotacao_integral(self):
        est = Estacionamento()
        self.assertEqual([v.numero for v in est.vagas], list(range(1, 201)))
        self.assertEqual(Counter(v.classificacao for v in est.vagas),
                         dict(comum=116, eletrica=60, pcd=4, idoso=10, adicional=4, familia=6))
        c = est.cadastrar_cliente(ClienteComum('Teste'))
        for v in est.vagas:
            placa = f'E{v.numero}'
            est.cadastrar_veiculo(Carro(placa, 'Modelo', 'eletrica'))
            est.vincular_veiculo(placa, c.identificador)
            if hasattr(v, 'grupos'):
                grupo = v.grupos[-1]
                meio = 'fisica' if grupo in ('pcd','idoso') else 'administrativa'
                est.conferir_autorizacao(c.identificador, placa, grupo, 'passageiro', meio, date.max.isoformat())
            est.iniciar_estadia(placa, v.numero, c.identificador, beneficiario_presente=True)
        self.assertEqual(est.relatorio()['ocupadas'], 200)
        self.assertEqual(Estacionamento.reconstruir(est.historico).relatorio()['livres'], 0)
        for numero in (0, 201):
            with self.assertRaises(ValueError):
                est.estacionar(Carro('FORA','Modelo'), numero)

    def test_beneficiario_e_placa_conferidos_sem_privilegio_comercial(self):
        for grupo, vaga, meio in [('pcd',177,'digital'),('idoso',181,'fisica'),('obesa',191,'administrativa'),
                                  ('gestante',195,'administrativa'),('colo',200,'administrativa')]:
            self.conferir(self.outro, 'COM', grupo, meio)
            self.s.reservar_vaga(self.outro, 'COM', vaga)
            with self.assertRaises(ErroDeNegocio):
                self.s.iniciar_estadia('COM', vaga, self.outro)
            e = self.s.iniciar_estadia('COM', vaga, self.outro, beneficiario_presente=True)
            self.assertEqual(self.s.consultar_estadia(e['estadia_id'])['categoria'], 'comum')
            self.s.concluir_saida('COM','0',self.s.consultar_cobranca('COM','0'))
            with self.assertRaises(ErroDeNegocio):
                self.s.reservar_vaga(self.dono, 'EV1', vaga)
        with self.assertRaises(ErroDeNegocio):
            self.conferir(self.dono, 'COM', 'pcd', 'digital')
        with self.assertRaises(ErroDeNegocio):
            self.conferir(self.dono, 'EV1', 'idoso', 'administrativa')

    def test_vencimento_e_reconstrucao_independem_da_data_de_leitura(self):
        self.conferir(self.dono, 'EV1', 'pcd', 'digital', 0)
        self.s.reservar_vaga(self.dono,'EV1',177)
        amanha = date.today() + timedelta(days=1)
        from datetime import datetime
        with patch('model.estacionamento.datetime', wraps=datetime) as clock:
            clock.now.return_value = datetime.combine(amanha, datetime.min.time()).astimezone()
            with self.assertRaises(ErroDeNegocio):
                self.s.iniciar_estadia('EV1',177,self.dono,beneficiario_presente=True)
            self.assertEqual(self.invariante()['reservada'], 1)

    def test_revogacao_ou_substituicao_nao_transfere_reserva(self):
        chave = self.conferir(self.dono, 'EV1', 'pcd', 'digital')
        with self.assertRaises(ErroDeNegocio):
            self.conferir(self.dono, 'HB2', 'pcd', 'digital')
        self.s.reservar_vaga(self.dono,'EV1',177)
        self.s.revogar_autorizacao(self.dono, chave)
        self.conferir(self.dono, 'EV1', 'pcd', 'fisica')
        with self.assertRaises(ErroDeNegocio):
            self.s.iniciar_estadia('EV1',177,self.dono,beneficiario_presente=True)
        self.assertIsNotNone(self.s.opcoes_de_vaga(self.dono,'EV1',entrada=True)[176]['motivo'])
        res = self.s.consultar_ocupacao(titular=self.dono)['minhas_reservas'][0]
        self.s.cancelar_reserva(self.dono,177,res['id'])
        self.assertEqual(self.invariante()['livre'],200)

    def test_recarga_falha_antes_e_durante_uso_preserva_saida_e_tarifa(self):
        for dono, placa in [(self.dono,'ANT'),(self.outro,'COM')]:
            with self.assertRaises(ErroDeNegocio):
                self.s.reservar_vaga(dono, placa, 117)
        self.s.reservar_vaga(self.dono,'HB2',117)
        self.s.alterar_carregador(117,False)
        with self.assertRaises(ErroDeNegocio):
            self.s.iniciar_estadia('HB2',117,self.dono)
        self.s.alterar_carregador(117,True)
        self.s.iniciar_estadia('HB2',117,self.dono)
        self.s.alterar_carregador(117,False)
        c = self.s.consultar_cobranca('HB2','1.225')
        self.assertEqual(c['valor_centavos'],613)
        self.s.confirmar_pagamento('HB2','1.225',c,confirmado=True)
        self.assertEqual(self.invariante()['ocupada'],1)
        self.s.concluir_saida('HB2','1.225',c)
        self.assertEqual(self.s.indicadores()['eletricas'],59)
        self.s.reservar_vaga(self.dono,'EV1',118)

    def test_vip_downgrade_antes_e_depois_da_entrada(self):
        for dono, placa, numero in [(self.outro,'COM',1),(self.dono,'EV1',117),(self.dono,'EV1',177)]:
            with self.assertRaises(ErroDeNegocio):
                self.s.reservar_vaga(dono, placa, numero,vip=True)
        self.s.reservar_vaga(self.dono,'ANT',1,vip=True)
        self.s.mudar_categoria(self.dono,'vip','comum')
        with self.assertRaises(ErroDeNegocio):
            self.s.iniciar_estadia('ANT',1,self.dono)
        self.s.mudar_categoria(self.dono,'comum','mensalista')
        e = self.s.iniciar_estadia('ANT',1,self.dono)
        self.s.mudar_categoria(self.dono,'mensalista','comum')
        self.assertEqual(self.s.indicadores()['vip'],1)
        c = self.s.consultar_cobranca('ANT','2')
        self.assertEqual(c['valor_centavos'],0)
        self.s.concluir_saida('ANT','2',c)
        self.assertEqual(self.s.indicadores()['vip'],0)
        self.assertTrue(self.s.consultar_estadia(e['estadia_id'])['vip'])
        self.assertEqual(self.invariante()['livre'],200)

    def test_disputa_vip_nao_confunde_placas_do_mesmo_titular(self):
        def tentar(placa):
            try:
                EstacionamentoService(self.arquivo).reservar_vaga(self.dono, placa, 42, vip=True)
                return placa
            except ErroDeNegocio:
                return None
        with ThreadPoolExecutor(2) as pool:
            resultados = list(pool.map(tentar, ['HB2','EV1']))
        self.assertEqual(resultados.count(None),1)
        vencedora = next(placa for placa in resultados if placa)
        outra = 'HB2' if vencedora == 'EV1' else 'EV1'
        self.assertEqual([v['numero'] for v in self.s.opcoes_de_vaga(self.dono,vencedora,entrada=True)
                          if not v['motivo']],[42])
        self.assertTrue(self.s.opcoes_de_vaga(self.dono,outra,entrada=True)[41]['motivo'])
        with self.assertRaises(ErroDeNegocio):
            self.s.iniciar_estadia(outra,42,self.dono)
        self.assertEqual(self.invariante()['reservada'],1)

    def test_sequencias_de_estados_conservam_somas_apos_cada_evento(self):
        from random import Random
        rng = Random(2200)
        estados = {'EV1': ('livre', None), 'HB2': ('livre', None)}
        for passo in range(40):
            placa = rng.choice(list(estados))
            estado, vaga = estados[placa]
            if estado == 'livre':
                vaga = rng.choice([n for n in range(1,7) if n not in {v for _,v in estados.values()}])
                self.s.reservar_vaga(self.dono,placa,vaga,vip=bool(rng.randrange(2)))
                estado = 'reservada'
            elif estado == 'reservada':
                if rng.randrange(3):
                    self.s.iniciar_estadia(placa,vaga,self.dono)
                    estado = 'ocupada'
                else:
                    r = next(r for r in self.s.consultar_ocupacao(titular=self.dono)['minhas_reservas'] if r['placa']==placa)
                    self.s.cancelar_reserva(self.dono,vaga,r['id'])
                    estado, vaga = 'livre', None
            else:
                c = self.s.consultar_cobranca(placa,'1.225')
                self.s.confirmar_pagamento(placa,'1.225',c,confirmado=True)
                self.assertEqual(self.invariante()['ocupada'],sum(e=='ocupada' for e,_ in estados.values()))
                self.s.concluir_saida(placa,'1.225',c)
                estado, vaga = 'livre', None
            estados[placa] = estado, vaga
            contagem = self.invariante()
            for situacao in ('reservada','ocupada'):
                self.assertEqual(contagem[situacao],sum(e==situacao for e,_ in estados.values()),passo)

    def test_revisao_de_entrada_exige_mesma_reserva_e_destinacao(self):
        op = self.s.opcoes_de_vaga(self.dono,'EV1',entrada=True)[0]
        expectativa = {k:op[k] for k in ('classificacao','vip','reserva_id','conferencia')}
        self.s.reservar_vaga(self.dono,'EV1',1,vip=True)
        with self.assertRaises(ErroDeNegocio):
            self.s.iniciar_estadia('EV1',1,self.dono,expectativa_uso=expectativa)
        self.assertEqual(self.invariante()['reservada'],1)

    def test_portal_pessoal_limita_consulta_e_conferencia_a_gestao(self):
        import re
        from secrets import token_urlsafe
        from web import create_app
        app = create_app(dict(TESTING=True,DADOS=self.arquivo.parent,HISTORICO=self.arquivo))
        self.addCleanup(app.extensions['escritor'].fechar)
        senha = token_urlsafe(24)
        app.extensions['autenticacao'].provisionar('titular', senha, 'cliente', self.outro)
        http = app.test_client()
        def campo(pagina, nome):
            return re.search(f'name="{nome}" value="([^"]+)"',pagina.text)[1]
        http.post('/entrar',data=dict(usuario='titular',senha=senha,csrf_token=campo(http.get('/entrar'),'csrf_token')))
        with http.session_transaction() as sessao:
            csrf = sessao['csrf']
        antes = self.arquivo.read_bytes()
        p = http.get('/cliente/disponibilidade?placa=COM&classificacao=pcd')
        self.assertIn('conferência administrativa válida',p.text)
        self.assertNotIn('EV1',p.text)
        self.assertNotIn(self.dono,p.text)
        self.assertEqual(http.get('/cliente/disponibilidade?placa=EV1').status_code,422)
        self.assertEqual(http.get('/gestao/vagas').status_code,403)
        self.assertEqual(http.post(f'/gestao/clientes/{self.outro}/autorizacoes',data={'csrf_token':csrf}).status_code,403)
        self.assertEqual(http.post('/gestao/vagas/117/carregador',data={'csrf_token':csrf}).status_code,403)
        self.assertNotIn('name="revisao"',http.get('/cliente/reservas/117?placa=COM').text)
        self.assertNotIn('name="revisao"',http.get('/cliente/reservas/1?placa=COM&vip=1').text)
        self.assertEqual(http.post('/cliente/reservas/1',data={}).status_code,400)
        self.assertEqual(self.arquivo.read_bytes(),antes)
