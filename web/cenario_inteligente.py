"""Demonstração MOVE 2.0 em diretório próprio. Nunca acrescenta dados a um cenário existente."""
import argparse
import json
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from persistence.privacidade import criar_pasta_privada
from web import create_app
from web.demonstracao import configuracao, criar_cenario, provisionar_demonstracao, verificar_separacao, validar_pasta_demonstrativa
from web.__main__ import reservar_porta, servir


def preparar(pasta):
    verificar_separacao(pasta)
    if pasta.exists():
        raise ValueError('O destino já existe. Escolha um diretório novo.')
    with TemporaryDirectory(dir=pasta.parent) as temporario:
        pronta = Path(temporario) / 'cenario'
        criar_pasta_privada(pronta)
        app = create_app(configuracao(pronta))
        s = app.extensions['estacionamento']
        lia = criar_cenario(s)
        validade = (date.today() + timedelta(days=365)).isoformat()
        passageiros = [('EV200', 'eletrica', 'pcd'), ('HB200', 'plugin', 'idoso'),
                       ('CM200', 'convencional', 'obesa'), ('FC200', 'convencional', 'colo')]
        for beneficiario, (placa, motor, grupo) in enumerate(passageiros, start=1):
            s.cadastrar_veiculo_do_cliente(lia, 'carro', placa, 'Modelo demonstrativo', motor)
            meio = {'pcd': 'digital', 'idoso': 'fisica'}.get(grupo, 'administrativa')
            s.conferir_autorizacao(lia, placa, grupo, 'passageiro', meio, validade, beneficiario)
        s.alterar_carregador(176, False)
        s.reservar_vaga(lia, 'HB200', 120)
        s.reservar_vaga(lia, 'CM200', 16, vip=True)
        caio = s.cliente_do_veiculo('CB3')['identificador']
        s.reservar_vaga(caio, 'CB3', 15)
        (pronta / 'contas.json').write_text('[]', encoding='utf-8')
        (pronta / 'inteligente.json').write_text(json.dumps({'versao': 2, 'titular': lia}), encoding='utf-8')
        pronta.rename(pasta)


def abrir(pasta):
    verificar_separacao(pasta)
    validar_pasta_demonstrativa(pasta, 'inteligente.json')
    info = json.loads((pasta / 'inteligente.json').read_text(encoding='utf-8'))
    if info.get('versao') != 2:
        raise ValueError('Selecione um cenário inteligente criado para avaliação.')
    config = configuracao(pasta)
    config['SESSION_COOKIE_NAME'] = 'move_inteligente_demo'
    return create_app(config), info['titular']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pasta', type=Path)
    parser.add_argument('--novo', action='store_true', help='Prepara uma nova pasta de dados fictícios.')
    parser.add_argument('--porta', type=int, default=5012)
    args = parser.parse_args()
    pasta = args.pasta.expanduser().absolute()
    if args.porta == 5000 or not 1 <= args.porta <= 65535:
        parser.error('Use uma porta independente entre 1 e 65535, diferente de 5000.')
    if args.novo:
        preparar(pasta)
    app, lia = abrir(pasta)
    with reservar_porta('127.0.0.1', args.porta, False) as porta:
        escritor = app.extensions['escritor']
        escritor.abrir()
        try:
            provisionar_demonstracao(app, lia)
            servir(app, porta, '127.0.0.1', args.porta, False)
        finally:
            escritor.fechar()


if __name__ == '__main__':
    main()
