"""Zoom nativo do Chrome em um display Xvfb privado (Linux)."""
import json
import os
import subprocess
import sys
from pathlib import Path
from secrets import token_urlsafe
from tempfile import TemporaryDirectory

from playwright.sync_api import sync_playwright

from qa.desempenho import servidor
from tests.navegador_08c import login
from tests.test_contexto_acesso import demo_temporaria


def verificar():
    from Xlib import X, XK, display
    from Xlib.ext import xtest

    with TemporaryDirectory() as tmp, sync_playwright() as pw:
        senha = token_urlsafe()
        app = demo_temporaria(Path(tmp), token_urlsafe(), senha_master=senha)
        with servidor(app) as url, pw.chromium.launch(channel='chrome', headless=False,
                args=['--ozone-platform=x11','--window-size=1366,768']) as chrome, chrome.new_context(no_viewport=True) as ctx:
            p = ctx.new_page()
            p.goto(url+'/entrar')
            p.bring_to_front()
            tela = display.Display()
            try:
                janela = next(j for j in tela.screen().root.query_tree().children
                              if j.get_attributes().map_state == X.IsViewable
                              and any('chrome' in c.lower() for c in (j.get_wm_class() or ())))
                janela.set_input_focus(X.RevertToParent, X.CurrentTime)
                tela.sync()
                ctrl, igual = [tela.keysym_to_keycode(XK.string_to_keysym(k)) for k in ('Control_L','equal')]
                base = p.evaluate('devicePixelRatio')
                for _ in range(5):
                    anterior = p.evaluate('devicePixelRatio')
                    for evento, tecla in [(X.KeyPress,ctrl),(X.KeyPress,igual),(X.KeyRelease,igual),(X.KeyRelease,ctrl)]:
                        xtest.fake_input(tela, evento, tecla)
                    tela.sync()
                    p.wait_for_function('a => devicePixelRatio > a', arg=anterior, timeout=3000)
            finally:
                tela.close()
            assert abs(p.evaluate('devicePixelRatio') / base - 2) < .01
            saida = []
            for cor in ('light','dark'):
                p.emulate_media(color_scheme=cor)
                for rota in ('/entrar','/criar-conta'):
                    assert p.goto(url+rota).ok
                    assert p.locator('button[type=submit]').is_visible()
                    assert p.evaluate('document.documentElement.scrollWidth <= innerWidth')
                    saida.append((rota,cor,p.evaluate('innerWidth')))
            login_url = url+'/entrar'
            p.goto(login_url)
            login(p,'master.demo',senha)
            for rota in ('/gestao/', '/gestao/entrada', '/gestao/relatorios'):
                assert p.goto(url+rota).ok and p.evaluate('document.documentElement.scrollWidth <= innerWidth')
                saida.append((rota,'dark',p.evaluate('innerWidth')))
            print(json.dumps(dict(zoom='200%', paginas=saida, versao=chrome.version)))


if __name__ == '__main__':
    if os.environ.get('MOVE_QA_XVFB') == '1' and sys.argv[1:] == ['--display-privado']:
        verificar()
    else:
        subprocess.run(['xvfb-run','-a','-s','-screen 0 1600x1000x24',sys.executable,'-B',
                        '-m','qa.zoom','--display-privado'], env={**os.environ,'MOVE_QA_XVFB':'1'}, check=True)
