"""Ensaio do acesso público e do primeiro login, com Flask e dados temporários."""
import argparse
from pathlib import Path
from secrets import token_urlsafe
from tempfile import TemporaryDirectory
from threading import Thread
from urllib.parse import urlsplit

from werkzeug.serving import make_server

from tests.test_contexto_acesso import demo_temporaria


FRONTEIRA = [(1119, 800), (1120, 800), (1121, 800)]
DESKTOP = FRONTEIRA + [(1280, 720), (1366, 768), (1440, 900), (1536, 864), (1920, 1080),
           (2560, 1440), (3440, 1440)]
TOQUE = FRONTEIRA + [(320, 568), (360, 800), (390, 844), (800, 360), (844, 390),
                     (768, 1024), (1024, 768), (1280, 800), (1366, 1024)]


def foto(pagina, pasta, nome):
    if pasta:
        pagina.screenshot(path=pasta / (nome + '.png'), animations='disabled')


def conferir_telas(browser, url, pasta):
    for toque, dimensoes in [(False, DESKTOP), (True, TOQUE)]:
        for largura, altura in dimensoes:
            for cor, tema in [('light','claro'), ('dark','escuro')]:
                with browser.new_context(viewport=dict(width=largura, height=altura), color_scheme=cor,
                                         has_touch=toque, is_mobile=toque, locale='pt-BR') as contexto:
                    pagina = contexto.new_page()
                    recursos = []
                    pagina.on('request', lambda req: recursos.append(req.url))
                    for tela, rota in [('login','entrar'), ('cadastro','criar-conta')]:
                        assert pagina.goto(f'{url}/{rota}', wait_until='load').ok
                        pagina.evaluate('document.fonts.ready')
                        formulario = pagina.locator('main form')
                        assert formulario.count() == 1 and formulario.is_visible()
                        assert pagina.locator('html').get_attribute('data-tema') == tema
                        amplo = largura >= 1120  # Fonte inicial de 16 px neste perfil do Chrome.
                        assert pagina.locator('.login-institucional').is_visible() == amplo
                        assert pagina.evaluate('document.documentElement.scrollWidth <= innerWidth')
                        for campo in formulario.locator('input:not([type=hidden])').all():
                            assert campo.evaluate('e => !!e.labels.length')
                        if amplo:
                            caixa = formulario.bounding_box()
                            painel = pagina.locator('.login-institucional').bounding_box()
                            assert abs(painel['width'] - .58 * largura) < 1
                            assert abs(caixa['width'] - min(.42 * largura - 96, 416)) < 1
                            assert painel['width'] < caixa['x']
                            assert int(pagina.locator('button[type=submit]').bounding_box()['height']) >= 44
                        foto(pagina, pasta, f'{tela}-{largura}x{altura}-{tema}')
                    assert any(r.endswith('/estacionamento.webp') for r in recursos) == amplo
                    assert all(urlsplit(r).netloc == urlsplit(url).netloc for r in recursos)
    print(f'Login e cadastro: {len(DESKTOP)} perfis com mouse e {len(TOQUE)} com toque, nos dois temas.', flush=True)


def percorrer(browser, url, pasta, toque=False):
    with browser.new_context(viewport=dict(width=390 if toque else 1366, height=844 if toque else 768),
                             has_touch=toque, is_mobile=toque, color_scheme='light') as ctx:
        p = ctx.new_page()
        erros = []
        p.on('pageerror', lambda erro: erros.append(str(erro)))
        p.goto(url + '/entrar')
        p.evaluate('document.fonts.ready')
        tema = p.locator('.menu-aparencia summary')
        if toque:
            tema.tap()
        else:
            p.keyboard.press('Tab')
            assert p.locator('.pular').evaluate('e => e.matches(":focus-visible")')
            p.keyboard.press('Tab')
            assert tema.evaluate('e => e.matches(":focus-visible")')
            p.keyboard.press('Enter')
            foto(p, pasta, 'menu-aparencia')
        p.get_by_text('Escuro', exact=True).click()
        p.keyboard.press('Escape')
        assert p.locator('html').get_attribute('data-tema') == 'escuro'
        p.get_by_label('Usuário', exact=True).fill('exemplo')
        p.get_by_label('Senha', exact=True).fill('exemplo ilustrativo')
        p.get_by_role('button', name='Mostrar senha').click()
        assert p.locator('#senha').get_attribute('type') == 'text'
        if not toque:
            foto(p, pasta, 'senha-visivel')
        p.get_by_role('button', name='Ocultar senha').click()
        p.locator('form').evaluate("""form => form.addEventListener('submit', () => {
            sessionStorage.setItem('ensaio-envio', String(form.getAttribute('aria-busy') === 'true'
                && form.querySelector('button[type=submit]').disabled));
        })""")
        with p.expect_response(lambda r: r.request.method == 'POST' and r.url.endswith('/entrar')) as tentativa:
            p.get_by_role('button', name='Entrar').click()
        assert tentativa.value.status == 401
        assert p.get_by_role('alert').is_visible()
        if not toque:
            foto(p, pasta, 'erro-autenticacao')
        assert p.evaluate("sessionStorage.getItem('ensaio-envio')") == 'true'
        p.get_by_role('link', name='Criar conta').click()
        assert p.locator('html').get_attribute('data-tema') == 'escuro'
        usuario = 'pessoa-' + ('mobile' if toque else 'desktop')
        senha = token_urlsafe(24)
        p.get_by_label('Nome completo').fill('Lia Vale')
        p.get_by_label('Nome de usuário').fill(usuario)
        p.get_by_label('Senha', exact=True).fill(senha)
        p.get_by_label('Confirmação de senha', exact=True).fill(senha + 'x')
        p.get_by_role('button', name='Mostrar confirmação de senha').click()
        assert p.locator('#senha').get_attribute('type') == 'password'
        assert p.locator('#confirmacao').get_attribute('type') == 'text'
        p.get_by_role('button', name='Criar conta').click()
        assert p.get_by_role('alert').is_visible() and p.locator('#nome').input_value() == 'Lia Vale'
        assert p.locator('#senha').input_value() == p.locator('#confirmacao').input_value() == ''
        p.locator('#senha').fill(senha)
        p.locator('#confirmacao').fill(senha)
        if not toque:
            p.set_viewport_size(dict(width=900, height=700))
            assert not p.locator('aside').is_visible()
            assert p.locator('#usuario').input_value() == usuario
            p.set_viewport_size(dict(width=1366, height=768))
            assert p.locator('aside').is_visible()
        p.get_by_role('button', name='Criar conta').click()
        assert p.get_by_role('status').inner_text().startswith('Conta criada')
        p.locator('#usuario').fill(usuario)
        p.locator('#senha').fill(senha)
        p.get_by_role('button', name='Entrar').click()
        p.wait_for_url(url + '/cliente/')
        assert 'Lia Vale' in p.locator('h1').inner_text()
        assert not p.locator('.menu-ambiente').count()
        assert p.goto(url + '/gestao/').status == 403
        assert not erros, erros


def main():
    from playwright.sync_api import sync_playwright
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--chrome')
    cli.add_argument('--capturas', type=Path)
    args = cli.parse_args()
    if args.capturas:
        args.capturas.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory() as tmp, sync_playwright() as pw:
        app = demo_temporaria(Path(tmp), token_urlsafe(24))
        with make_server('127.0.0.1', 0, app, threaded=True) as servidor, pw.chromium.launch(executable_path=args.chrome) as browser:
            thread = Thread(target=servidor.serve_forever)
            thread.start()
            try:
                url = f'http://127.0.0.1:{servidor.server_port}'
                conferir_telas(browser, url, args.capturas)
                for toque in [False, True]:
                    percorrer(browser, url, args.capturas, toque)
                print(f'Cadastro, login e isolamento em desktop e celular emulado. Chrome {browser.version}')
            finally:
                servidor.shutdown()
                thread.join()
                app.extensions['escritor'].fechar()


if __name__ == '__main__':
    main()
