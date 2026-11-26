"""Partições de formulários e recuperação de erros em clientes de teste descartáveis."""
import json
import random
import re
from pathlib import Path
from secrets import token_urlsafe
from tempfile import TemporaryDirectory

from tests.test_contexto_acesso import demo_temporaria


def token(http):
    with http.session_transaction() as sessao:
        return sessao['csrf']


def entrada(raiz):
    senha = token_urlsafe()
    app = demo_temporaria(raiz, senha)
    http = app.test_client()
    rng = random.Random(1225)
    antes = app.config['HISTORICO'].read_bytes()
    contas = app.config['CONTAS'].read_bytes()
    n = 0
    try:
        for i in range(72):
            pagina = http.get('/criar-conta')
            campos = dict(re.findall(r'<input type="hidden" name="([^"]+)" value="([^"]+)"', pagina.text))
            dados = dict(campos, nome='Cliente QA', usuario='teste', senha=senha, confirmacao=senha)
            campo, valor = rng.choice([('nome', ' ' * rng.randint(0,8)), ('nome', 'É' * rng.randint(121,200)),
                ('usuario', 'Íris '+str(i)), ('usuario',''), ('confirmacao',''), ('usuario','x'*65)])
            dados[campo] = valor
            resposta = http.post('/criar-conta', data=dados)
            assert resposta.status_code == 422 and senha not in resposta.text
            n += 1
        for usuario in ('', '  ', 'é', 'não cadastrado', 'a'*65):
            assert http.post('/entrar',data=dict(usuario=usuario, senha=senha, csrf_token=token(http))).status_code == 401
            n += 1
        assert http.post('/entrar', data=dict(usuario='gestao.demo', senha=senha, csrf_token=token(http))).status_code == 303
        s = app.extensions['estacionamento']
        numero = next(e['estadia_id'] for e in s.listar_estadias_ativas() if e['placa']=='AV1')
        for _ in range(20):
            componente = ''.join(rng.choices('abcç ', k=rng.randrange(2,16)))
            for rota, query in [('/gestao/relatorios',dict(inicio=componente)),
                                (f'/gestao/estadias/{numero}/saida',dict(horas=componente))]:
                assert http.get(rota,query_string=query).status_code == 422
                n += 1
        assert app.config['HISTORICO'].read_bytes()==antes and app.config['CONTAS'].read_bytes()==contas
    finally:
        app.extensions['escritor'].fechar()
    return dict(semente=1225, formularios=n)


if __name__ == '__main__':
    with TemporaryDirectory() as tmp:
        print(json.dumps(entrada(Path(tmp))))
