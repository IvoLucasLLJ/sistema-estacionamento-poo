"""Campanha determinística de transições, partições e interrupções reais de cadastro."""
import json
import multiprocessing
import os
import random
from collections import Counter
from pathlib import Path
from secrets import token_urlsafe
from tempfile import TemporaryDirectory
from unittest.mock import patch

from model.cliente import Cliente
from model.veiculo import Veiculo
from persistence import historico_json
from service.estacionamento_service import ErroDeInfraestrutura, ErroDeNegocio, EstacionamentoService
from web import create_app
from web.contas import normalizar_usuario


def ciclos(arquivo, semente):
    rng = random.Random(semente)
    s = EstacionamentoService(arquivo)
    ids = {p: s.cadastrar_cliente(cat, p)['identificador']
           for p, cat in [('A', 'vip'), ('B', 'mensalista'), ('C', 'comum')]}
    for placa in ids:
        s.cadastrar_veiculo('carro', placa, 'Modelo')
        s.vincular_veiculo(placa, ids[placa])
    ativas, cotacoes, concluidas = {}, {}, {}
    receita = 0
    contagem = Counter()
    for _ in range(280):
        p = rng.choice(list(ids))
        vaga = rng.randint(1, 3)
        operacao = rng.choice(['entrada', 'cotacao', 'pagamento', 'saida', 'reinicio', 'cancelar'])
        antes = arquivo.read_bytes()
        ativa = ativas.get(p)
        esperado = {'A': 613, 'B': 0, 'C': 1225}[p]
        cotacao = cotacoes.get(p)
        vigente = bool(ativa and cotacao and cotacao['estadia_id'] == ativa['id'])
        sucesso = {'entrada': not ativa and all(e['vaga'] != vaga for e in ativas.values()),
                   'cotacao': bool(ativa), 'pagamento': vigente and esperado > 0 and not ativa['paga'],
                   'saida': vigente and (not esperado or ativa['paga']),
                   'reinicio': True, 'cancelar': True}[operacao]
        try:
            if operacao == 'entrada':
                e = s.iniciar_estadia(p, vaga, ids[p])
                assert e['estadia_id'] == len(json.loads(antes)) + 1
                ativas[p] = dict(id=e['estadia_id'], vaga=vaga, paga=False)
            elif operacao == 'cotacao':
                cotacoes[p] = s.consultar_cobranca(p, '1.225')
                assert cotacoes[p]['valor_centavos'] == esperado
            elif operacao == 'pagamento':
                s.confirmar_pagamento(p, '1.225', cotacao, confirmado=True)
                ativa['paga'] = True
            elif operacao == 'saida':
                e = s.concluir_saida(p, '1.225', cotacao)
                concluidas[e['estadia_id']] = ids[p]
                receita += esperado
                del ativas[p]
            elif operacao == 'reinicio':
                s = EstacionamentoService(arquivo)
            # Cancelar uma revisão não exige chamada de escrita ao domínio.
        except ErroDeNegocio:
            assert not sucesso, (semente, _, p, operacao)
        else:
            assert sucesso, (semente, _, p, operacao)
        if not sucesso or operacao in ('reinicio', 'cotacao', 'cancelar'):
            assert arquivo.read_bytes() == antes
        contagem[(operacao, bool(sucesso))] += 1
        assert s.consultar_ocupacao() == dict(ocupadas=len(ativas), livres=10-len(ativas), total=10)
        assert {(e['placa'], e['vaga']) for e in s.listar_estadias_ativas()} == {(p, e['vaga']) for p,e in ativas.items()}
        assert s.consultar_faturamento()['centavos'] == receita
    for numero, titular in concluidas.items():
        e = s.consultar_estadia(numero)
        assert (e['cliente_id'], e['situacao']) == (titular, 'concluida')
    return {f'{o}/{s}': n for (o,s), n in sorted(contagem.items())}


def entradas(arquivo, semente):
    rng = random.Random(semente)
    resultados = Counter()
    alfabeto = 'Az-9α漢 é+.:,/_\t'
    for _ in range(240):
        texto = ''.join(rng.choices(alfabeto, k=rng.randrange(18)))
        for f in (normalizar_usuario, Cliente.normalizar_identificador, Veiculo.normalizar_placa):
            try:
                valor = f(texto)
            except ValueError:
                resultados['recusados'] += 1
            else:
                assert isinstance(valor, str) and valor == f(valor)
                resultados['aceitos'] += 1
    for dados in ([None], [{'acao': 'desconhecida'}], {}, 0, False, 'texto', [[[]]]):
        bruto = json.dumps(dados).encode()
        arquivo.write_bytes(bruto)
        try:
            EstacionamentoService(arquivo).consultar_ocupacao()
        except ErroDeInfraestrutura:
            assert arquivo.read_bytes() == bruto
        else:
            raise AssertionError(dados)
    return dict(resultados, historicos_invalidos=7)


def cadastrar_ate_queda(pasta, senha, escrita, depois):
    app = create_app(dict(DADOS=pasta, HISTORICO=pasta/'h.json'))
    salvar = historico_json.salvar
    ordem = 0

    def interromper(*args, **kwargs):
        nonlocal ordem
        ordem += 1
        if ordem == escrita and not depois:
            os._exit(74)
        retorno = salvar(*args, **kwargs)
        if ordem == escrita and depois:
            os._exit(74)
        return retorno
    with patch.object(historico_json, 'salvar', side_effect=interromper):
        app.extensions['autenticacao'].cadastrar_pessoal('Pessoa QA', 'pessoa', senha, senha)


def interrupcoes():
    for escrita in (1, 2, 3):
        for depois in (False, True):
            with TemporaryDirectory() as tmp:
                pasta, senha = Path(tmp), token_urlsafe()
                proc = multiprocessing.get_context('spawn').Process(
                    target=cadastrar_ate_queda, args=(pasta, senha, escrita, depois))
                proc.start()
                try:
                    proc.join(15)
                    assert proc.exitcode == 74
                finally:
                    if proc.is_alive():
                        proc.kill()
                        proc.join(5)
                    proc.close()
                app = create_app(dict(DADOS=pasta, HISTORICO=pasta/'h.json'))
                auth, srv = app.extensions['autenticacao'], app.extensions['estacionamento']
                reserva = auth.contas.por_usuario('pessoa')
                assert len(srv.listar_clientes()) == int(escrita == 3 or escrita == 2 and depois)
                assert auth.autenticar('pessoa', token_urlsafe()) is None
                if escrita == 1 and not depois:
                    assert reserva is None
                    auth.cadastrar_pessoal('Pessoa QA', 'pessoa', senha, senha)
                else:
                    assert reserva and (reserva.nome_pendente is None) == (escrita == 3 and depois)
                identidade = auth.autenticar('pessoa', senha)
                assert [c['identificador'] for c in srv.listar_clientes()] == [identidade.cliente_id]
                if reserva:
                    assert identidade == reserva.identidade


if __name__ == '__main__':
    with TemporaryDirectory() as tmp:
        pasta = Path(tmp)
        saida = {s: ciclos(pasta / f'h{s}.json', s) for s in (22023, 613, 20262)}
        saida['entradas'] = entradas(pasta / 'invalido.json', 613)
    interrupcoes()
    print(json.dumps(dict(sequencias=saida, interrupcoes=6), indent=2))
