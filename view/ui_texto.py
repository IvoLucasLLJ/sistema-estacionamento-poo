from decimal import InvalidOperation
from view.operacoes_vagas import operacao
from controller.controller import Controller
from persistence.caminhos import historico_local
from view.formatacao import dinheiro


def menu(arquivo=None):
    try:
        ctrl = Controller(historico_local() if arquivo is None else arquivo)
    except (ValueError, OSError) as erro:
        print(f"Não foi possível abrir o histórico: {erro}")
        return

    while True:
        print("\n--- Sistema de Estacionamento ---")
        print("1. Cadastro e entrada rápida (compatibilidade)")
        print("2. Retirar por vaga (compatibilidade)")
        print("3. Relatório")
        print("4. Sair")
        print("5. Cadastrar veículo")
        print("6. Estacionar veículo cadastrado")
        print("7. Retirar por placa")
        print("8. Consultar setor | 9. Novo cliente | 10. Veículo com motorização | 11. Vincular veículo")
        print("12. Conferir autorização | 13. Revogar | 14. Reservar | 15. Cancelar reserva")
        print("16. Entrada identificada | 17. Carregador simulado | 18. Cobrança, pagamento ou saída")
        print("19. Clientes, frota e reservas | 20. Mudança de categoria simulada")
        opcao = input("Escolha: ").strip()

        if opcao == "1":
            tipo = input("Tipo (carro/moto/caminhao): ").lower()
            placa = input("Placa: ")
            modelo = input("Modelo: ")
            try:
                vaga = int(input("Número da vaga: "))
                ctrl.estacionar_veiculo(tipo, placa, modelo, vaga)
                print(f"Veículo {placa} estacionado na vaga {vaga}.")
            except ValueError as e:
                print(e)

        elif opcao == "2":
            try:
                vaga = int(input("Número da vaga: "))
                horas = float(input("Horas estacionado: ").replace(",", "."))
                tarifa = ctrl.retirar_veiculo(vaga, horas)
                print(f"Veículo retirado. Tarifa: {dinheiro(tarifa)}")
            except ValueError as e:
                print(e)

        elif opcao == "5":
            tipo = input("Tipo (carro/moto/caminhao): ")
            placa = input("Placa: ")
            modelo = input("Modelo: ")
            try:
                veiculo = ctrl.cadastrar_veiculo(tipo, placa, modelo)
                print(f"Veículo {veiculo.placa} cadastrado.")
            except ValueError as erro:
                print(erro)

        elif opcao == "6":
            placa = input("Placa cadastrada: ")
            try:
                vaga = int(input("Número da vaga: "))
                ctrl.estacionar_cadastrado(placa, vaga)
                print(f"Veículo estacionado na vaga {vaga}.")
            except ValueError as erro:
                print(erro)

        elif opcao == "7":
            placa = input("Placa: ")
            try:
                horas = float(input("Horas estacionado: ").replace(",", "."))
                tarifa = ctrl.retirar_por_placa(placa, horas)
                print(f"Veículo retirado. Tarifa: {dinheiro(tarifa)}")
            except ValueError as erro:
                print(erro)

        elif opcao in {str(n) for n in range(8, 21)}:
            try:
                operacao(ctrl, opcao)
            except (ValueError, InvalidOperation) as erro:
                print(f"Operação recusada: {erro}")
        elif opcao == "3":
            rel = ctrl.relatorio()
            print(f"Vagas ocupadas: {rel['ocupadas']}, Vagas livres: {rel['livres']}")
            print(f"Capacidade: {len(ctrl.listar_vagas())} · Reservadas: {sum(v.reserva is not None for v in ctrl.listar_vagas())}")
            print(f"Faturamento total: {dinheiro(rel['faturamento'])}")

        elif opcao == "4":
            try:
                ctrl.salvar()
            except OSError as e:
                print(f"Não foi possível salvar o histórico: {e}")
                continue
            print("Saindo... Histórico salvo.")
            break
        else:
            print("Opção inválida.")
