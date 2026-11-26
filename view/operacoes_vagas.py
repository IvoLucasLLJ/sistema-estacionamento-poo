"""Comandos administrativos da interface terminal, sob a trava do processo."""
from decimal import Decimal
from model.uso_vaga import CLASSIFICACOES, GRUPOS, MOTORES
from model.vaga import VAGAS_POR_SETOR


def operacao(ctrl, opcao):
    est = ctrl.estacionamento
    if opcao == '8':
        setor = int(input('Setor (a partir de 1): '))
        inicio = (setor - 1) * VAGAS_POR_SETOR
        if not 0 <= inicio < len(est.vagas):
            raise ValueError('Setor inexistente.')
        for v in est.vagas[inicio:inicio + VAGAS_POR_SETOR]:
            equipamento = (' · carregador operacional' if v.carregador.disponivel else
                           ' · carregador indisponível') if v.carregador else ''
            print(f'{v.numero:03d} · {CLASSIFICACOES[v.classificacao]} · {v.estado}{equipamento}',
                  '· VIP' if v.vip else '')
    elif opcao == '9':
        categoria = input('Categoria (comum/vip/mensalista): ')
        cliente = ctrl.cadastrar_cliente(categoria, input('Nome fictício: '))
        print('UUID:', cliente.identificador)
    elif opcao == '10':
        v = ctrl.cadastrar_veiculo(input('Tipo: '), input('Placa: '), input('Modelo: '),
                                   input(f'Motorização ({"/".join(MOTORES)}): '))
        print('Veículo cadastrado:', v.placa)
    elif opcao == '11':
        ctrl.vincular_veiculo(input('Placa: '), input('UUID do cliente: '))
    elif opcao == '12':
        cliente, placa = input('UUID do titular: '), input('Placa: ')
        grupo = input(f'Grupo ({"/".join(GRUPOS)}): ')
        numero = est.conferir_autorizacao(cliente, placa, grupo, input('Beneficiário (condutor/passageiro): '),
                                          input('Conferência fictícia (fisica/digital/administrativa): '),
                                          input('Validade AAAA-MM-DD: '))
        print('Autorização:', numero)
    elif opcao == '13':
        est.revogar_autorizacao(input('UUID do titular: '), int(input('Número da autorização: ')))
    elif opcao == '14':
        cliente, placa = input('UUID do titular: '), input('Placa: ')
        numero = int(input('Vaga: '))
        est.reservar_vaga(cliente, placa, numero, vip=input('Solicitar VIP? (s/n): ').lower() == 's')
        print('Reserva:', est.vagas[numero - 1].reserva.identificador)
    elif opcao == '15':
        est.cancelar_reserva(input('UUID do titular: '), int(input('Vaga: ')), int(input('ID da reserva: ')))
    elif opcao == '16':
        placa, numero, titular = input('Placa: '), int(input('Vaga: ')), input('UUID do titular: ')
        ctrl.iniciar_estadia(placa, numero, titular,
                             beneficiario_presente=input('Beneficiário presente e conferido? (s/n): ').lower() == 's')
    elif opcao == '17':
        est.alterar_carregador(int(input('Vaga elétrica: ')), input('Carregador operacional? (s/n): ') == 's')
    elif opcao == '18':
        placa = input('Placa: ')
        cotacao = ctrl.consultar_cobranca(placa, Decimal(input('Duração em horas: ').replace(',', '.')))
        print(f'Estadia {cotacao.estadia_id} · Total R$ {cotacao.valor_devido:.2f}'.replace('.', ','))
        acao = input('Pagar em simulação (p), concluir saída (s) ou voltar: ')
        if acao == 'p':
            ctrl.confirmar_pagamento(cotacao, confirmado=True)
        elif acao == 's':
            ctrl.concluir_saida(cotacao)

    elif opcao == '19':
        for c in ctrl.listar_clientes():
            print(c.identificador, c.nome, c.categoria)
            for v in ctrl.veiculos_do_cliente(c.identificador):
                print(f'  {v.placa} · {v.modelo} · {MOTORES[v.motorizacao]}')
        for v in ctrl.listar_vagas():
            if v.reserva:
                print(f'Reserva {v.reserva.identificador} · {v.numero:03d} · {v.reserva.placa}')
    elif opcao == '20':
        from model.categorias_cliente import preco_da_mudanca
        from view.formatacao import dinheiro
        titular = ctrl.buscar_cliente(input('UUID do titular: '))
        destino = input('Nova categoria (comum/vip/mensalista): ')
        valor = preco_da_mudanca(titular.categoria, destino)
        print('Mudança simulada:', dinheiro(Decimal(valor).scaleb(-2)))
        if input('Confirmar? (s/n): ') == 's':
            est.mudar_categoria(titular.identificador, titular.categoria, destino)
