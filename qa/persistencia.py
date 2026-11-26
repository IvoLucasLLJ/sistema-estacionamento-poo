"""Falhas delimitadas na publicação de uma versão e uso concorrente de revisões locais."""
import json
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack, contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier
from unittest.mock import Mock, patch

from persistence import historico_json as disco
from service.estacionamento_service import ErroDeInfraestrutura, EstacionamentoService
from web.revisoes import Revisoes


def falha_na_escrita(arquivo, etapa):
    abrir = disco.temporario_privado
    substituir = disco.substituir_arquivo
    original = disco.salvar(arquivo, [], disco.ler(arquivo)[1])
    esperado = [{'acao':'cadastro','placa':'QA','tipo':'carro','modelo':'Teste'}]

    @contextmanager
    def temporario(destino):
        if etapa == 'criar':
            raise OSError('criação temporária indisponível')
        with abrir(destino) as (caminho, saida):
            yield caminho, saida

    def trocar(origem, destino):
        if etapa == 'antes_replace':
            raise OSError('substituição indisponível')
        substituir(origem,destino)
        if etapa == 'depois_replace':
            raise OSError('resposta perdida')

    with ExitStack() as injecao:
        injecao.enter_context(patch.object(disco, 'temporario_privado', temporario))
        injecao.enter_context(patch.object(disco,'substituir_arquivo',trocar))
        if etapa in ('write','flush'):
            @contextmanager
            def com_falha(destino):
                with abrir(destino) as (caminho, saida):
                    fluxo = Mock(wraps=saida)
                    getattr(fluxo,etapa).side_effect = OSError('E/S interrompida')
                    yield caminho, fluxo
            injecao.enter_context(patch.object(disco,'temporario_privado',com_falha))
        if etapa == 'fsync':
            injecao.enter_context(patch.object(disco.os,'fsync',side_effect=OSError('disco')))
        try:
            disco.salvar(arquivo, esperado, original)
        except OSError as exc:
            falha = type(exc).__name__
        else:
            raise AssertionError(etapa)
    if etapa == 'depois_replace':
        assert disco.ler(arquivo)[0] == esperado
    else:
        assert arquivo.read_bytes() == original
    assert not list(arquivo.parent.glob('*.tmp'))
    return falha


def publicacao(pasta):
    arquivo = pasta / 'historico.json'
    casos = {etapa: falha_na_escrita(arquivo, etapa)
             for etapa in ('criar', 'write', 'flush', 'fsync', 'antes_replace', 'depois_replace')}
    for bruto in (b'\xff',b'[',b'{"a":false}', b'[[[[[]]]]]',b'[null]',b'[NaN]'):
        arquivo.write_bytes(bruto)
        try:
            EstacionamentoService(arquivo).consultar_historico()
        except ErroDeInfraestrutura:
            assert arquivo.read_bytes() == bruto
        else:
            raise AssertionError(bruto)
    return casos


def revisoes():
    r = Revisoes(validade=10, capacidade=3)
    with patch('web.revisoes.monotonic',return_value=100):
        chaves = [r.emitir('A','entrada',{'n':n}) for n in range(4)]
        assert r.obter(chaves[0],'A','entrada') is None
        assert r.obter(chaves[1],'A','entrada')=={'n':1}
        dupla = Barrier(2,timeout=10)
        def consumir(_):
            dupla.wait()
            return r.obter(chaves[-1],'A','entrada',consumir=True)
        with ThreadPoolExecutor(2) as grupo:
            resultados = list(grupo.map(consumir,range(2)))
        assert resultados.count(None)==1 and resultados.count({'n':3})==1
    with patch('web.revisoes.monotonic',return_value=110):
        assert r.obter(chaves[1],'A','entrada') is None


if __name__ == '__main__':
    with TemporaryDirectory() as tmp:
        casos = publicacao(Path(tmp))
    revisoes()
    print(json.dumps(dict(escritas=casos, arquivos_invalidos=6, disputa='um consumo'), ensure_ascii=False))
