"""Apresentação completa em uma única aba autenticada como master.demo."""
import argparse
from pathlib import Path
from secrets import token_urlsafe
from tempfile import TemporaryDirectory
from threading import Thread

from werkzeug.serving import make_server

from service.estacionamento_service import EstacionamentoService
from tests.navegador_08c import destino, login
from tests.test_contexto_acesso import demo_temporaria


def apresentar(pagina, url, senha, largura, capturas):
    logins, erros = [], []
    pagina.on('request', lambda req: logins.append(req.url) if req.method == 'POST' and req.url == url + '/entrar' else None)
    pagina.on('pageerror', lambda exc: erros.append(str(exc)))
    menu = pagina.locator('.menu-ambiente')

    def foto(nome):
        if capturas:
            pagina.evaluate('document.fonts.ready')
            pagina.screenshot(path=capturas / f'{largura}-{nome}.png')

    def botao(nome):
        pagina.get_by_role('button', name=nome, exact=True).click()

    def seguir(nome):
        pagina.locator('main').get_by_role('link', name=nome, exact=True).click()

    def gestao(nome):
        abrir = pagina.locator('[data-menu]')
        if abrir.is_visible() and abrir.get_attribute('aria-expanded') == 'false':
            abrir.click()
        pagina.get_by_role('navigation').get_by_role('link', name=nome, exact=True).click()

    def alternar(de, para, captura=None):
        assert menu.locator('summary').inner_text().strip() == de
        if largura < 768:
            menu.locator('summary').tap()
        else:
            menu.locator('summary').click()
        assert menu.locator('[aria-current="true"]').inner_text().strip() == 'MOVE ' + de
        if captura:
            foto(captura)
        botao('MOVE ' + para)
        pagina.wait_for_url(url + ('/cliente/' if para == 'Cliente' else '/gestao/'))
        assert pagina.locator('.perfil summary').get_attribute('aria-label').endswith('master.demo')
        assert pagina.locator('html').get_attribute('data-tema') == ('escuro' if largura < 768 else 'claro')
        assert pagina.evaluate('document.documentElement.scrollWidth <= innerWidth')

    pagina.goto(url)
    login(pagina, 'master.demo', senha)
    pagina.wait_for_url(url + '/gestao/')
    # Os dois veículos originais de Lia já estão estacionados no cenário inicial.
    gestao('Veículos')
    pagina.get_by_label('Tipo', exact=True).select_option('carro')
    pagina.get_by_label('Placa', exact=True).fill('MD3')
    pagina.get_by_label('Modelo', exact=True).fill('Brisa Demo')
    botao('Cadastrar veículo')
    responsavel = pagina.get_by_label('Cliente responsável')
    opcao = responsavel.locator('option').filter(has_text='Lia Vale')
    responsavel.select_option(label=opcao.inner_text())
    botao('Vincular cliente')
    seguir('Registrar entrada')
    pagina.get_by_label('Vaga livre').select_option('3')
    botao('Revisar entrada')
    botao('Confirmar entrada')
    numero = int(pagina.url.rsplit('/', 1)[1])
    alternar('Gestão', 'Cliente', 'seletor-gestao')
    seguir('MD3 · Vaga 3')
    assert 'Sem pagamento confirmado' in pagina.locator('main').inner_text()
    alternar('Cliente', 'Gestão')
    gestao('Estadias ativas')
    registro = pagina.locator('article').filter(has=pagina.get_by_role('heading', name='MD3', exact=True))
    registro.get_by_role('link', name='Preparar saída').click()
    pagina.get_by_label('Duração em horas').fill('1,225')
    botao('Consultar cobrança')
    seguir('Revisar pagamento')
    botao('Confirmar pagamento simulado')
    alternar('Gestão', 'Cliente')
    ativo = pagina.locator('article').filter(has_text='MD3')
    assert 'Pagamento confirmado · R$ 6,13' in ativo.inner_text()
    assert 'Veículo ainda estacionado' in ativo.inner_text()
    alternar('Cliente', 'Gestão', 'seletor-cliente')
    gestao('Pagamentos')
    seguir('Continuar saída')
    botao('Concluir saída paga')
    alternar('Gestão', 'Cliente')
    assert 'MD3' not in pagina.locator('#estadias').inner_text()
    destino(pagina, 'Meu histórico')
    seguir(f'Estadia {numero} · MD3')
    seguir('Ver comprovante')
    recibo = pagina.locator('main').inner_text()
    for trecho in ('Saída paga', 'R$ 12,25', 'R$ 6,13', 'Sem valor fiscal'):
        assert trecho in recibo, recibo
    assert 'Faturamento' not in recibo
    foto('comprovante')
    assert logins == [url + '/entrar'] and not erros, (logins, erros)
    return numero


def main():
    from playwright.sync_api import sync_playwright

    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--chrome')
    cli.add_argument('--capturas', type=Path)
    args = cli.parse_args()
    if args.capturas:
        args.capturas.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw, pw.chromium.launch(executable_path=args.chrome) as browser:
        for largura, altura in [(1440, 900), (1024, 768), (390, 844)]:
            with TemporaryDirectory(prefix='move-master-') as pasta:
                senha = token_urlsafe(24)
                app = demo_temporaria(Path(pasta), token_urlsafe(24), senha_master=senha)
                with make_server('127.0.0.1', 0, app) as servidor, browser.new_context(
                        viewport=dict(width=largura, height=altura), is_mobile=largura < 768,
                        has_touch=largura <= 1024, color_scheme='dark' if largura < 768 else 'light') as ctx:
                    thread = Thread(target=servidor.serve_forever)
                    thread.start()
                    try:
                        pagina = ctx.new_page()
                        pagina.set_default_timeout(7000)
                        numero = apresentar(pagina, f'http://127.0.0.1:{servidor.server_port}', senha, largura, args.capturas)
                    finally:
                        servidor.shutdown()
                        thread.join()
                        app.extensions['escritor'].fechar()
                leitor = EstacionamentoService(app.config['HISTORICO'])
                estadia = leitor.consultar_estadia(numero)
                assert estadia['situacao'] == 'concluida' and estadia['cobranca']['valor_centavos'] == 613
                assert leitor.consultar_ocupacao()['livres'] == 7
                print(f'{largura} × {altura} · Chrome {browser.version} · um login · estadia {numero} · 613 centavos persistidos',
                      flush=True)


if __name__ == '__main__':
    main()
