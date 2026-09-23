# sistema_estacionamento.py
# Projeto POO - Sistema de Estacionamento Inteligente


# ============================================================
# CLASSE BASE: VEICULO
# ============================================================

class Veiculo:
    def __init__(self, placa, modelo):
        self.placa = placa
        self.modelo = modelo

    def calcular_tarifa(self, horas):
        raise NotImplementedError(
            "O método calcular_tarifa deve ser implementado pelas subclasses."
        )

    def __str__(self):
        return f"{self.__class__.__name__} - {self.placa} - {self.modelo}"


# ============================================================
# CLASSES FILHAS
# ============================================================

class Carro(Veiculo):
    def __init__(self, placa, modelo):
        super().__init__(placa, modelo)

    def calcular_tarifa(self, horas):
        valor_hora = 10.00
        return horas * valor_hora


class Moto(Veiculo):
    def __init__(self, placa, modelo):
        super().__init__(placa, modelo)

    def calcular_tarifa(self, horas):
        valor_hora = 5.00
        return horas * valor_hora


class Caminhao(Veiculo):
    def __init__(self, placa, modelo):
        super().__init__(placa, modelo)

    def calcular_tarifa(self, horas):
        valor_hora = 20.00
        return horas * valor_hora


# ============================================================
# CLASSE VAGA
# ============================================================

class Vaga:
    def __init__(self, numero, tipo):
        self.numero = numero
        self.tipo = tipo
        self.ocupada = False
        self.veiculo = None

    def aceita_veiculo(self, veiculo):
        if self.tipo == "carro" and isinstance(veiculo, Carro):
            return True

        if self.tipo == "moto" and isinstance(veiculo, Moto):
            return True

        if self.tipo == "caminhao" and isinstance(veiculo, Caminhao):
            return True

        return False

    def ocupar(self, veiculo):
        if self.ocupada:
            return False

        if not self.aceita_veiculo(veiculo):
            return False

        self.veiculo = veiculo
        self.ocupada = True

        return True

    def liberar(self):
        veiculo = self.veiculo

        self.veiculo = None
        self.ocupada = False

        return veiculo

    def __str__(self):
        if self.ocupada:
            return (
                f"Vaga {self.numero} "
                f"({self.tipo}) - OCUPADA por {self.veiculo.placa}"
            )

        return f"Vaga {self.numero} ({self.tipo}) - LIVRE"


# ============================================================
# CLASSE ESTACIONAMENTO
# ============================================================

class Estacionamento:
    def __init__(self, nome, capacidade=200):
        self.nome = nome
        self.capacidade = capacidade
        self.vagas = []

        self.criar_vagas()

    def criar_vagas(self):
        """
        Cria automaticamente as 200 vagas.

        120 vagas para carros
        50 vagas para motos
        30 vagas para caminhões

        Total = 200 vagas
        """

        numero = 1

        # 120 vagas para carros
        for _ in range(120):
            self.vagas.append(Vaga(numero, "carro"))
            numero += 1

        # 50 vagas para motos
        for _ in range(50):
            self.vagas.append(Vaga(numero, "moto"))
            numero += 1

        # 30 vagas para caminhões
        for _ in range(30):
            self.vagas.append(Vaga(numero, "caminhao"))
            numero += 1

    def encontrar_vaga_livre(self, veiculo):
        for vaga in self.vagas:
            if not vaga.ocupada and vaga.aceita_veiculo(veiculo):
                return vaga

        return None

    def entrada_veiculo(self, veiculo):
        # Verifica se o veículo já está estacionado
        for vaga in self.vagas:
            if vaga.ocupada and vaga.veiculo.placa == veiculo.placa:
                print("Veículo já está no estacionamento.")
                return False

        vaga = self.encontrar_vaga_livre(veiculo)

        if vaga is None:
            print("Não existe vaga disponível para este tipo de veículo.")
            return False

        vaga.ocupar(veiculo)

        print(
            f"Entrada autorizada: {veiculo.placa} "
            f"na vaga {vaga.numero}."
        )

        return True

    def localizar_veiculo(self, placa):
        for vaga in self.vagas:
            if vaga.ocupada:
                if vaga.veiculo.placa == placa:
                    return vaga

        return None

    def saida_veiculo(self, placa, horas):
        vaga = self.localizar_veiculo(placa)

        if vaga is None:
            print("Veículo não encontrado.")
            return False

        veiculo = vaga.veiculo

        valor = veiculo.calcular_tarifa(horas)

        vaga.liberar()

        print("\n--- SAÍDA DO VEÍCULO ---")
        print(f"Placa: {veiculo.placa}")
        print(f"Modelo: {veiculo.modelo}")
        print(f"Tempo: {horas} hora(s)")
        print(f"Valor: R$ {valor:.2f}")
        print(f"Vaga {vaga.numero} liberada.")

        return True

    def mostrar_vagas(self):
        print("\n--- SITUAÇÃO DAS VAGAS ---")

        for vaga in self.vagas:
            print(vaga)

    def resumo(self):
        total_ocupadas = 0

        carros = 0
        motos = 0
        caminhoes = 0

        for vaga in self.vagas:
            if vaga.ocupada:
                total_ocupadas += 1

                if vaga.tipo == "carro":
                    carros += 1

                elif vaga.tipo == "moto":
                    motos += 1

                elif vaga.tipo == "caminhao":
                    caminhoes += 1

        livres = self.capacidade - total_ocupadas

        print("\n========== RESUMO ==========")
        print(f"Estacionamento: {self.nome}")
        print(f"Capacidade: {self.capacidade}")
        print(f"Vagas ocupadas: {total_ocupadas}")
        print(f"Vagas livres: {livres}")
        print(f"Carros estacionados: {carros}")
        print(f"Motos estacionadas: {motos}")
        print(f"Caminhões estacionados: {caminhoes}")
        print("============================")


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():

    estacionamento = Estacionamento(
        "Estacionamento Inteligente"
    )

    # Criando objetos
    carro1 = Carro(
        "ABC1D23",
        "Volkswagen Golf"
    )

    moto1 = Moto(
        "MOT2E34",
        "Honda CB 500"
    )

    caminhao1 = Caminhao(
        "CAM3F45",
        "Volvo FH"
    )

    print("\n=== SISTEMA DE ESTACIONAMENTO ===")

    # Entrada dos veículos
    estacionamento.entrada_veiculo(carro1)
    estacionamento.entrada_veiculo(moto1)
    estacionamento.entrada_veiculo(caminhao1)

    # Mostra o resumo
    estacionamento.resumo()

    # Localiza um veículo
    vaga = estacionamento.localizar_veiculo("ABC1D23")

    if vaga:
        print(
            f"\nO veículo ABC1D23 está "
            f"na vaga {vaga.numero}."
        )

    # Saída do carro após 3 horas
    estacionamento.saida_veiculo(
        "ABC1D23",
        3
    )

    # Resumo depois da saída
    estacionamento.resumo()


# Executa o programa somente quando este arquivo
# for executado diretamente.
if __name__ == "__main__":
    main()