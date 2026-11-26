"""Caracterização local delimitada. Medições em ms, sem aquecimento de cache forçado."""
import json
import math
import re
import statistics
import time
import tracemalloc
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from http.cookiejar import CookieJar
from pathlib import Path
from secrets import token_urlsafe
from tempfile import TemporaryDirectory
from threading import Barrier, Thread
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, ProxyHandler, build_opener

from werkzeug.serving import WSGIRequestHandler, make_server
from controller.controller import Controller
from service.estacionamento_service import EstacionamentoService
from tests.cenario_gestao import preparar_p0
from web import create_app


class Silencioso(WSGIRequestHandler):
    def log_request(self, *args):
        pass  # A campanha guarda métricas, sem cookies nem URLs de revisão.


def medir(f, *args):
    inicio = time.perf_counter()
    resultado = f(*args)
    return round(1000 * (time.perf_counter()-inicio), 3), resultado


def resumo(amostras):
    return dict(n=len(amostras), media_ms=round(statistics.mean(amostras), 3),
                mediana_ms=round(statistics.median(amostras), 3),
                p95_ms=sorted(amostras)[math.ceil(len(amostras)*.95)-1], max_ms=max(amostras))


def volumes(pasta):
    saida = {}
    for volume in (10, 100, 1000, 5000):
        arquivo = pasta / f'volume-{volume}.json'
        ctrl = Controller(arquivo)
        for n in range(volume):
            ctrl.cadastrar_veiculo('carro', f'QA{n}', 'Teste')
        ctrl.salvar()
        s = EstacionamentoService(arquivo)
        amostras = []
        for _ in range(5):
            ms, eventos = medir(s.consultar_historico)
            assert len(eventos) == volume and eventos[-1]['placa'] == f'QA{volume-1}'
            amostras.append(ms)
        tracemalloc.start()
        s.consultar_historico()
        _, pico = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        saida[volume] = dict(resumo(amostras), bytes_json=arquivo.stat().st_size, pico_python_bytes=pico)
    return saida


@contextmanager
def servidor(app):
    with make_server('127.0.0.1', 0, app, threaded=True, request_handler=Silencioso) as srv:
        thread = Thread(target=srv.serve_forever)
        thread.start()
        try:
            yield f'http://127.0.0.1:{srv.server_port}'
        finally:
            srv.shutdown()
            thread.join(10)
            app.extensions['escritor'].fechar()


def navegador(url, senha):
    http = build_opener(ProxyHandler({}), HTTPCookieProcessor(CookieJar()))
    def abrir(rota, dados=None):
        with http.open(url+rota, data=urlencode(dados).encode() if dados else None, timeout=10) as r:
            assert r.status == 200
            return r.read()
    csrf = re.search(rb'name="csrf_token" value="([^"]+)"', abrir('/entrar'))[1].decode()
    ms, pagina = medir(lambda: abrir('/entrar', dict(csrf_token=csrf, usuario='qa', senha=senha)))
    assert b'Faturamento' in pagina
    return ms, abrir


def tempo_ate_login(pasta):
    """Do início da fábrica até receber a página, após importar os módulos Python."""
    inicio = time.perf_counter()
    app = create_app(dict(DADOS=pasta, CONTAS=pasta / 'contas.json', HISTORICO=pasta / 'historico.json'))
    with servidor(app) as url:
        with build_opener(ProxyHandler({})).open(url + '/entrar', timeout=10) as resposta:
            assert resposta.status == 200 and b'name="csrf_token"' in resposta.read()
            return round((time.perf_counter() - inicio) * 1000, 3)


def campanha(pasta):
    arquivo = pasta / 'historico.json'
    s = preparar_p0(arquivo)
    cfg = dict(DADOS=pasta, HISTORICO=arquivo)
    ms, app = medir(lambda: create_app(cfg))
    saida = dict(fabrica_ms=ms, inicio_ate_login_ms=[
        tempo_ate_login(pasta / f'inicio-{i}') for i in range(3)])
    senha = token_urlsafe()
    app.extensions['autenticacao'].provisionar('qa', senha, 'gestao')
    saida['consultas_ms'] = {}
    for nome, f in [('ocupacao', s.consultar_ocupacao), ('historico', s.consultar_historico),
                    ('cotacao', lambda: s.consultar_cobranca('AV1','1.225'))]:
        saida['consultas_ms'][nome] = resumo([medir(f)[0] for _ in range(12)])
    with servidor(app) as url:
        clientes = [navegador(url, senha) for _ in range(8)]
        saida['login_com_dashboard'] = resumo([ms for ms, _ in clientes])
        saida['carga_http'] = {}
        saldo = arquivo.read_bytes()
        for n in (1, 2, 4, 8, 1):
            barreira = Barrier(n, timeout=10)
            def ler(indice, sincronizar=barreira):
                abrir = clientes[indice][1]
                sincronizar.wait()
                amostras = []
                for i in range(6):
                    rota = ('/gestao/','/gestao/historico','/gestao/relatorios')[i % 3]
                    ms, corpo = medir(abrir, rota)
                    assert b'<main' in corpo
                    amostras.append(ms)
                return amostras
            cpu = time.process_time()
            with ThreadPoolExecutor(n) as grupo:
                inicio = time.perf_counter()
                listas = list(grupo.map(ler, range(n)))
                tempo = (time.perf_counter() - inicio) * 1000
            amostras = [ms for lista in listas for ms in lista]
            chave = str(n) if str(n) not in saida['carga_http'] else '1-recuperacao'
            saida['carga_http'][chave] = dict(resumo(amostras), erros=0,
                req_s=round(len(amostras)*1000/tempo, 2), cpu_s=round(time.process_time()-cpu, 3))
        assert arquivo.read_bytes() == saldo
    rel = {}
    ids = s.cliente_do_veiculo('CB3')['identificador']
    fd = Path('/proc/self/fd')
    inicial = len(list(fd.iterdir())) if fd.exists() else None
    rss = {}
    for i in range(40):
        for nome, f in [('entrada',lambda: s.iniciar_estadia('CB3', 4, ids)),
                        ('consulta',lambda: s.consultar_cobranca('CB3','0'))]:
            ms, dados = medir(f)
            rel.setdefault(nome, []).append(ms)
        ms, _ = medir(s.concluir_saida, 'CB3', '0', dados)
        rel.setdefault('saida', []).append(ms)
        status = Path('/proc/self/status')
        if (i+1) % 10 == 0 and status.is_file():
            rss[i+1] = int(re.search(r'^VmRSS:\s+(\d+)', status.read_text(), re.M)[1])
    assert EstacionamentoService(arquivo).consultar_faturamento()['reais'] == '40.005'
    assert s.consultar_ocupacao()['ocupadas'] == 3 and not list(pasta.glob('*.tmp'))
    saida['resistencia'] = dict(ciclos=40, tempos={k:resumo(v) for k,v in rel.items()},
                               rss_kib_por_ciclo=rss, fd_inicio=inicial, fd_fim=len(list(fd.iterdir())) if fd.exists() else None)
    return saida


if __name__ == '__main__':
    with TemporaryDirectory() as tmp:
        pasta = Path(tmp)
        print(json.dumps(dict(historicos=volumes(pasta), operacoes=campanha(pasta)), indent=2))
