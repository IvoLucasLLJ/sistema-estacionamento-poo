"""Percurso de aparência e ambientes, com contas fictícias e servidor em loopback."""
import argparse
from pathlib import Path
from secrets import token_urlsafe
from tempfile import TemporaryDirectory
from threading import Thread

from werkzeug.serving import make_server

from tests.navegador_08c import login
from tests.test_contexto_acesso import demo_temporaria


def conferir_largura(pagina):
    assert pagina.evaluate('document.documentElement.scrollWidth <= innerWidth')
    controles = pagina.locator('.cabecalho a.assinatura, .cabecalho summary, .ferramentas-acesso summary')
    anterior = 0
    for el in controles.all():
        caixa = el.bounding_box()
        assert anterior <= caixa['x'] and caixa['height'] > 0
        anterior = caixa['x'] + caixa['width']
        assert anterior <= pagina.viewport_size['width']
    for painel in pagina.locator('[data-menu-cabecalho][open] .painel-menu').all():
        caixa = painel.bounding_box()
        assert 0 <= caixa['x'] <= pagina.viewport_size['width'] - caixa['width']


def percorrer(browser, url, senha, largura, altura, toque, capturas):
    with browser.new_context(viewport=dict(width=largura, height=altura), is_mobile=toque,
                             has_touch=toque, color_scheme='light', locale='pt-BR') as contexto:
        p = contexto.new_page()
        p.add_init_script("""new MutationObserver((_, observador) => {
            if (document.body) {
                window.temaAoCriarCorpo = document.documentElement.dataset.tema;
                observador.disconnect();
            }
        }).observe(document, {childList: true, subtree: true});""")
        erros = []
        p.on('pageerror', lambda exc: erros.append(str(exc)))
        p.set_default_timeout(5000)
        tema = p.locator('.menu-aparencia > summary')
        ambiente = p.locator('.menu-ambiente > summary')

        def acionar(elemento):
            if toque:
                elemento.tap()
            else:
                elemento.focus()
                p.keyboard.press('Enter')

        def modo(valor):
            p.locator(f'html[data-tema="{valor}"]').wait_for(state='attached')

        def foto(nome):
            if capturas:
                p.evaluate('document.fonts.ready')
                p.screenshot(path=capturas / (nome + '.png'), animations='disabled')

        p.goto(url)
        modo('claro')
        assert p.locator('.cartao-acesso [data-componente=N07]').count() == 0
        assert not p.get_by_role('radio', name='Sistema').is_visible()
        conferir_largura(p)
        if largura in (390, 1440):
            foto(f'login-{largura}')
        p.emulate_media(color_scheme='dark')
        modo('escuro')
        assert tema.get_attribute('aria-label') == 'Aparência: Sistema'
        acionar(tema)
        conferir_largura(p)
        assert p.get_by_role('radio', name='Sistema').is_checked()
        if largura in (390, 1440):
            foto(f'aparencia-{largura}')
        if toque:
            p.locator('.tema label').filter(has_text='Claro').tap()
        else:
            p.keyboard.press('Tab')
            p.keyboard.press('ArrowRight')
        modo('claro')
        assert tema.get_attribute('aria-label') == 'Aparência: Claro'
        if toque:
            tema.tap()
        else:
            p.keyboard.press('Escape')
            assert tema.evaluate('el => el === document.activeElement')
        p.reload()
        modo('claro')
        assert p.evaluate('window.temaAoCriarCorpo') == 'claro'
        login(p, 'gestao.demo', senha)
        p.wait_for_url(url + '/gestao/')
        modo('claro')
        conferir_largura(p)
        acionar(ambiente)
        conferir_largura(p)
        if largura in (1024, 1440):
            foto(f'gestao-ambientes-{largura}')
        acionar(p.get_by_role('button', name='MOVE Cliente'))
        p.wait_for_url(url + '/cliente/')
        modo('claro')
        assert 'Lia Vale' in p.locator('h1').inner_text()
        assert 'Faturamento' not in p.locator('main').inner_text()
        conferir_largura(p)
        acionar(tema)
        if toque:
            p.locator('.tema label').filter(has_text='Escuro').tap()
        else:
            p.keyboard.press('Tab')
            p.keyboard.press('ArrowRight')
        modo('escuro')
        p.emulate_media(color_scheme='light')
        assert tema.get_attribute('aria-label') == 'Aparência: Escuro'
        acionar(ambiente)  # Fecha o menu anterior ao abrir o seletor.
        assert not p.locator('.menu-aparencia').evaluate('el => el.open')
        conferir_largura(p)
        if largura in (390, 1024):
            foto(f'cliente-ambientes-{largura}')
        assert p.goto(url + '/gestao/').status == 403
        modo('escuro')
        acionar(p.get_by_role('link', name='Voltar ao início'))
        p.wait_for_url(url + '/cliente/')
        if largura in (390, 1024):
            foto(f'cliente-{largura}')
        acionar(ambiente)
        acionar(p.get_by_role('button', name='MOVE Gestão'))
        p.wait_for_url(url + '/gestao/')
        modo('escuro')
        acionar(p.locator('.perfil > summary'))
        acionar(p.get_by_role('button', name='Sair'))
        p.wait_for_url(url + '/entrar')
        modo('escuro')
        # Uma nova sessão de navegador recupera apenas a preferência local.
        with browser.new_context(storage_state=contexto.storage_state(), color_scheme='light') as reaberto:
            nova = reaberto.new_page()
            nova.goto(url)
            assert nova.url == url + '/entrar'
            assert nova.locator('html').get_attribute('data-tema') == 'escuro'
        assert not erros, erros
        print(f'{largura} × {altura} · {"toque emulado" if toque else "teclado"} · aprovado', flush=True)


def main():
    from playwright.sync_api import sync_playwright

    opcoes = argparse.ArgumentParser(description=__doc__)
    opcoes.add_argument('--chrome', help='Executável Chrome ou Chromium.')
    opcoes.add_argument('--capturas', type=Path)
    args = opcoes.parse_args()
    if args.capturas:
        args.capturas.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix='move-ui-') as pasta, sync_playwright() as pw:
        senha = token_urlsafe(24)
        app = demo_temporaria(Path(pasta), senha)
        with pw.chromium.launch(executable_path=args.chrome) as browser, make_server('127.0.0.1', 0, app) as servidor:
            thread = Thread(target=servidor.serve_forever)
            thread.start()
            try:
                url = f'http://127.0.0.1:{servidor.server_port}'
                for largura, altura, toque in [(320, 720, True), (390, 844, True), (768, 1024, True),
                                              (1024, 768, True), (1440, 900, False)]:
                    percorrer(browser, url, senha, largura, altura, toque, args.capturas)
                print(f'Chromium {browser.version}')
            finally:
                servidor.shutdown()
                thread.join()
                app.extensions['escritor'].fechar()


if __name__ == '__main__':
    main()
