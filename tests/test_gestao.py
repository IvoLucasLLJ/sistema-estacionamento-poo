import re
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from uuid import uuid4

from web import create_app


class GestaoTests(TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        raiz = Path(tmp.name)
        self.config = dict(TESTING=True, DADOS=raiz, HISTORICO=raiz/'hist.json',
                           CONTAS=raiz/'acessos.json', SECRET_KEY=None, SESSION_COOKIE_SECURE=False)
        self.app = create_app(self.config)
        self.addCleanup(self.app.extensions['escritor'].fechar)
        self.s = self.app.extensions['estacionamento']
        self.http = self.app.test_client()
        self.senha = uuid4().hex
        self.app.extensions['autenticacao'].provisionar('gestor', self.senha, 'gestao')
        self.login('gestor')

    def login(self, usuario):
        r = self.http.get('/entrar')
        self.http.post('/entrar', data=dict(usuario=usuario, senha=self.senha,
                                            csrf_token=self.campo(r, 'csrf_token')))
        with self.http.session_transaction() as sessao:
            self.csrf = sessao['csrf']

    @staticmethod
    def campo(resposta, nome):
        return re.search(fr'name="{nome}" value="([^"]+)"', resposta.text)[1]

    def enviar(self, url, **dados):
        return self.http.post(url, data=dict(csrf_token=self.csrf, **dados))

    def test_mapa_ativas_e_dashboard(self):
        self.assertEqual(self.http.get('/gestao/vagas').status_code, 200)
        self.assertIn('Nenhuma estadia', self.http.get('/gestao/estadias').text)
        self.assertEqual(self.http.get('/gestao/').text.count('class="livre"'), 10)

    def cadastrar(self, recurso, **dados):
        url = '/gestao/' + recurso
        revisao = self.campo(self.http.get(url), 'revisao')
        return self.enviar(url, revisao=revisao, **dados)

    def test_clientes_homonimos_e_reenvio(self):
        revisao = self.campo(self.http.get('/gestao/clientes'), 'revisao')
        dados = dict(nome='Lia Vale', categoria='vip', revisao=revisao)
        self.assertEqual(self.enviar('/gestao/clientes', **dados).status_code, 303)
        self.assertEqual(self.enviar('/gestao/clientes', **dados).status_code, 409)
        self.cadastrar('clientes', nome='Lia Vale', categoria='comum')
        self.assertEqual(len({c['identificador'] for c in self.s.listar_clientes()}), 2)
        self.assertEqual(self.http.get('/gestao/clientes?q=lia').text.count('>Lia Vale<'), 2)

    def test_placa_duplicada_e_vinculo(self):
        c = self.s.cadastrar_cliente('comum', 'Lia')['identificador']
        dados = dict(tipo='carro', placa='av-1', modelo='Atlas')
        self.assertEqual(self.cadastrar('veiculos', **dados).status_code, 303)
        self.assertEqual(self.cadastrar('veiculos', **dados).status_code, 422)
        self.assertEqual(self.enviar('/gestao/vinculos', placa='AV1', cliente_id=c).status_code, 303)
        self.assertEqual(self.s.cliente_do_veiculo('AV1')['identificador'], c)

    def preparar_entrada(self, placa='AV1', vaga=2, categoria='vip'):
        cliente = self.s.cadastrar_cliente(categoria, 'Lia Vale')['identificador']
        self.s.cadastrar_veiculo('carro', placa, 'Atlas')
        self.s.vincular_veiculo(placa, cliente)
        resposta = self.http.get('/gestao/entrada', query_string=dict(
            cliente_id=cliente, placa=placa, vaga=vaga, revisar=1))
        self.assertEqual(resposta.status_code, 200)
        return cliente, self.campo(resposta, 'revisao')

    def test_entrada_revalida_vaga_disputada(self):
        _, primeira = self.preparar_entrada()
        _, segunda = self.preparar_entrada('BB2')
        self.s.iniciar_estadia('AV1', 2, self.s.cliente_do_veiculo('AV1')['identificador'])
        r = self.enviar('/gestao/entrada', revisao=segunda)
        self.assertEqual(r.status_code, 409)
        self.assertIn('BB2', r.text)
        self.assertEqual(len(self.s.listar_estadias_ativas()), 1)

    def cotar(self, numero=22, horas='1,225'):
        return self.http.get(f'/gestao/estadias/{numero}/saida', query_string={'horas': horas})

    def ticket_pagamento(self, numero=22, horas='1,225'):
        r = self.cotar(numero, horas)
        link = re.search(r'href="([^"]+/pagamento\?revisao=[^"]+)"', r.text)[1]
        return self.campo(self.http.get(link), 'revisao')

    def test_ciclo_financeiro_figma_e_reabertura(self):
        from tests.cenario_gestao import preparar_p0
        from service.estacionamento_service import EstacionamentoService
        preparar_p0(self.config['HISTORICO'])
        def estado(ocupadas, pendentes, reais):
            leitor = EstacionamentoService(self.config['HISTORICO'])
            self.assertEqual(leitor.consultar_ocupacao(), dict(ocupadas=ocupadas, livres=10-ocupadas,total=10))
            self.assertEqual(len(leitor.listar_pagamentos_abertos()), pendentes)
            self.assertEqual(leitor.consultar_faturamento()['reais'], reais)
        base = '/gestao/estadias/22'
        estado(3, 0, '40.005')
        c = self.s.consultar_cobranca('AV1', '1.225')
        from decimal import Decimal
        self.assertEqual((Decimal(c['tarifa_base']), Decimal(c['desconto']), c['valor_centavos']),
                         (Decimal('12.25'), Decimal('6.125'), 613))
        revisao = self.ticket_pagamento()
        res = self.enviar(base+'/pagamento', revisao=revisao, decisao='confirmar', valor_centavos='1')
        self.assertEqual(res.status_code, 303)
        estado(3, 1, '40.005')
        self.assertEqual(self.enviar(base+'/pagamento', revisao=revisao, decisao='confirmar').status_code, 409)
        r = self.http.get(base)
        self.assertIn('Pagamento confirmado.', r.text)
        chave = self.campo(r, 'revisao')
        self.assertEqual(self.enviar(base+'/concluir', revisao=chave).status_code, 303)
        self.assertEqual(self.enviar(base+'/concluir', revisao=chave).status_code, 409)
        estado(2, 0, '46.135')
        self.assertEqual(self.s.consultar_estadia(22)['cobranca']['valor_centavos'], 613)
        self.assertEqual(self.s.consultar_estadia(23)['situacao'], 'ativa')

    def test_isencao_por_categoria_duracao_ou_arredondamento(self):
        for idx, (categoria, horas) in enumerate([('mensalista','2'), ('comum','0'), ('vip','0,0001')]):
            _, token = self.preparar_entrada('T'+str(idx), 1, categoria)
            r = self.enviar('/gestao/entrada', revisao=token)
            numero = int(r.location.rsplit('/',1)[1])
            cotacao = self.cotar(numero, horas)
            self.assertIn('Concluir saída isenta', cotacao.text)
            self.assertEqual(self.enviar(r.location+'/concluir', revisao=self.campo(cotacao,'revisao')).status_code,303)
            self.assertEqual(self.s.consultar_estadia(numero)['pagamento'], 'isento')

    def test_cotacao_antiga_nao_atinge_nova_estadia_da_placa(self):
        from tests.cenario_gestao import preparar_p0
        preparar_p0(self.config['HISTORICO'])
        antigo = self.ticket_pagamento()
        c = self.s.consultar_cobranca('AV1','0')
        self.s.concluir_saida('AV1','0',c)
        novo = self.s.iniciar_estadia('AV1',2,self.s.cliente_do_veiculo('AV1')['identificador'])
        res = self.enviar('/gestao/estadias/22/pagamento',revisao=antigo,decisao='confirmar')
        self.assertEqual(res.status_code, 409)
        self.assertIn('/gestao/estadias/22?recuperar=1',res.text)
        self.assertEqual(self.s.consultar_estadia(novo['estadia_id'])['pagamento'],'sem_confirmacao')

    def test_historico_periodo_e_dados_legados(self):
        from tests.cenario_gestao import preparar_p0
        preparar_p0(self.config['HISTORICO'])
        eventos = self.http.get('/gestao/historico?acao=saida&evento=2')
        self.assertIn('Evento 2 · Saída legada', eventos.text)
        self.assertIn('R$ 0,01', eventos.text)
        self.assertNotIn('Lia Vale', eventos.text)
        rel = self.http.get('/gestao/relatorios?fim=2026-11-19')
        self.assertIn('R$ 40,01', rel.text)
        self.assertIn('R$ 0,01', rel.text)
        self.assertEqual(self.http.get('/gestao/relatorios?inicio=2026-12-01&fim=2026-11-01').status_code,422)

    def test_relatorio_e_projecao_historica(self):
        from web.eventos import eventos_identificados, RelatorioSaidas
        eventos = eventos_identificados([dict(acao='saida',placa='ANT',tipo='carro',vaga=3,
            horas=1,valor='10.005',horario_entrada='2020-10-28',horario_saida='2020-10-29',
            cliente_id='terceiro',categoria='vip',estadia_id=99,valor_centavos=0)])
        self.assertNotIn('cliente_id', eventos[0])
        self.assertNotIn('valor_centavos', eventos[0])
        r = RelatorioSaidas.do_periodo(eventos)
        self.assertEqual((r.pagas,r.isentas,r.legadas,r.por_categoria),(0,0,1,(('legado',1),)))
        self.assertEqual(str(r.receita),'10.005')

    def test_cobertura_modelos_e_filtros(self):
        from tests.cenario_gestao import preparar_p0
        preparar_p0(self.config['HISTORICO'])
        c = self.s.cliente_do_veiculo('AV1')['identificador']
        for rota in ('','vagas?vaga=8','clientes','clientes/'+c,'veiculos','veiculos/AV1',
                     'entrada?cliente_id='+c,'estadias?q=AV1','estadias/22/saida','pagamentos',
                     'historico','estadias/22','relatorios'):
            with self.subTest(rota=rota):
                self.assertEqual(self.http.get('/gestao/'+rota).status_code, 200)
        self.assertTrue(self.ticket_pagamento())
        mapa = self.http.get('/gestao/vagas?vaga=8').text
        self.assertIn('Legada', mapa)
        self.assertNotIn('href="/gestao/estadias/None', mapa)
        self.assertNotIn('AM2',self.http.get('/gestao/estadias?q=AV1').text)

    def test_papel_e_csrf_em_todas_as_escritas(self):
        from tests.cenario_gestao import preparar_p0
        preparar_p0(self.config['HISTORICO'])
        caminhos = ['clientes','veiculos','vinculos','entrada','estadias/22/pagamento','estadias/22/concluir']
        for caminho in caminhos:
            self.assertEqual(self.http.post('/gestao/'+caminho).status_code,400)
        self.app.extensions['autenticacao'].provisionar('pessoal', self.senha,'cliente',
                                                      self.s.cliente_do_veiculo('AV1')['identificador'])
        self.enviar('/sair')
        self.login('pessoal')
        antes = self.config['HISTORICO'].read_bytes()
        for caminho in caminhos:
            self.assertEqual(self.enviar('/gestao/'+caminho).status_code,403)
        self.assertEqual(self.config['HISTORICO'].read_bytes(),antes)

    def test_resultados_incertos_recuperam_estadia_original(self):
        from unittest.mock import patch
        from controller.controller import Controller
        from tests.cenario_gestao import preparar_p0
        preparar_p0(self.config['HISTORICO'])
        salvar = Controller.salvar
        def perder_resposta(ctrl):
            salvar(ctrl)
            raise OSError('falha simulada após persistência')
        for acao in ['pagamento','concluir']:
            chave = self.ticket_pagamento() if acao=='pagamento' else self.campo(self.http.get('/gestao/estadias/22'),'revisao')
            with patch.object(Controller,'salvar',autospec=True,side_effect=perder_resposta) as gravar:
                res = self.enviar('/gestao/estadias/22/'+acao, revisao=chave, decisao='confirmar')
                self.assertEqual(res.status_code,503)
                self.assertIn('Consultar estado', res.text)
                url = '/gestao/estadias/22?recuperar=1'
                self.assertIn(url, res.text)
                r = self.http.get(url)
                self.assertIn('Pagamento confirmado.' if acao=='pagamento' else 'Comprovante acadêmico', r.text)
                gravar.assert_called_once()
        self.assertEqual(self.s.consultar_faturamento()['reais'],'46.135')

    def test_cancelar_e_horas_invalidas_preservam_historico(self):
        from tests.cenario_gestao import preparar_p0
        preparar_p0(self.config['HISTORICO'])
        antes = self.config['HISTORICO'].read_bytes()
        for horas in ['NaN','inf','-1','dois']:
            self.assertEqual(self.cotar(22,horas).status_code,422)
        chave = self.ticket_pagamento()
        resp = self.enviar('/gestao/estadias/22/pagamento', revisao=chave, decisao='cancelar')
        self.assertEqual(resp.status_code,303)
        self.assertEqual(self.enviar('/gestao/estadias/22/pagamento', revisao=chave, decisao='confirmar').status_code,409)
        self.assertEqual(self.config['HISTORICO'].read_bytes(),antes)

    def test_revisao_pertence_a_sessao_e_a_operacao_e_expira(self):
        from unittest.mock import patch
        from web.revisoes import Revisoes
        revisoes = Revisoes(validade=10)
        with patch('web.revisoes.monotonic', return_value=100):
            token = revisoes.emitir('sessao-a', 'pagamento/22', {'valor_centavos':613})
            self.assertIsNone(revisoes.obter(token, 'sessao-b', 'pagamento/22', consumir=True))
            self.assertIsNone(revisoes.obter(token, 'sessao-a', 'saida/22', consumir=True))
            copia = revisoes.obter(token, 'sessao-a', 'pagamento/22')
            copia['valor_centavos'] = 0
            self.assertEqual(revisoes.obter(token, 'sessao-a', 'pagamento/22')['valor_centavos'],613)
        with patch('web.revisoes.monotonic', return_value=110):
            self.assertIsNone(revisoes.obter(token, 'sessao-a', 'pagamento/22', consumir=True))

    def test_cadastro_concorrente_do_mesmo_formulario(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        token = self.campo(self.http.get('/gestao/clientes'), 'revisao')
        nome_cookie = self.app.config['SESSION_COOKIE_NAME']
        cookie = self.http.get_cookie(nome_cookie).value
        juntos = Barrier(2, timeout=5)
        def postar():
            navegador = self.app.test_client()
            navegador.set_cookie(nome_cookie, cookie)
            juntos.wait()
            return navegador.post('/gestao/clientes', data=dict(csrf_token=self.csrf, revisao=token,
                                  nome='Lia Vale', categoria='vip')).status_code
        with ThreadPoolExecutor(max_workers=2) as executor:
            resultados = [executor.submit(postar) for _ in range(2)]
            self.assertEqual(sorted(r.result(timeout=10) for r in resultados), [303,409])
        self.assertEqual(len(self.s.listar_clientes()),1)

    def test_entrada_sem_vinculo_lotacao_e_indisponibilidade_do_veiculo(self):
        c = self.s.cadastrar_cliente('comum','Iara Luz')['identificador']
        url = '/gestao/entrada'
        self.assertIn('Cliente sem veículos', self.http.get(url, query_string={'cliente_id':c}).text)
        self.assertEqual(self.http.get(url, query_string={'cliente_id':str(uuid4())}).status_code,422)
        self.s.cadastrar_veiculo('moto','EX','Sol')
        r = self.http.get(url, query_string=dict(cliente_id=c,placa='EX',vaga=1,revisar=1))
        self.assertEqual(r.status_code,422)
        self.s.vincular_veiculo('EX',c)
        self.s.iniciar_estadia('EX',1,c)
        self.assertIn('já estão estacionados',self.http.get(url,query_string={'cliente_id':c}).text)
        for vaga in range(2,11):
            placa = f'EX{vaga}'
            self.s.cadastrar_veiculo('moto',placa,'Sol')
            self.s.vincular_veiculo(placa,c)
            self.s.iniciar_estadia(placa,vaga,c)
        self.assertIn('Estacionamento lotado', self.http.get(url, query_string={'cliente_id':c}).text)

    def test_entrada_falha_antes_da_substituicao(self):
        from unittest.mock import patch
        from persistence.historico_json import FalhaAntesDaSubstituicao
        _, chave = self.preparar_entrada()
        antes = self.config['HISTORICO'].read_bytes()
        with patch('repository.estacionamento_repository.historico_json.salvar',
                   side_effect=FalhaAntesDaSubstituicao()):
            r = self.enviar('/gestao/entrada', revisao=chave)
        self.assertEqual(r.status_code, 503)
        self.assertNotIn('Entrada registrada.',r.text)
        self.assertEqual(self.config['HISTORICO'].read_bytes(), antes)
        self.assertFalse(self.s.listar_estadias_ativas())
