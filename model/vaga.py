class Vaga:
    def __init__(self, numero):
        self.numero = numero
        self.ocupada = False 
        self.veiculo = None

    def ocupar(self, veiculo):
        if self.ocupada:
            raise ValueError(f"A vaga {self.numero} já está ocupada. ")
        self.ocupada = True
        self.veiculo = veiculo
    
    def liberar(self):
        if not self.ocupada:
            raise ValueError(f"A vaga {self.numero} já está livre.")
        self.ocupada = False
        veiculo = self.veiculo
        self.veiculo = None
        return veiculo















# class Vaga:
#     def __init__(self, numero):
#         self.numero = numero
#         self.ocupada = False
#         self.veiculo = None

#     def ocupar(self, veiculo):
#         if self.ocupada:
#             raise ValueError(f"Vaga {self.numero} já está ocupada.")
#         self.veiculo = veiculo
#         self.ocupada = True

#     def liberar(self):
#         if not self.ocupada:
#             raise ValueError(f"Vaga {self.numero} já está livre.")
#         veiculo = self.veiculo
#         self.veiculo = None
#         self.ocupada = False
#         return veiculo
