"""Ensaio funcional opcional. Execute como módulo a partir da raiz do MOVE."""
import argparse
import secrets
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from unittest.mock import patch

from werkzeug.serving import make_server

from web import create_app
from web.contas import PapelAcesso


def cenario(app, senha):
    servico = app.extensions['estacionamento']
    acesso = app.extensions['autenticacao']
    lia = servico.cadastrar_cliente('vip', 'Lia Vale')['identificador']
    caio = servico.cadastrar_cliente('comum', 'Caio Demo')['identificador']
    acesso.provisionar('operacao.demo', senha, PapelAcesso.GESTAO)
    acesso.provisionar('lia.demo', senha, PapelAcesso.CLIENTE, lia)
    for placa, tipo, modelo, cliente, vaga in [('CB3', 'carro', 'Serra', caio, 8),
                                              ('AV1', 'carro', 'Atlas', lia, 2),
                                              ('AM2', 'moto', 'Brisa', lia, 5)]:
        servico.cadastrar_veiculo(tipo, placa, modelo)
        servico.vincular_veiculo(placa, cliente)
        servico.iniciar_estadia(placa, vaga, cliente)
    for placa, horas in [('CB3', '2'), ('AV1', '1.225')]:
        cotacao = servico.consultar_cobranca(placa, horas)
        servico.confirmar_pagamento(placa, horas, cotacao, confirmado=True)
        if placa == 'CB3':
            servico.concluir_saida(placa, horas, cotacao)
    return servico.iniciar_estadia('CB3', 8, caio)['estadia_id']


def percorrer(pagina, url, senha, terceiro, historico, capturas):
    erros, externos = [], []
    pagina.on('pageerror', lambda erro: erros.append(str(erro)))
    pagina.on('request', lambda req: externos.append(req.url) if not req.url.startswith(url + '/') else None)

    def foto(nome):
        if capturas:
            pagina.evaluate('document.fonts.ready')
            pagina.screenshot(path=capturas / f'move-08a-{nome}.png')

    def login(usuario):
        pagina.get_by_label('Usuário', exact=True).fill(usuario)
        pagina.get_by_label('Senha', exact=True).fill(senha)
        pagina.get_by_role('button', name='Entrar', exact=True).click()

    def sair():
        pagina.locator('summary').click()
        pagina.get_by_role('button', name='Sair', exact=True).click()
        assert pagina.url == url + '/entrar'

    def modo(preferencia):
        pagina.locator('.tema label').filter(has_text=preferencia).click()

    def sem_transbordamento():
        for largura in (320, 390, 768, 1440):
            pagina.set_viewport_size({'width': largura, 'height': 900})
            assert pagina.evaluate('document.documentElement.scrollWidth <= innerWidth'), largura

    pagina.goto(url)
    pagina.get_by_role('heading', name='Entrar no MOVE').wait_for()
    foto('login')
    pagina.get_by_role('button', name='Mostrar senha').click()
    assert pagina.locator('#senha').get_attribute('type') == 'text'
    pagina.get_by_role('button', name='Ocultar senha').click()
    pagina.get_by_label('Usuário', exact=True).fill('operacao.demo')
    pagina.get_by_label('Senha', exact=True).fill('incorreta')
    # Inspeciona o formulário durante o primeiro envio, antes da navegação HTTP.
    protecao = pagina.locator('form').evaluate("""form => {
        form.requestSubmit();
        const segundo = new SubmitEvent('submit', {bubbles: true, cancelable: true});
        return [form.getAttribute('aria-busy'), form.querySelector('[type=submit]').disabled,
                form.dispatchEvent(segundo)];
    }""")
    assert protecao == ['true', True, False]
    pagina.get_by_role('alert').wait_for()
    login('operacao.demo')
    assert pagina.url == url + '/gestao/'
    assert pagina.locator('.grade-vagas li').count() == 10
    assert pagina.locator('.grade-vagas .ocupada').count() == 3
    assert pagina.locator('.ocupacao .medida strong').inner_text() == '7'
    assert 'R$ 20,00' in pagina.locator('#financeiro').inner_text()
    foto('gestao')
    sem_transbordamento()
    modo('Escuro')
    sair()
    assert pagina.locator('html').get_attribute('data-tema') == 'escuro'

    login('lia.demo')
    assert pagina.url == url + '/cliente/'
    assert 'R$ 6,13' in pagina.locator('#estadias').inner_text()
    assert 'CB3' not in pagina.locator('main').inner_text()
    assert 'Faturamento' not in pagina.locator('main').inner_text()
    sem_transbordamento()
    pagina.set_viewport_size({'width': 390, 'height': 844})
    foto('cliente')
    pagina.locator('#estadias a').first.click()
    assert '/cliente/estadias/' in pagina.url
    assert pagina.goto(f'{url}/cliente/estadias/{terceiro}').status == 404
    mensagem = pagina.locator('main').inner_text()
    assert pagina.goto(url + '/cliente/estadias/999999').status == 404
    assert pagina.locator('main').inner_text() == mensagem
    assert pagina.goto(url + '/gestao/').status == 403
    foto('acesso-negado')
    pagina.get_by_role('link', name='Voltar ao início').click()
    assert pagina.url == url + '/cliente/'
    modo('Claro')
    assert pagina.locator('html').get_attribute('data-tema') == 'claro'
    modo('Sistema')
    pagina.emulate_media(color_scheme='dark')
    pagina.locator('html[data-tema="escuro"]').wait_for()
    pagina.reload()
    assert pagina.locator('html').get_attribute('data-tema') == 'escuro'
    assert pagina.evaluate('Object.keys(localStorage)') == ['move.tema']

    anterior = historico.read_bytes()
    try:
        historico.write_bytes(b'{')
        assert pagina.reload().status == 503
        pagina.get_by_role('heading', name='Serviço indisponível').wait_for()
    finally:
        historico.write_bytes(anterior)
    pagina.get_by_role('link', name='Repetir consulta').click()
    pagina.get_by_role('heading', name='Olá, Lia Vale').wait_for()
    with patch('web.seguranca.agora', return_value=10**10):
        assert pagina.reload().status == 401
        pagina.get_by_role('heading', name='Sessão expirada').wait_for()
    pagina.get_by_role('link', name='Entrar novamente').click()
    login('lia.demo')
    sair()
    assert pagina.goto(url + '/gestao/').url == url + '/entrar'
    assert not erros and not externos, (erros, externos)


def conferir_consulta_pessoal(browser, perfil, descricao, url, senha):
    with browser.new_context(**perfil, locale='pt-BR', color_scheme='dark') as contexto:
        pagina = contexto.new_page()
        pagina.goto(url + '/entrar')
        pagina.get_by_label('Usuário', exact=True).fill('lia.demo')
        pagina.get_by_label('Senha', exact=True).fill(senha)

        def ativar(controle):
            if perfil.get('has_touch'):
                controle.tap()
            else:
                controle.focus()
                pagina.keyboard.press('Enter')

        ativar(pagina.get_by_role('button', name='Entrar', exact=True))
        pagina.wait_for_url(url + '/cliente/')
        assert 'R$ 6,13' in pagina.locator('#estadias').inner_text()
        nav = pagina.get_by_role('navigation')
        consulta = nav.get_by_role('link', name='Disponibilidade', exact=True)
        if not consulta.is_visible():
            ativar(nav.get_by_role('button', name='Mais', exact=True))
        ativar(consulta)
        pagina.wait_for_url(url + '/cliente/disponibilidade')
        with pagina.expect_navigation(url=url + '/cliente/disponibilidade', wait_until='load'):
            ativar(pagina.get_by_role('link', name='Atualizar'))
        assert pagina.locator('.medida strong').inner_text() == '7'
        assert pagina.locator('html').get_attribute('data-tema') == 'escuro'
        assert pagina.evaluate('document.documentElement.scrollWidth <= innerWidth')
        assert 'AV1' not in pagina.locator('main').inner_text()
        print(f'{descricao} · consulta pessoal aprovada em {browser.browser_type.name} {browser.version}', flush=True)


def main():
    from playwright.sync_api import sync_playwright

    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--chrome', help='Executável Chromium/Chrome já instalado.')
    cli.add_argument('--webkit', action='store_true', help='Testar também perfis iPhone e iPad com o WebKit do Playwright.')
    cli.add_argument('--capturas', type=Path, help='Pasta de saída para os quatro PNGs.')
    args = cli.parse_args()
    if args.capturas:
        args.capturas.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix='move-navegador-') as pasta:
        raiz = Path(pasta)
        historico = raiz / 'historico.json'
        app = create_app(dict(DADOS=raiz, HISTORICO=historico, CONTAS=raiz / 'contas.json',
                              SECRET_KEY=None, SESSION_COOKIE_SECURE=False))
        senha = secrets.token_urlsafe(32)
        terceiro = cenario(app, senha)
        with make_server('127.0.0.1', 0, app, threaded=True) as servidor:
            thread = Thread(target=servidor.serve_forever)
            thread.start()
            try:
                with sync_playwright() as pw:
                    with pw.chromium.launch(executable_path=args.chrome) as browser:
                        pagina = browser.new_page(viewport={'width': 1440, 'height': 900}, color_scheme='light')
                        percorrer(pagina, f'http://127.0.0.1:{servidor.server_port}', senha,
                                  terceiro, historico, args.capturas)
                        print(f'Percurso aprovado em Chromium {browser.version}.')
                        url = f'http://127.0.0.1:{servidor.server_port}'
                        conferir_consulta_pessoal(browser, pw.devices['Pixel 7'], 'Perfil Pixel 7', url, senha)
                        conferir_consulta_pessoal(browser, {'viewport': {'width': 1366, 'height': 768}},
                                                  'Chrome desktop com teclado · referência Chromebook', url, senha)
                    if args.webkit:
                        with pw.webkit.launch() as browser:
                            for modelo in ('iPhone 13', 'iPad (gen 7)'):
                                conferir_consulta_pessoal(browser, pw.devices[modelo], modelo, url, senha)
            finally:
                servidor.shutdown()
                thread.join()
                app.extensions['escritor'].fechar()


if __name__ == '__main__':
    main()
