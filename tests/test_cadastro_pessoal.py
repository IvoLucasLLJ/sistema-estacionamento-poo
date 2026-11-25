"""Cadastro público com arquivos temporários, interrupções e retomada pelo titular."""
import re
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from secrets import token_urlsafe
from tempfile import TemporaryDirectory
from threading import Barrier
from unittest.mock import patch

from persistence import historico_json
from service.estacionamento_service import ErroDeInfraestrutura
from web import create_app


class CadastroPessoalTests(unittest.TestCase):
    def setUp(self):
        pasta = TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        raiz = Path(pasta.name)
        self.cfg = dict(TESTING=True, DADOS=raiz, CONTAS=raiz/'contas.json', HISTORICO=raiz/'historico.json')
        self.senha = token_urlsafe(26)
        self.abrir()

    def abrir(self):
        self.app = create_app(self.cfg)
        self.addCleanup(self.app.extensions['escritor'].fechar)
        self.auth = self.app.extensions['autenticacao']
        self.servico = self.app.extensions['estacionamento']
        self.http = self.app.test_client()

    def formulario(self):
        dados = self.http.get('/criar-conta').text
        ocultos = dict(re.findall(r'<input type="hidden" name="([^"]+)" value="([^"]+)"', dados))
        return dict(ocultos, usuario='nova.lia', nome='Lia Vale', senha=self.senha, confirmacao=self.senha)

    def login(self, senha):
        self.http.get('/entrar')
        with self.http.session_transaction() as sessao:
            csrf = sessao['csrf']
        return self.http.post('/entrar', data=dict(usuario='nova.lia', senha=senha, csrf_token=csrf))

    def test_cadastro_login_categoria_e_titularidade_do_homonimo(self):
        anterior = self.servico.cadastrar_cliente('vip', 'Lia Vale')['identificador']
        dados = self.formulario()
        resposta = self.http.post('/criar-conta', data=dados)
        self.assertEqual((resposta.status_code, resposta.location), (303, '/entrar'))
        self.assertIn('Conta criada.', self.http.get('/entrar').text)
        self.assertEqual(self.login(self.senha).location, '/cliente/')
        pessoal = self.auth.contas.por_usuario('nova.lia')
        cliente = self.servico.buscar_cliente(pessoal.identidade.cliente_id)
        self.assertNotEqual(cliente['identificador'], anterior)
        self.assertEqual((cliente['nome'], cliente['categoria'], pessoal.identidade.papel), ('Lia Vale','comum','cliente'))
        self.assertEqual(self.http.get('/gestao/').status_code, 403)
        self.assertEqual(self.http.get('/criar-conta').location, '/cliente/')
        for arquivo in (self.cfg['HISTORICO'], self.cfg['CONTAS']):
            self.assertNotIn(self.senha, arquivo.read_text(encoding='utf-8'))
        self.assertNotIn(pessoal.senha_hash, self.http.get('/cliente/').text)

    def test_campos_invalidos_e_senhas_nao_reexibidas(self):
        for alteracao in [dict(nome=' '), dict(nome='n' * 121), dict(usuario='a b'),
                          dict(senha='curta', confirmacao='curta'), dict(confirmacao='diferente')]:
            with self.subTest(campos=list(alteracao)):
                resposta = self.http.post('/criar-conta', data={**self.formulario(), **alteracao})
                self.assertEqual(resposta.status_code, 422)
                self.assertNotIn(self.senha, resposta.text)
        self.assertEqual(self.servico.listar_clientes(), [])

    def test_recusa_parametros_de_privilegio_associacao_e_nomes_reservados(self):
        for campo, valor in [('papel','gestao'), ('categoria','vip'), ('cliente_id','uuid'), ('placa','AV1')]:
            with self.subTest(campo=campo):
                self.assertEqual(self.http.post('/criar-conta', data={**self.formulario(), campo:valor}).status_code, 400)
        for usuario in ('MASTER.DEMO','gestao.demo','Cliente.Demo'):
            self.assertEqual(self.http.post('/criar-conta', data={**self.formulario(),'usuario':usuario}).status_code, 422)
        self.assertEqual(self.servico.listar_clientes(), [])

    def test_csrf_revisao_reenvio_e_duplicidade(self):
        dados = self.formulario()
        self.assertEqual(self.http.post('/criar-conta', data={**dados,'csrf_token':''}).status_code, 400)
        self.assertEqual(self.http.post('/criar-conta', data={**dados,'revisao':'outra'}).status_code, 409)
        self.assertEqual(self.http.post('/criar-conta', data=dados).status_code, 303)
        self.assertEqual(self.http.post('/criar-conta', data=dados).status_code, 409)
        self.assertEqual(self.http.post('/criar-conta', data={**self.formulario(),'usuario':'NOVA.LIA'}).status_code, 422)
        self.assertEqual(len(self.servico.listar_clientes()), 1)

    def test_concorrencia_reserva_um_nome_e_um_uuid(self):
        barreira = Barrier(2)
        def cadastrar(indice):
            barreira.wait(timeout=10)
            try:
                self.auth.cadastrar_pessoal(f'Titular {indice}', 'dupla', self.senha, self.senha)
            except ValueError as erro:
                return str(erro)
            return 'criada'
        with ThreadPoolExecutor(max_workers=2) as grupo:
            resultados = list(grupo.map(cadastrar, range(2)))
        self.assertCountEqual(resultados, ['criada','Nome de usuário já utilizado.'])
        self.assertEqual(len(self.servico.listar_clientes()), 1)

    def simular_interrupcao(self, escrita, depois):
        salvar = historico_json.salvar
        ordem = 0
        def interromper(*args, **kwargs):
            nonlocal ordem
            ordem += 1
            if ordem != escrita:
                return salvar(*args, **kwargs)
            if depois:
                salvar(*args, **kwargs)
            raise OSError('Interrupção simulada')
        dados = self.formulario()
        with patch('persistence.historico_json.salvar', side_effect=interromper):
            self.assertEqual(self.http.post('/criar-conta', data=dados).status_code, 503)
        self.app.extensions['escritor'].fechar()
        self.abrir()
        inicial = self.auth.contas.por_usuario('nova.lia')
        clientes = self.servico.listar_clientes()
        self.assertEqual(len(clientes), int(escrita > 2 or escrita == 2 and depois))
        if escrita == 1 and not depois:
            self.assertIsNone(inicial)
            self.assertEqual(self.login(self.senha).status_code, 401)
            self.assertEqual(self.http.post('/criar-conta', data=self.formulario()).status_code, 303)
        else:
            self.assertEqual(inicial.nome_pendente is None, escrita == 3 and depois)
            if inicial.nome_pendente:
                self.assertIsNone(self.auth.contas.por_id(inicial.identidade.id))
            self.assertEqual(self.login('senha incorreta').status_code, 401)
            self.assertEqual(self.servico.listar_clientes(), clientes)
        self.assertEqual(self.login(self.senha).location, '/cliente/')
        conta = self.auth.contas.por_usuario('nova.lia')
        if inicial:
            self.assertEqual(inicial.identidade, conta.identidade)
        self.assertIsNone(conta.nome_pendente)
        self.assertEqual([c['identificador'] for c in self.servico.listar_clientes()], [conta.identidade.cliente_id])

    def test_falha_antes_da_reserva(self):
        self.simular_interrupcao(1, False)

    def test_perda_da_resposta_da_reserva(self):
        self.simular_interrupcao(1, True)

    def test_falha_antes_de_persistir_cliente(self):
        self.simular_interrupcao(2, False)

    def test_falha_de_confirmacao_do_historico(self):
        self.simular_interrupcao(2, True)

    def test_falha_antes_de_ativar_conta(self):
        self.simular_interrupcao(3, False)

    def test_perda_da_resposta_da_ativacao(self):
        self.simular_interrupcao(3, True)

    def test_retomada_preserva_reserva_se_o_historico_ficar_indisponivel(self):
        with patch.object(self.servico, 'confirmar_cadastro_pessoal', side_effect=ErroDeInfraestrutura()):
            self.assertEqual(self.http.post('/criar-conta', data=self.formulario()).status_code, 503)
        self.cfg['HISTORICO'].write_bytes(b'{')
        self.assertEqual(self.login(self.senha).status_code, 503)
        self.assertEqual(self.cfg['HISTORICO'].read_bytes(), b'{')
        self.assertIsNotNone(self.auth.contas.por_usuario('nova.lia').nome_pendente)
