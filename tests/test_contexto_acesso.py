"""Alternância com as contas reais de um cenário inteiramente temporário."""
import json
import re
from pathlib import Path
from secrets import token_urlsafe
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from web import create_app
from web.demonstracao import configuracao, criar_cenario, provisionar_demonstracao


def demo_temporaria(pasta, senha, *, senha_master=None):
    app = create_app(configuracao(pasta))
    titular = criar_cenario(app.extensions['estacionamento'])
    auth = app.extensions['autenticacao']
    auth.provisionar('gestao.demo', senha, 'gestao')
    auth.provisionar('cliente.demo', senha, 'cliente', titular)
    auth.provisionar('master.demo', senha_master or token_urlsafe(20), 'gestao')
    provisionar_demonstracao(app, titular)
    return app


class ContextoAcessoTests(TestCase):
    def setUp(self):
        temporaria = TemporaryDirectory()
        self.addCleanup(temporaria.cleanup)
        self.pasta = Path(temporaria.name)
        self.senha = token_urlsafe(20)
        self.senha_master = token_urlsafe(20)
        self.app = demo_temporaria(self.pasta, self.senha, senha_master=self.senha_master)
        self.addCleanup(self.app.extensions['escritor'].fechar)
        self.http = self.app.test_client()
        self.srv = self.app.extensions['estacionamento']

    def sessao(self):
        with self.http.session_transaction() as sessao:
            return dict(sessao)

    def login(self, usuario, senha=None, **campos):
        self.http.get('/entrar')
        return self.http.post('/entrar', data={'usuario': usuario, 'senha': senha or self.senha,
                                               'csrf_token': self.sessao()['csrf'], **campos})

    def alternar(self, ambiente, **campos):
        return self.http.post('/ambiente', data={'csrf_token': self.sessao()['csrf'],
                                                'ambiente': ambiente, **campos})

    def test_master_escolhe_cliente_no_login_e_retorna_sem_trocar_de_conta(self):
        outro = self.srv.cliente_do_veiculo('NM4')['identificador']
        resposta = self.login('master.demo', self.senha_master, ambiente='cliente', cliente_id=outro)
        self.assertEqual((resposta.status_code, resposta.location), (303, '/cliente/'))
        conta = self.sessao()['conta']
        self.assertNotEqual(self.sessao()['conta_pessoal_ativa'], conta)
        pessoal = self.http.get('/cliente/').text
        for proprio in ('master.demo', 'Olá, Lia Vale', 'AV1', 'AM2'):
            self.assertIn(proprio, pessoal)
        for externo in (outro, 'NM4', 'Faturamento'):
            self.assertNotIn(externo, pessoal)
        self.assertEqual(self.http.get('/gestao/').status_code, 403)
        self.assertEqual(self.alternar('gestao').location, '/gestao/')
        self.assertNotIn('conta_pessoal_ativa', self.sessao())
        self.assertEqual(self.alternar('cliente').location, '/cliente/')
        self.assertEqual(self.sessao()['conta'], conta)

    def test_escolha_inicial_respeita_o_papel_e_so_abre_sessao_quando_autorizada(self):
        self.app.config['VINCULOS_PORTAIS'] = {}
        arquivos = [self.app.config[chave] for chave in ('HISTORICO', 'CONTAS')]
        antes = [p.read_bytes() for p in arquivos]
        for usuario, ambiente, vedado in [('cliente.demo', 'cliente', 'gestao'), ('gestao.demo', 'gestao', 'cliente')]:
            with self.subTest(usuario=usuario):
                self.assertEqual(self.login(usuario, ambiente=vedado).status_code, 403)
                self.assertNotIn('conta', self.sessao())
                self.assertEqual(self.http.get(f'/{vedado}/').location, '/entrar')
                self.assertEqual(self.login(usuario, ambiente=ambiente).location, f'/{ambiente}/')
                self.assertEqual(self.http.get(f'/{ambiente}/').status_code, 200)
                self.assertNotIn('conta_pessoal_ativa', self.sessao())
                self.http.post('/sair', data={'csrf_token': self.sessao()['csrf']})
        self.assertEqual(antes, [p.read_bytes() for p in arquivos])

    def test_escolha_inicial_exige_credenciais_csrf_e_um_unico_destino_valido(self):
        for campos in ({'ambiente': ''}, {'ambiente': '/gestao/'}, {'ambiente': ['cliente', 'gestao']},
                       {'ambiente': 'gestao', 'csrf_token': ''}):
            with self.subTest(campos=campos):
                self.assertEqual(self.login('master.demo', self.senha_master, **campos).status_code, 400)
                self.assertNotIn('conta', self.sessao())
        resposta = self.login('master.demo', self.senha, ambiente='cliente')
        self.assertEqual(resposta.status_code, 401)
        self.assertIn('Usuário ou senha inválidos.', resposta.text)
        self.assertNotIn('conta', self.sessao())

    def test_duas_areas_mesma_autenticacao_prazo_e_titularidade(self):
        self.assertEqual(self.login('gestao.demo').location, '/gestao/')
        anterior = self.sessao()
        self.assertEqual(self.http.get('/cliente/').status_code, 403)
        outro = self.srv.cliente_do_veiculo('NM4')['identificador']
        resposta = self.alternar('cliente', cliente_id=outro)
        self.assertEqual((resposta.status_code, resposta.location), (303, '/cliente/'))
        self.assertEqual(self.http.get('/').location, '/cliente/')
        pessoal = self.http.get('/cliente/').text
        self.assertIn('Olá, Lia Vale', pessoal)
        self.assertIn('AV1', pessoal)
        for externo in ('NM4', outro, 'Faturamento', '/gestao/'):
            self.assertNotIn(externo, pessoal)
        self.assertEqual(self.http.get('/gestao/').status_code, 403)
        terceiros = next(e for e in self.srv.listar_estadias_ativas() if e['placa'] == 'NM4')
        for sufixo in ('', '/comprovante'):
            rota = f"/cliente/estadias/{terceiros['estadia_id']}{sufixo}"
            resposta = self.http.get(rota)
            self.assertEqual(resposta.status_code, 404)
            self.assertEqual(resposta.data, self.http.get('/cliente/estadias/99999' + sufixo).data)
        atual = self.sessao()
        self.assertEqual((atual['conta'], atual['expira']), (anterior['conta'], anterior['expira']))
        self.assertNotEqual(atual['csrf'], anterior['csrf'])
        self.assertEqual(self.alternar('gestao', csrf_token=anterior['csrf']).status_code, 400)
        self.assertEqual(self.alternar('gestao').location, '/gestao/')
        self.assertEqual(self.http.get('/gestao/').status_code, 200)

    def test_pessoal_direta_sem_elevacao_e_gestor_sem_vinculo(self):
        self.login('cliente.demo')
        self.assertNotIn('menu-ambiente', self.http.get('/cliente/').text)
        self.assertEqual(self.alternar('gestao').status_code, 403)
        self.assertEqual(self.http.get('/gestao/').status_code, 403)
        self.http.post('/sair', data={'csrf_token': self.sessao()['csrf']})
        self.app.config['VINCULOS_PORTAIS'] = {}
        self.login('gestao.demo')
        self.assertNotIn('menu-ambiente', self.http.get('/gestao/').text)
        self.assertEqual(self.alternar('cliente').status_code, 403)

    def test_seletor_exige_post_csrf_e_destino_conhecido(self):
        self.login('gestao.demo')
        self.assertEqual(self.http.get('/ambiente').status_code, 405)
        self.assertEqual(self.http.post('/ambiente', data={'ambiente': 'cliente'}).status_code, 400)
        self.assertEqual(self.alternar('/gestao/').status_code, 400)
        self.assertEqual(self.http.get('/').location, '/gestao/')

    def test_revogacao_ou_troca_de_titular_exige_nova_autenticacao(self):
        auth = self.app.extensions['autenticacao']
        outro = auth.provisionar('outra.pessoa', self.senha, 'cliente',
                                 self.srv.cliente_do_veiculo('NM4')['identificador'])
        originais = self.app.config['VINCULOS_PORTAIS']
        for novo in (None, outro.id):
            with self.subTest(revogacao=novo is None):
                self.app.config['VINCULOS_PORTAIS'] = originais
                self.login('gestao.demo')
                self.alternar('cliente')
                self.app.config['VINCULOS_PORTAIS'] = {self.sessao()['conta']: novo} if novo else {}
                self.assertEqual(self.http.get('/cliente/').status_code, 401)
                self.assertNotIn('conta', self.sessao())

    def test_logout_e_expiracao_encerram_os_dois_contextos(self):
        for expirar in (False, True):
            with self.subTest(expirar=expirar):
                self.login('gestao.demo')
                self.alternar('cliente')
                if expirar:
                    with patch('web.seguranca.agora', return_value=10**10):
                        self.assertEqual(self.alternar('gestao').status_code, 401)
                else:
                    self.assertEqual(self.http.post('/sair', data={'csrf_token': self.sessao()['csrf']}).location,
                                     '/entrar')
                for area in ('/gestao/', '/cliente/'):
                    self.assertEqual(self.http.get(area).location, '/entrar')

    def test_reabertura_da_demo_reutiliza_contas_sem_regravar_dados(self):
        arquivos = [self.app.config[chave] for chave in ('HISTORICO', 'CONTAS')]
        antes = [p.read_bytes() for p in arquivos]
        nova = create_app(configuracao(self.pasta))
        self.assertFalse(nova.config['VINCULOS_PORTAIS'])
        provisionar_demonstracao(nova, self.srv.cliente_do_veiculo('AV1')['identificador'])
        self.assertEqual(nova.config['VINCULOS_PORTAIS'], self.app.config['VINCULOS_PORTAIS'])
        self.assertEqual(antes, [p.read_bytes() for p in arquivos])

    def test_master_inicia_na_gestao_alterna_para_lia_e_encerra_os_dois_portais(self):
        self.assertEqual(self.login('master.demo').status_code, 401)
        self.assertEqual(self.login('master.demo', self.senha_master).location, '/gestao/')
        inicial = self.sessao()
        self.assertEqual(self.http.post('/ambiente', data={'ambiente': 'cliente'}).status_code, 400)
        terceiro = self.srv.cliente_do_veiculo('NM4')['identificador']
        self.assertEqual(self.alternar('cliente', cliente_id=terceiro).location, '/cliente/')
        pagina = self.http.get('/cliente/')
        self.assertIn('Olá, Lia Vale', pagina.text)
        self.assertIn('master.demo', pagina.text)
        self.assertNotIn(terceiro, pagina.text)
        self.assertNotIn('NM4', pagina.text)
        self.assertNotIn('Faturamento', pagina.text)
        self.assertEqual(self.http.get('/gestao/').status_code, 403)
        self.assertEqual(self.http.post('/gestao/clientes', data={'csrf_token': self.sessao()['csrf']}).status_code, 403)
        atual = self.sessao()
        self.assertEqual(atual['conta'], inicial['conta'])
        self.assertEqual(atual['expira'], inicial['expira'])
        self.assertEqual(self.alternar('gestao').location, '/gestao/')
        self.assertEqual(self.http.post('/sair', data={'csrf_token': self.sessao()['csrf']}).location, '/entrar')
        for rota in ('/gestao/', '/cliente/'):
            self.assertEqual(self.http.get(rota).location, '/entrar')

    def test_master_restrita_a_demo_mesmo_com_registro_valido_em_armazenamento_operacional(self):
        pasta = self.pasta / 'operacao'
        op = create_app(dict(DADOS=pasta, HISTORICO=pasta/'historico.json'))
        self.addCleanup(op.extensions['escritor'].fechar)
        auth = op.extensions['autenticacao']
        with self.assertRaisesRegex(ValueError, 'reservada'):
            auth.provisionar(' MASTER.DEMO ', self.senha_master, 'gestao')
        with self.assertRaisesRegex(ValueError, 'ambiente isolado'):
            provisionar_demonstracao(op, self.app.config['TITULAR_DEMO'])
        self.assertFalse(op.config['CONTAS'].exists())
        # Representa a importação acidental de contas fictícias preexistentes.
        op.config['CONTAS'].write_bytes(self.app.config['CONTAS'].read_bytes())
        master = auth.contas.por_usuario('master.demo').identidade
        op.config['VINCULOS_PORTAIS'] = self.app.config['VINCULOS_PORTAIS']
        op.config['TITULAR_DEMO'] = self.app.config['TITULAR_DEMO']
        http = op.test_client()
        http.get('/entrar')
        with http.session_transaction() as sessao:
            csrf = sessao['csrf']
        resposta = http.post('/entrar', data=dict(usuario='Master.Demo', senha=self.senha_master, csrf_token=csrf))
        self.assertEqual(resposta.status_code, 401)
        self.assertIn('Usuário ou senha inválidos', resposta.text)
        # A própria guarda deve recusar uma sessão anterior que identifique essa conta.
        with http.session_transaction() as sessao:
            sessao.update(conta=master.id, expira=10**10)
        self.assertEqual(http.get('/gestao/').status_code, 401)
        self.assertEqual(http.get('/cliente/').location, '/entrar')

    def test_master_nao_pode_trocar_titular_pessoal(self):
        self.login('master.demo', self.senha_master)
        self.alternar('cliente')
        self.app.config['TITULAR_DEMO'] = self.srv.cliente_do_veiculo('NM4')['identificador']
        self.assertEqual(self.http.get('/cliente/estadias').status_code, 401)
        self.assertNotIn('conta', self.sessao())

    def test_troca_descarta_revisao_financeira_sem_afetar_outra_sessao(self):
        self.login('master.demo', self.senha_master)
        anterior = self.sessao()['csrf']
        estadia = next(e['estadia_id'] for e in self.srv.listar_estadias_ativas() if e['placa'] == 'AV1')
        base = f'/gestao/estadias/{estadia}'
        cotacao = self.http.get(base + '/saida?horas=1,225')
        link = re.search(r'href="([^"]+/pagamento\?revisao=[^"]+)"', cotacao.text)[1]
        revisao = re.search(r'name="revisao" value="([^"]+)"', self.http.get(link).text)[1]
        revisoes = self.app.extensions['revisoes']
        outra = revisoes.emitir('outra-sessao', 'cliente')
        self.assertIsNotNone(revisoes.obter(revisao, anterior, f'pagamento/{estadia}'))
        self.alternar('cliente')
        self.assertIsNone(revisoes.obter(revisao, anterior, f'pagamento/{estadia}'))
        self.alternar('gestao')
        self.assertEqual(self.http.post(base + '/pagamento', data=dict(decisao='confirmar', revisao=revisao,
                                  csrf_token=self.sessao()['csrf'])).status_code, 409)
        self.assertEqual(self.srv.listar_pagamentos_abertos(), [])
        self.assertEqual(revisoes.obter(outra, 'outra-sessao', 'cliente'), {})

    def test_instalacao_existente_pede_so_a_senha_da_master_e_reabre_sem_prompt(self):
        cfg = configuracao(self.pasta / 'anterior')
        app = create_app(cfg)
        titular = criar_cenario(app.extensions['estacionamento'])
        auth = app.extensions['autenticacao']
        auth.provisionar('gestao.demo', self.senha, 'gestao')
        auth.provisionar('cliente.demo', self.senha, 'cliente', titular)
        anteriores = json.loads(cfg['CONTAS'].read_bytes())
        estado = [cfg['HISTORICO'], cfg['DADOS'] / 'sessao.key']
        antes = [p.read_bytes() for p in estado]
        with patch('sys.stdin.isatty', return_value=False), self.assertRaisesRegex(ValueError, 'master.demo'):
            provisionar_demonstracao(app, titular)
        with patch('sys.stdin.isatty', return_value=True), patch('click.prompt', return_value=self.senha_master) as prompt:
            provisionar_demonstracao(app, titular)
        prompt.assert_called_once_with('Senha', hide_input=True, confirmation_prompt='Repita a senha')
        contas = cfg['CONTAS'].read_bytes()
        registros = json.loads(contas)
        self.assertEqual(registros[:-1], anteriores)
        self.assertEqual(registros[-1]['usuario'], 'master.demo')
        self.assertTrue(registros[-1]['senha_hash'].startswith('scrypt:'))
        self.assertNotIn(self.senha_master.encode(), contas)
        nova = create_app(cfg)
        with patch('sys.stdin.isatty', return_value=False):
            provisionar_demonstracao(nova, titular)
        self.assertEqual(nova.extensions['autenticacao'].autenticar('master.demo', self.senha_master).id,
                         registros[-1]['id'])
        self.assertEqual(contas, cfg['CONTAS'].read_bytes())
        self.assertEqual(antes, [p.read_bytes() for p in estado])
