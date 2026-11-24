from model.cliente import Cliente


class ClienteVIP(Cliente):
    CATEGORIA = "vip"

    def calcular_cobranca(self, tarifa_base):
        self._validar_tarifa_base(tarifa_base)
        return tarifa_base / 2
