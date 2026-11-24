from model.cliente import Cliente


class ClienteMensalista(Cliente):
    def calcular_cobranca(self, tarifa_base):
        self._validar_tarifa_base(tarifa_base)
        return 0
