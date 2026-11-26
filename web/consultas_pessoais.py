"""Leituras do serviço limitadas ao titular já identificado no servidor."""
from web.eventos import eventos_identificados


class ConsultasPessoais:
    def __init__(self, servico, titular):
        self._servico = servico
        self._titular = titular

    def veiculos(self):
        return self._servico.veiculos_do_cliente(self._titular)

    def ativas(self):
        return [e for e in self._servico.listar_estadias_ativas() if e['cliente_id'] == self._titular]

    def historico(self):
        """Uma linha por entrada identificada do titular, na ordem mais recente primeiro."""
        estadias = {}
        for evento in eventos_identificados(self._servico.consultar_historico()):
            if evento.get('cliente_id') != self._titular or 'estadia_id' not in evento:
                continue
            numero = evento['estadia_id']
            if evento['acao'] == 'entrada_cliente':
                estadias[numero] = {chave: evento[chave] for chave in
                                    ('estadia_id', 'placa', 'tipo', 'vaga', 'categoria', 'horario_entrada')}
                estadias[numero].update(classificacao=evento.get('classificacao'), vip=evento.get('vip',False),
                                        estado='ativa', horario_saida=None, horas=None, valor_centavos=None)
            elif evento['acao'] == 'pagamento_confirmado':
                estadias[numero].update(estado='aguardando', horas=evento['horas'],
                                        valor_centavos=evento['valor_centavos'])
            elif evento['acao'] == 'saida_cliente':
                estado = 'isenta' if evento['pagamento'] == 'isento' else 'paga'
                estadias[numero].update(estado=estado, horario_saida=evento['horario_saida'],
                                        horas=evento['horas'], valor_centavos=evento['valor_centavos'])
        return list(reversed(estadias.values()))
