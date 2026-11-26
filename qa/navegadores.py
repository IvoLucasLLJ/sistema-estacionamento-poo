"""Reflow e acessibilidade em um servidor descartável. Uso: python -m qa.navegadores --help"""
import argparse
import json
from pathlib import Path
from secrets import token_urlsafe
from tempfile import TemporaryDirectory

from playwright.sync_api import sync_playwright

from qa.desempenho import servidor
from tests.navegador_08c import login
from tests.test_contexto_acesso import demo_temporaria


def conferir(motor, nome, url, senha, axe):
    achados = []
    pares = [(320,640),(360,800),(390,844),(430,932),(600,900),(768,1024),
             (1024,768),(1280,720),(1366,768),(1440,900),(1920,1080),(683,384)]
    contagem = 0
    with motor.new_context() as ctx:
        p = ctx.new_page()
        for cor in ('light', 'dark'):
            p.emulate_media(color_scheme=cor)
            for w,h in pares:
                p.set_viewport_size(dict(width=w, height=h))
                for rota in ('/entrar','/criar-conta'):
                    r = p.goto(url+rota)
                    assert r.ok
                    p.evaluate('document.fonts.ready')
                    assert p.locator('main form').is_visible()
                    assert p.evaluate('document.documentElement.scrollWidth <= innerWidth'), (nome, cor, w, rota)
                    contagem += 1
        p.set_viewport_size(dict(width=1366, height=768))
        for rota in ('/entrar','/criar-conta','/gestao/','/cliente/'):
            if rota == '/gestao/':
                p.goto(url+'/entrar')
                login(p, 'master.demo', senha)
            if rota == '/cliente/':
                p.locator('.menu-ambiente summary').focus()
                p.keyboard.press('Space')
                p.get_by_role('button', name='MOVE Cliente', exact=True).focus()
                p.keyboard.press('Enter')
                p.wait_for_url(url + '/cliente/')
            assert p.goto(url+rota).ok and p.url == url+rota
            if axe:
                for cor in ('light','dark'):
                    p.emulate_media(color_scheme=cor)
                    p.evaluate(axe.read_text(encoding='utf-8'))
                    rel = p.evaluate("""async () => (await axe.run(document, {
                      runOnly: {type:'tag', values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}
                    })).violations.map(v => ({regra:v.id,impacto:v.impact,elementos:v.nodes.map(n => n.target)}))""")
                    achados.append(dict(rota=rota,cor=cor,violacoes=rel))
    return dict(motor=nome, versao=motor.version, reflow=contagem, axe=achados)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('motor', choices=['chromium','firefox','webkit'])
    parser.add_argument('--executavel')
    parser.add_argument('--axe', type=Path)
    args = parser.parse_args()
    with TemporaryDirectory() as tmp, sync_playwright() as pw:
        senha = token_urlsafe()
        app = demo_temporaria(Path(tmp), token_urlsafe(), senha_master=senha)
        with servidor(app) as url, getattr(pw,args.motor).launch(executable_path=args.executavel) as motor:
            print(json.dumps(conferir(motor,args.motor,url,senha,args.axe), ensure_ascii=False, indent=2))
