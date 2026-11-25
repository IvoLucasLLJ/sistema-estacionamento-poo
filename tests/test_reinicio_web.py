"""Integração HTTP antes e depois de reiniciar a aplicação com o mesmo armazenamento."""
import re
from pathlib import Path
from secrets import token_urlsafe
from tempfile import TemporaryDirectory
from unittest import TestCase

from tests.cenario_gestao import preparar_p0
from web import create_app


class ReinicioWebTests(TestCase):
    def test_perde_revisoes_mas_recupera_pagamento_e_saida_pelo_id_original(self):
        pasta = self.enterContext(TemporaryDirectory())
        arquivo = Path(pasta) / 'historico.json'
        servico = preparar_p0(arquivo)
        config = dict(DADOS=pasta, HISTORICO=arquivo, CONTAS=Path(pasta) / 'contas.json',
                      TESTING=True, SECRET_KEY=None, SESSION_COOKIE_SECURE=False)
        base = '/gestao/estadias/22'
        app = create_app(config)
        self.addCleanup(app.extensions['escritor'].fechar)
        senha = token_urlsafe(32)
        app.extensions['autenticacao'].provisionar('gestor.qa', senha, 'gestao')
        http = app.test_client()
        http.get('/entrar')
        with http.session_transaction() as sessao:
            csrf = sessao['csrf']
        login = http.post('/entrar', data=dict(usuario='gestor.qa', senha=senha, csrf_token=csrf))
        self.assertEqual(login.status_code, 303)
        with http.session_transaction() as sessao:
            csrf = sessao['csrf']

        def reiniciar(anterior, cliente):
            cookie = cliente.get_cookie(anterior.config['SESSION_COOKIE_NAME'])
            anterior.extensions['escritor'].fechar()
            nova = create_app(config)
            self.addCleanup(nova.extensions['escritor'].fechar)
            navegador = nova.test_client()
            navegador.set_cookie(cookie.key, cookie.value)
            return nova, navegador

        cotacao = http.get(base + '/saida?horas=1,225')
        link = re.search(r'href="([^"]+/pagamento\?revisao=[^"]+)"', cotacao.text)[1]
        revisao = re.search(r'name="revisao" value="([^"]+)"', http.get(link).text)[1]
        pago = http.post(base + '/pagamento', data=dict(revisao=revisao, csrf_token=csrf,
                                                        decisao='confirmar'))
        self.assertEqual(pago.status_code, 303)

        def revisao_de_saida(cliente):
            pagina = cliente.get(base + '?recuperar=1')
            self.assertIn('Pagamento confirmado.', pagina.text)
            return re.search(r'name="revisao" value="([^"]+)"', pagina.text)[1]

        pendente = revisao_de_saida(http)
        antes = arquivo.read_bytes()
        app, http = reiniciar(app, http)
        self.assertEqual(http.get(base + '/concluir').status_code, 405)
        recusada = http.post(base + '/concluir', data=dict(revisao=pendente, csrf_token=csrf))
        self.assertEqual(recusada.status_code, 409)
        self.assertIn(base + '?recuperar=1', recusada.text)
        self.assertEqual(arquivo.read_bytes(), antes)
        self.assertEqual(servico.consultar_faturamento()['reais'], '40.005')
        nova = revisao_de_saida(http)
        self.assertEqual(http.post(base + '/concluir', data=dict(revisao=nova, csrf_token=csrf)).status_code, 303)

        depois = arquivo.read_bytes()
        app, http = reiniciar(app, http)
        self.assertIn('Comprovante acadêmico', http.get(base + '?recuperar=1').text)
        self.assertEqual(servico.consultar_faturamento()['reais'], '46.135')
        self.assertEqual(servico.listar_pagamentos_abertos(), [])
        self.assertEqual(arquivo.read_bytes(), depois)
