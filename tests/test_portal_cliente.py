import json
from pathlib import Path
from secrets import token_urlsafe
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from uuid import UUID

from service.estacionamento_service import ErroDeInfraestrutura
from tests.cenario_gestao import preparar_p0
from model.vaga import DISTRIBUICAO_HISTORICA
from web import create_app


class PortalClienteTests(TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        raiz = Path(tmp.name)
        self.arquivo = raiz / 'historico.json'
        preparar_p0(self.arquivo)
        self.app = create_app(dict(TESTING=True, DISTRIBUICAO=DISTRIBUICAO_HISTORICA, DADOS=raiz, HISTORICO=self.arquivo,
                                   CONTAS=raiz / 'contas.json', SECRET_KEY=None, SESSION_COOKIE_SECURE=False))
        self.addCleanup(self.app.extensions['escritor'].fechar)
        self.s = self.app.extensions['estacionamento']
        self.http = self.app.test_client()
        self.senha = token_urlsafe(24)
        self.entrar(1)

    def entrar(self, numero, navegador=None):
        http = navegador or self.http
        usuario = f'conta{numero}'
        papel = 'cliente' if numero else 'gestao'
        dono = str(UUID(int=numero)) if numero else None
        self.app.extensions['autenticacao'].provisionar(usuario, self.senha, papel, dono)
        with http.session_transaction() as sessao:
            sessao.clear()
        http.get('/entrar')
        with http.session_transaction() as sessao:
            csrf = sessao['csrf']
        res = http.post('/entrar', data=dict(usuario=usuario, senha=self.senha, csrf_token=csrf))
        self.assertEqual(res.status_code, 303)

    def pagina(self, caminho, **params):
        res = self.http.get('/cliente/' + caminho, query_string=params)
        self.assertEqual(res.status_code, 200)
        return res.text

    def test_variantes_de_inicio_ativas_e_frota(self):
        for caminho in ('', 'estadias', 'veiculos'):
            html = self.pagina(caminho, cliente_id=str(UUID(int=2)))
            for texto in ('AV1', 'AM2', '/cliente/estadias/22', '/cliente/estadias/23'):
                self.assertIn(texto, html)
            for texto in ('CB3', 'LEG9', 'NM4', 'R$ 40,01', 'R$ 0,00', '/gestao/'):
                self.assertNotIn(texto, html)
        self.entrar(4)
        self.assertIn('Nenhum veículo vinculado', self.pagina('veiculos'))
        self.assertIn('Nenhuma estadia ativa', self.pagina('estadias'))

    def test_falha_parcial_conserva_blocos_independentes(self):
        with patch.object(self.s, 'listar_estadias_ativas', side_effect=ErroDeInfraestrutura()):
            html = self.pagina('')
            self.assertIn('Estadias indisponíveis', html)
            self.assertIn('AV1', html)
            self.assertNotIn('Nenhuma estadia ativa', html)
            self.assertIn('Situação indisponível', self.pagina('veiculos'))
        with patch.object(self.s, 'consultar_ocupacao', side_effect=ErroDeInfraestrutura()):
            self.assertIn('Disponibilidade indisponível', self.pagina(''))

    def test_historico_por_entrada_original_e_filtros(self):
        html = self.pagina('historico')
        self.assertIn('Estadia 22', html)
        self.assertIn('Estadia 23', html)
        for dado in ['LEG9', 'CB3', 'Lia Demo', 'NM4', 'R$ 40,01', str(UUID(int=2))]:
            self.assertNotIn(dado, html)
        self.assertNotIn('Estadia 23', self.pagina('historico', placa='AV1'))
        self.assertIn('Nenhuma utilização corresponde', self.pagina('historico', estado='paga'))
        self.assertIn('Nenhuma utilização corresponde', self.pagina('historico', fim='1900-01-01'))
        resposta = self.http.get('/cliente/historico?inicio=2026-12-01&fim=2026-01-01')
        self.assertEqual(resposta.status_code, 422)

    def test_comprovantes_de_terceiro_e_ausentes_equivalentes(self):
        for rota in ('/cliente/estadias/{}', '/cliente/estadias/{}/comprovante'):
            alheio = self.http.get(rota.format(19))
            ausente = self.http.get(rota.format(9999))
            self.assertEqual((alheio.status_code, alheio.data), (404, ausente.data))
            self.assertEqual(alheio.headers['Cache-Control'], 'no-store')
        self.assertEqual(self.http.get('/cliente/estadias/22/comprovante').status_code, 404)
        self.entrar(2)
        self.assertIn('R$ 40,00', self.pagina('estadias/19/comprovante'))
        self.assertNotIn('AV1', self.pagina('historico'))

    def test_mensalista_ve_isencao_e_imprime_comprovante_proprio(self):
        self.entrar(3)
        html = self.pagina('estadias/17/comprovante')
        for texto in ['Comprovante acadêmico', 'Saída isenta', 'R$ 0,00', 'Sem valor fiscal', 'Noa Reis']:
            self.assertIn(texto, html)
        self.assertIn('Estadia 17', self.pagina('historico', estado='isenta'))
        self.assertNotIn('Concluir saída', html)

    def test_disponibilidade_agregada_lotacao_e_falha(self):
        html = self.pagina('disponibilidade')
        self.assertIn('30% de ocupação', html)
        for dado in ('AV1', 'AM2', 'LEG9', 'Vaga 002', 'Lia Vale', 'Faturamento'):
            self.assertNotIn(dado, html)
        dono = str(UUID(int=1))
        for vaga in (1, 3, 4, 6, 7, 9, 10):
            placa = f'LOT{vaga}'
            self.s.cadastrar_veiculo('moto', placa, 'Sol')
            self.s.vincular_veiculo(placa, dono)
            self.s.iniciar_estadia(placa, vaga, dono)
        self.assertIn('Estacionamento lotado', self.pagina('disponibilidade'))
        with patch.object(self.s, 'consultar_ocupacao', side_effect=ErroDeInfraestrutura()):
            resposta = self.http.get('/cliente/disponibilidade')
        self.assertEqual(resposta.status_code, 503)
        self.assertIn('Repetir consulta', resposta.text)
        self.assertNotIn('0 vagas', resposta.text)

    def test_catalogo_coincide_com_as_tres_subclasses(self):
        from decimal import Decimal
        from model.carro import Carro
        from model.caminhao import Caminhao
        from model.moto import Moto

        tarifas = self.s.consultar_tarifas()
        self.assertEqual(tarifas, {'carro': 10, 'moto': 5, 'caminhao': 20})
        for classe in (Carro, Moto, Caminhao):
            v = classe('REF', 'Teste')
            self.assertEqual(tarifas[classe.__name__.lower()], v.calcular_tarifa(Decimal(1)))
        self.assertIn('50% de desconto', self.pagina('tarifas'))
        self.assertIn(str(UUID(int=1)), self.pagina('perfil'))

    def test_conta_de_gestao_sem_portal_pessoal_e_sessao_expirada(self):
        admin = self.app.test_client()
        self.entrar(0, admin)
        for rota in ('', 'estadias', 'veiculos', 'disponibilidade', 'tarifas', 'historico',
                     'estadias/19', 'estadias/19/comprovante', 'perfil'):
            with self.subTest(rota=rota):
                self.assertEqual(admin.get('/cliente/' + rota, query_string={'cliente_id': str(UUID(int=2))}).status_code, 403)
        with patch('web.seguranca.agora', return_value=10**10):
            r = self.http.get('/cliente/estadias/22')
            self.assertEqual(r.status_code, 401)
            self.assertNotIn('AV1', r.text)
        self.assertEqual(self.http.get('/cliente/estadias/22').location, '/entrar')

    def test_titular_atual_nao_herda_saida_legada_da_placa(self):
        # O arquivo importado termina antes da nova ocupação legada, com a saída antiga já concluída.
        eventos = json.loads(self.arquivo.read_text(encoding='utf-8'))
        cadastro = next(e for e in eventos if e.get('identificador') == str(UUID(int=1)))
        self.arquivo.write_text(json.dumps([*eventos[:2], cadastro]))
        self.s.vincular_veiculo('LEG9', str(UUID(int=1)))
        self.assertIn('LEG9', self.pagina('veiculos'))
        self.assertNotIn('LEG9', self.pagina('historico'))
        self.assertEqual(self.http.get('/cliente/estadias/3').status_code, 404)

    def test_leituras_nao_escrevem_e_falha_integral_nao_exibe_vazio(self):
        self.entrar(2)
        antes = self.arquivo.read_bytes()
        for rota in ('', 'estadias', 'veiculos', 'disponibilidade', 'tarifas', 'historico',
                     'estadias/19', 'estadias/19/comprovante', 'perfil'):
            html = self.pagina(rota)
            for privado in ('AV1', 'AM2', 'LEG9', 'Noa Reis', 'Iara Luz', '/gestao/', 'scrypt:'):
                self.assertNotIn(privado, html, rota)
        self.assertEqual(self.arquivo.read_bytes(), antes)
        self.arquivo.write_bytes(b'{')
        resposta = self.http.get('/cliente/historico')
        self.assertEqual(resposta.status_code, 503)
        for falso in ('Nenhuma utilização', 'Traceback', str(self.arquivo)):
            self.assertNotIn(falso, resposta.text)

    def test_integracao_gestao_cliente_p0_p1_p2(self):
        import re
        from service.estacionamento_service import EstacionamentoService

        admin = self.app.test_client()
        self.entrar(0, admin)
        with admin.session_transaction() as sessao:
            csrf = sessao['csrf']
        url = '/gestao/estadias/22'
        def revisao(pagina):
            return re.search(r'name="revisao" value="([^"]+)"', pagina.text)[1]

        p0 = self.pagina('estadias')
        self.assertNotIn('R$ ', p0)
        self.assertIn('Estadia 23', p0)
        self.assertIn('R$ 40,01', admin.get('/gestao/').text)
        consulta = admin.get(url + '/saida?horas=1,225')
        confirmar = re.search(r'href="([^"]+/pagamento\?revisao=[^"]+)"', consulta.text)[1]
        r = admin.post(url + '/pagamento', data=dict(csrf_token=csrf, revisao=revisao(admin.get(confirmar)),
                                                    decisao='confirmar'))
        self.assertEqual(r.status_code, 303)
        self.assertIn('R$ 6,13', self.pagina('estadias'))
        self.assertIn('ainda estacionado na vaga 002', self.pagina('estadias/22'))
        self.assertIn('30% de ocupação', self.pagina('disponibilidade'))
        self.assertIn('R$ 40,01', admin.get('/gestao/').text)
        self.assertEqual(admin.post(url + '/concluir', data=dict(
            csrf_token=csrf, revisao=revisao(admin.get(url)))).status_code, 303)
        p2 = self.pagina('estadias')
        self.assertIn('Estadia 23', p2)
        self.assertNotIn('AV1', p2)
        self.assertIn('Estadia 22', self.pagina('historico', estado='paga'))
        self.assertIn('20% de ocupação', self.pagina('disponibilidade'))
        comprovante = self.pagina('estadias/22/comprovante')
        for texto in ('<dt>Desconto</dt>', 'R$ 6,13', 'R$ 12,25', '1,225 h'):
            self.assertIn(texto, comprovante)
        self.assertEqual(comprovante.count('<dd>R$ 6,13</dd>'), 2)
        self.assertNotRegex(comprovante, r'R\$ [\d.]+,\d{3}')
        self.assertNotIn('R$ 46,14', comprovante)
        self.assertIn('R$ 46,14', admin.get('/gestao/').text)
        leitor = EstacionamentoService(self.arquivo)
        self.assertEqual(leitor.consultar_estadia(22)['cobranca']['valor_centavos'], 613)

    def test_objetos_de_consulta_isolam_titulares_e_descartam_alteracoes_locais(self):
        from web.consultas_pessoais import ConsultasPessoais

        lia = ConsultasPessoais(self.s, str(UUID(int=1)))
        homonima = ConsultasPessoais(self.s, str(UUID(int=2)))
        pessoal = lia.historico()
        self.assertEqual([e['estadia_id'] for e in pessoal], [23, 22])
        self.assertEqual([e['estadia_id'] for e in homonima.historico()], [19])
        pessoal[0]['placa'] = 'LOCAL'
        self.assertEqual(lia.historico()[0]['placa'], 'AM2')
        self.assertEqual({v['placa'] for v in lia.veiculos()}, {'AV1', 'AM2'})
        self.assertFalse(homonima.ativas())
