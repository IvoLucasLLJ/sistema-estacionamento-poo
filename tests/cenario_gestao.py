"""Cenário P0 do MOVE para execução em um diretório temporário vazio."""
import json
from datetime import datetime
from unittest.mock import patch
from uuid import UUID

from service.estacionamento_service import EstacionamentoService


def preparar_p0(arquivo):
    legado = dict(placa='LEG9', tipo='moto', vaga=8, horario_entrada='2026-11-18T08:00:00')
    registros = [dict(legado, acao='entrada'),
                 dict(legado, acao='saida', horario_saida='2026-11-18T08:01:00', horas=0.001, valor=0.005),
                 dict(legado, acao='entrada', horario_entrada='2026-11-19T09:00:00')]
    for numero, (nome, categoria) in enumerate([('Lia Vale', 'vip'), ('Lia Vale', 'comum'),
                                                ('Noa Reis', 'mensalista'), ('Iara Luz', 'comum')], 1):
        registros.append(dict(acao='cadastro_cliente', nome=nome, categoria=categoria,
                              identificador=str(UUID(int=numero))))
    with arquivo.open('x', encoding='utf-8') as destino:
        json.dump(registros, destino)
    s = EstacionamentoService(arquivo)
    for placa, tipo, modelo, dono in [('AV1','carro','Atlas',1), ('AM2','moto','Brisa',1),
                                      ('CB3','caminhao','Serra',2), ('NM4','moto','Lua',3),
                                      ('LV5','carro','Sol',None)]:
        s.cadastrar_veiculo(tipo, placa, modelo)
        if dono:
            s.vincular_veiculo(placa, str(UUID(int=dono)))
    # Fixar as saídas históricas permite testar filtros de data em qualquer dia de execução.
    with patch('model.estacionamento.datetime', wraps=datetime) as relogio:
        for placa, vaga, dono, entrada, saida in [('NM4', 1, 3, '09:00', '11:00'),
                                                 ('CB3', 4, 2, '11:00', '13:00')]:
            relogio.now.return_value = datetime.fromisoformat(f'2026-11-20T{entrada}:00-03:00')
            s.iniciar_estadia(placa, vaga, str(UUID(int=dono)))
            c = s.consultar_cobranca(placa, '2')
            if c['valor_centavos']:
                s.confirmar_pagamento(placa, '2', c, confirmado=True)
            relogio.now.return_value = datetime.fromisoformat(f'2026-11-20T{saida}:00-03:00')
            s.concluir_saida(placa, '2', c)
    s.iniciar_estadia('AV1', 2, str(UUID(int=1)))
    s.iniciar_estadia('AM2', 5, str(UUID(int=1)))
    return s
