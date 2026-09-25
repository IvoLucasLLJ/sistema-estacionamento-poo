from controller.controller import Controller


def menu():
    ctrl = Controller()

    while True:
        print("\n--- Sistema de Estacionamento ---")
        print("1. Estacionar veículo")
        print("2. Retirar veículo")
        print("3. Relatório")
        print("4. Sair")
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
                print(f"Veículo retirado. Tarifa: R$ {tarifa:.2f}")
            except ValueError as e:
                print(e)

        elif opcao == "3":
            rel = ctrl.relatorio()
            print(f"Vagas ocupadas: {rel['ocupadas']}, Vagas livres: {rel['livres']}")
            print(f"Faturamento total: R$ {rel['faturamento']:.2f}")

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
