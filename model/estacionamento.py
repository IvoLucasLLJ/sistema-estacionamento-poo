import json
import math
from datetime import datetime

from model.vaga import Vaga


class Estacionamento:
    def __init__(self):
        self.vagas = [Vaga(num+1) for num in range(10)]
        self.historico = []

    def _buscar_vaga(self, numero):
        if type(numero) is not int or not 1 <= numero <= len(self.vagas):
            raise ValueError(f"Número da vaga deve ser inteiro entre 1 e {len(self.vagas)}.")
        return self.vagas[numero - 1]

    def estacionar(self, veiculo, num_vaga):
        vaga = self._buscar_vaga(num_vaga)
        if any(v.ocupada and v.veiculo.placa == veiculo.placa for v in self.vagas):
            raise ValueError(f"O veículo {veiculo.placa} já está estacionado.")
        vaga.ocupar(veiculo)
        self.historico.append({
            "acao": "entrada", "placa": veiculo.placa,
            "tipo": type(veiculo).__name__.lower(), "vaga": vaga.numero,
            "horario_entrada": datetime.now().astimezone().isoformat(),
        })

    def retirar(self, num_vaga, num_horas):
        vaga = self._buscar_vaga(num_vaga)
        if (isinstance(num_horas, bool) or not isinstance(num_horas, (int, float))
                or not math.isfinite(num_horas) or num_horas < 0):
            raise ValueError("Horas devem ser um número finito maior ou igual a zero.")
        if not vaga.ocupada:
            raise ValueError(f"A vaga {vaga.numero} já está livre.")
        veiculo = vaga.veiculo
        tarifa = veiculo.calcular_tarifa(num_horas)
        if not math.isfinite(tarifa):
            raise ValueError("O número de horas informado resulta em uma tarifa inválida.")
        entrada = next((evento for evento in reversed(self.historico)
                        if evento["acao"] == "entrada"
                        and evento["placa"] == veiculo.placa
                        and evento["vaga"] == vaga.numero), None)
        vaga.liberar()
        self.historico.append({
            "acao": "saida", "placa": veiculo.placa,
            "tipo": type(veiculo).__name__.lower(), "vaga": vaga.numero,
            "horario_entrada": entrada["horario_entrada"] if entrada else None,
            "horario_saida": datetime.now().astimezone().isoformat(),
            "horas": num_horas, "valor": tarifa,
        })
        return tarifa

    def relatorio(self):
        ocupadas = sum(1 for vaga in self.vagas if vaga.ocupada)
        return {
            "ocupadas": ocupadas,
            "livres": len(self.vagas) - ocupadas,
            "faturamento": sum(e["valor"] for e in self.historico if e["acao"] == "saida"),
        }

    def salvar_historico(self, arquivo="historico.json"):
        with open(arquivo, "w", encoding="utf-8") as destino:
            json.dump(self.historico, destino, ensure_ascii=False, indent=4)















# import json

# from model.vaga import Vaga


# class Estacionamento:
#     def __init__(self, total_vagas=10):
#         self.vagas = [Vaga(i+1) for i in range(total_vagas)]
#         self.historico = []

#     def estacionar(self, veiculo, numero_vaga):
#         vaga = self.vagas[numero_vaga - 1]
#         vaga.ocupar(veiculo)
#         self.historico.append({"acao": "entrada", "placa": veiculo.placa})

#     def retirar(self, numero_vaga, horas):
#         vaga = self.vagas[numero_vaga - 1]
#         veiculo = vaga.liberar()
#         tarifa = veiculo.calcular_tarifa(horas)
#         self.historico.append({
#             "acao": "saida",
#             "placa": veiculo.placa,
#             "valor": tarifa
#         })
#         return tarifa

#     def relatorio(self):
#         ocupadas = sum(1 for v in self.vagas if v.ocupada)
#         livres = len(self.vagas) - ocupadas
#         return {"ocupadas": ocupadas, "livres": livres}

#     def salvar_historico(self, arquivo="historico.json"):
#         with open(arquivo, "w") as f:
#             json.dump(self.historico, f, indent=4)
