"""Matriz dos destinos de leitura conhecidos dos portais em uma aplicação de teste."""
import json
from pathlib import Path
from secrets import token_urlsafe
from tempfile import TemporaryDirectory
from unittest.mock import patch

from qa.formularios import token
from tests.test_contexto_acesso import demo_temporaria


def matriz(raiz):
    senha, master = token_urlsafe(), token_urlsafe()
    app = demo_temporaria(raiz, senha, senha_master=master)
    srv = app.extensions['estacionamento']
    titular = srv.cliente_do_veiculo('AV1')['identificador']
    estadia = next(e['estadia_id'] for e in srv.listar_estadias_ativas() if e['placa']=='AV1')
    auth = app.extensions['autenticacao']
    auth.provisionar('gestao.qa', senha, 'gestao')
    auth.cadastrar_pessoal('Outro titular','novo',senha,senha)
    rotas = {'gestao': ['', 'vagas', 'estadias', 'clientes', 'veiculos', f'clientes/{titular}',
                        'veiculos/AV1', 'entrada', f'estadias/{estadia}', f'estadias/{estadia}/saida',
                        f'estadias/{estadia}/pagamento', 'pagamentos','historico','relatorios'],
             'cliente':['','estadias','veiculos',f'estadias/{estadia}', f'estadias/{estadia}/comprovante',
                        'historico','disponibilidade','tarifas','perfil']}
    antes = app.config['HISTORICO'].read_bytes()
    linhas = []
    try:
        for usuario, papel in [(None,None), ('gestao.qa','gestao'), ('cliente.demo','cliente'),
                               ('gestao.demo','gestao'), ('gestao.demo','cliente'),
                               ('master.demo','gestao'), ('master.demo','cliente'), ('novo','cliente'),
                               ('cliente.demo','expirada'), ('cliente.demo','revogada')]:
            for area, caminhos in rotas.items():
                for caminho in caminhos:
                    # Cada recusa encerra a sessão. A próxima célula precisa de um login próprio.
                    if papel in ('expirada', 'revogada') or (area=='gestao' and caminho==''):
                        http = app.test_client()
                        http.get('/entrar')
                        if usuario:
                            login = http.post('/entrar',data=dict(usuario=usuario,
                                senha=master if usuario=='master.demo' else senha,csrf_token=token(http)))
                            assert login.status_code == 303
                        if papel=='cliente' and usuario in ('gestao.demo','master.demo'):
                            assert http.post('/ambiente',data=dict(ambiente='cliente',csrf_token=token(http))).status_code == 303
                    if papel == 'expirada':
                        with patch('web.seguranca.agora',return_value=10**10):
                            r=http.get(f'/{area}/{caminho}')
                        esperado=401
                    elif papel == 'revogada':
                        assert app.extensions['sessoes'].substituir(anterior=token(http))
                        r = http.get(f'/{area}/{caminho}')
                        esperado = 401
                    else:
                        r=http.get(f'/{area}/{caminho}')
                        if not usuario:
                            esperado=302
                        elif papel!=area:
                            esperado=403
                        elif caminho.endswith('/pagamento'):
                            esperado=409  # Nenhuma revisão de pagamento em curso.
                        elif caminho.endswith('/comprovante') or (usuario=='novo' and caminho.startswith('estadias/')):
                            esperado=404
                        else:
                            esperado=200
                    assert r.status_code==esperado and 'no-store' in r.cache_control.to_header(), (usuario,papel,area,caminho,r.status_code)
                    linhas.append([usuario,papel,area,caminho,esperado])
        assert app.config['HISTORICO'].read_bytes()==antes
    finally:
        app.extensions['escritor'].fechar()
    return linhas


if __name__ == '__main__':
    with TemporaryDirectory() as tmp:
        print(json.dumps(matriz(Path(tmp)),ensure_ascii=False))
