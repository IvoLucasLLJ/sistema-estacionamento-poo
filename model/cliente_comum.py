from model.cliente import Cliente


class ClienteComum(Cliente):
    def calcular_cobranca(self, tarifa_base):
        self._validar_tarifa_base(tarifa_base)
        return tarifa_base
