"""Regressões do histórico entre o terminal, o Repository e a aplicação web."""
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from secrets import token_urlsafe
from tempfile import TemporaryDirectory
from unittest import TestCase

from controller.controller import Controller
from tests.cenario_gestao import preparar_p0
from web import create_app


class HorariosLegadosTests(TestCase):
    def setUp(self):
        pasta = TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.raiz = Path(pasta.name)
        self.arquivo = self.raiz / 'historico.json'

    def gravar_par(self, inicio, fim):
        entrada = dict(acao='entrada', tipo='moto', placa='LEG9', vaga=8, horario_entrada=inicio)
        saida = dict(entrada, acao='saida', horario_saida=fim, horas=0.001, valor=0.005)
        self.arquivo.write_text(json.dumps([entrada, saida]), encoding='utf-8')

    def test_retirada_no_terminal_reabre_na_gestao_com_ids_e_valores_originais(self):
        preparar_p0(self.arquivo)
        anteriores = json.loads(self.arquivo.read_bytes())
        self.assertIsNone(datetime.fromisoformat(anteriores[2]['horario_entrada']).tzinfo)
        processo = subprocess.run(
            [sys.executable, '-B', str(Path(__file__).resolve().parents[1] / 'main.py')],
            cwd=self.raiz, env={**os.environ, 'MOVE_HISTORICO': str(self.arquivo)},
            input='7\nLEG9\n2\n4\n', capture_output=True, text=True, timeout=10, check=True)
        self.assertIn('Tarifa: R$ 10,00', processo.stdout)
        gravado = self.arquivo.read_bytes()
        eventos = json.loads(gravado)
        self.assertEqual(eventos[:-1], anteriores)
        self.assertEqual(eventos[-1]['horario_entrada'], anteriores[2]['horario_entrada'])
        self.assertIsNotNone(datetime.fromisoformat(eventos[-1]['horario_saida']).tzinfo)
        self.assertEqual((eventos[-1]['horas'], eventos[-1]['valor']), (2, 10))
        self.assertEqual(Controller(self.arquivo).consultar_historico(), eventos)

        app = create_app(dict(TESTING=True, DADOS=self.raiz, HISTORICO=self.arquivo,
                              SECRET_KEY=None, SESSION_COOKIE_SECURE=False))
        self.addCleanup(app.extensions['escritor'].fechar)
        servico = app.extensions['estacionamento']
        self.assertEqual(servico.consultar_ocupacao(), dict(total=10, ocupadas=2, livres=8))
        self.assertEqual(servico.consultar_faturamento()['reais'], '50.005')
        self.assertEqual([servico.consultar_estadia(i)['placa'] for i in (22, 23)], ['AV1', 'AM2'])
        http = app.test_client()
        senha = token_urlsafe(32)
        app.extensions['autenticacao'].provisionar('gestor.qa', senha, 'gestao')
        http.get('/entrar')
        with http.session_transaction() as sessao:
            token = sessao['csrf']
        self.assertEqual(http.post('/entrar', data=dict(usuario='gestor.qa', senha=senha,
                                                       csrf_token=token)).status_code, 303)
        pagina = http.get('/gestao/historico?evento=24')
        self.assertEqual(pagina.status_code, 200)
        self.assertIn('Evento 24 · Saída legada', pagina.text)
        self.assertIn('R$ 50,01', http.get('/gestao/').text)
        self.assertEqual(self.arquivo.read_bytes(), gravado)

    def test_recupera_pares_legados_sem_mudar_os_horarios_ou_inferir_duracao(self):
        for inicio, fim in [
            ('2024-01-01T10:00', '2024-01-01T11:00'),
            ('2024-01-01T10:00-03:00', '2024-01-01T10:00-03:00'),
            ('2024-01-01T10:00+03:00', '2024-01-01T06:00-02:00'),
            ('2024-01-01T10:00', '2024-01-01T08:00Z'),
            ('2024-01-01T10:00Z', '2024-01-01T08:00'),
        ]:
            with self.subTest(inicio=inicio, fim=fim):
                self.gravar_par(inicio, fim)
                antes = self.arquivo.read_bytes()
                ctrl = Controller(self.arquivo)
                self.assertEqual(ctrl.consultar_historico(), json.loads(antes))
                self.assertEqual(ctrl.relatorio(), dict(livres=10, ocupadas=0, faturamento=0.005))
                self.assertEqual(self.arquivo.read_bytes(), antes)

    def test_recusa_ordem_comprovadamente_invertida_e_preserva_arquivo(self):
        for inicio, fim in [
            ('2024-01-01T11:00', '2024-01-01T10:59'),
            ('2024-01-01T10:00Z', '2024-01-01T09:59Z'),
            ('2024-01-01T10:00-03:00', '2024-01-01T11:59+01:00'),
            ('2024-01-02T10:00', '2024-01-01T10:00Z'),
            ('2024-01-02T10:00Z', '2024-01-01T10:00'),
        ]:
            with self.subTest(inicio=inicio, fim=fim):
                self.gravar_par(inicio, fim)
                antes = self.arquivo.read_bytes()
                with self.assertRaisesRegex(ValueError, 'Saída anterior à entrada'):
                    Controller(self.arquivo)
                self.assertEqual(self.arquivo.read_bytes(), antes)

    def test_retirada_rejeita_inversao_antes_de_liberar_a_vaga(self):
        self.gravar_par('9999-12-31T12:00', '9999-12-31T13:00')
        entrada = json.loads(self.arquivo.read_bytes())[:1]
        self.arquivo.write_text(json.dumps(entrada), encoding='utf-8')
        ctrl = Controller(self.arquivo)
        with self.assertRaisesRegex(ValueError, 'Saída anterior à entrada'):
            ctrl.retirar_por_placa('LEG9', 1)
        self.assertEqual(ctrl.consultar_historico(), entrada)
        self.assertEqual(ctrl.relatorio(), dict(livres=9, ocupadas=1, faturamento=0))
