"""Chrome real com fixture descartável. A auditoria axe usa uma cópia local indicada por argumento."""
import argparse
import json
from contextlib import contextmanager, nullcontext
from pathlib import Path
from secrets import token_urlsafe
from tempfile import TemporaryDirectory
from threading import Thread

from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server
from web.cenario_inteligente import preparar, abrir
from web.demonstracao import provisionar_demonstracao

TELAS = [(1440,900),(768,1024),(1024,768),(390,844),(844,390)]


@contextmanager
def demonstracao(raiz):
    preparar(raiz)
    app, lia = abrir(raiz)
    senha = token_urlsafe(24)
    auth = app.extensions['autenticacao']
    for usuario, papel, titular in [('master.demo','gestao',None),('cliente.demo','cliente',lia),('gestao.demo','gestao',None)]:
        auth.provisionar(usuario, senha, papel, titular)
    provisionar_demonstracao(app, lia)
    with make_server('127.0.0.1',0,app,threaded=True) as servidor:
        thread = Thread(target=servidor.serve_forever)
        thread.start()
        try:
            yield f'http://127.0.0.1:{servidor.server_port}', lia, senha
        finally:
            servidor.shutdown()
            thread.join()


def percorrer(browser, base, lia, senha, dimensoes, tema, pasta, axe):
    w,h = dimensoes
    toque = w != 1440
    with browser.new_context(viewport=dict(width=w,height=h), has_touch=toque,is_mobile=toque,
                             color_scheme=tema, locale='pt-BR') as ctx:
        p = ctx.new_page()
        p.set_default_timeout(6000)
        erros = []
        p.on('pageerror',lambda exc: erros.append(str(exc)))
        def acionar(elemento):
            navega = elemento.evaluate("el => el.matches('a[href], button[type=submit]')")
            with p.expect_navigation(wait_until='domcontentloaded') if navega else nullcontext():
                if toque:
                    elemento.tap()
                else:
                    elemento.click()
        def botao(nome):
            acionar(p.get_by_role('button',name=nome,exact=True))
        def portal(nome):
            acionar(p.locator('.menu-ambiente summary'))
            botao('MOVE '+nome)
            p.wait_for_url('**/'+('gestao' if nome=='Gestão' else 'cliente')+'/')
        def cabe():
            assert p.evaluate('document.documentElement.scrollWidth <= innerWidth'), (p.url,w)
        def foto(nome):
            cabe()
            p.evaluate('document.fonts.ready')
            p.screenshot(path=pasta/f'{w}x{h}-{tema}-{nome}.png')
        def auditar(nome):
            p.evaluate(axe.read_text(encoding='utf-8'))
            resultado=p.evaluate("""async () => (await axe.run(document,{runOnly:{type:'tag',
                values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}})).violations.map(
                v=>({id:v.id,alvos:v.nodes.map(n=>n.target)}))""")
            print('axe', nome, w, tema, json.dumps(resultado),flush=True)
            return resultado
        p.goto(base+'/entrar')
        p.get_by_label('Usuário', exact=True).fill('master.demo')
        p.get_by_label('Senha', exact=True).fill(senha)
        botao('Entrar')
        p.wait_for_url('**/gestao/')
        p.goto(base+'/gestao/vagas')
        assert p.locator('.grade-vagas li').count()==20
        p.get_by_role('link',name='Próxima',exact=True).focus()
        p.keyboard.press('Enter')
        assert 'Página 2 de 10' in p.locator('main').inner_text()
        p.locator('[name=setor]').select_option('9')
        p.locator('[name=classificacao]').select_option('pcd')
        botao('Filtrar')
        assert p.locator('.grade-vagas li').count()==4
        p.locator('[name=setor]').select_option('')
        p.locator('[name=classificacao]').select_option('')
        p.get_by_label('Número da vaga').fill('176')
        botao('Filtrar')
        acionar(p.locator('.grade-vagas a'))
        assert 'Simular indisponibilidade' not in p.locator('main').inner_text()
        p.goto(base+'/gestao/vagas?setor=9')
        if toque:
            p.locator('.grade-vagas').scroll_into_view_if_needed()
        foto('mapa')
        resultados = auditar('mapa') if w in (390,1440) else []
        portal('Cliente')
        p.goto(base+'/cliente/disponibilidade')
        p.get_by_label('Meu veículo').select_option('EV200')
        p.wait_for_url('**/cliente/disponibilidade?**')
        p.locator('[name=classificacao]').select_option('pcd')
        botao('Consultar vagas')
        assert p.locator('.grade-vagas a').count()==4
        if toque:
            p.locator('.grade-vagas').scroll_into_view_if_needed()
        foto('reserva')
        if w in (390,1440):
            resultados += auditar('reserva')
        acionar(p.locator('.grade-vagas a').first)
        botao('Confirmar reserva')
        assert 'Vaga 177' in p.locator('main').inner_text()
        portal('Gestão')
        p.goto(base+'/gestao/entrada?cliente_id='+lia+'&placa=EV200')
        def numeros():
            return p.locator('#escolha-vaga option').evaluate_all('els=>els.map(e=>e.value).filter(Boolean)')
        assert numeros()==['177']
        p.get_by_label('Veículo vinculado').select_option('HB200')
        p.wait_for_url('**/entrada?**placa=HB200')
        assert numeros()==['120']
        p.get_by_label('Veículo vinculado').select_option('EV200')
        p.wait_for_url('**/entrada?**placa=EV200')
        p.get_by_label('Vaga livre').select_option('177')
        botao('Revisar entrada')
        p.get_by_role('checkbox').check()
        botao('Confirmar entrada')
        assert 'Exclusiva PcD' in p.locator('main').inner_text()
        eid = p.url.split('/')[-1]
        acionar(p.get_by_role('link',name='Preparar saída',exact=True).last)
        p.get_by_label('Duração em horas').fill('1,225')
        botao('Consultar cobrança')
        acionar(p.get_by_role('link',name='Revisar pagamento'))
        botao('Confirmar pagamento simulado')
        assert 'Veículo na vaga 177' in p.locator('main').inner_text()
        botao('Concluir saída paga')
        portal('Cliente')
        p.goto(base+f'/cliente/estadias/{eid}/comprovante')
        assert 'R$ 6,13' in p.locator('.conta').inner_text()
        cabe()
        if w==1440:
            foto('comprovante')
        if w == 1440 and tema == 'light':
            # Um segundo percurso testa uma avaria entre a reserva e a entrada.
            p.goto(base+'/cliente/disponibilidade?placa=EV200&numero=117')
            acionar(p.locator('.grade-vagas a'))
            botao('Confirmar reserva')
            portal('Gestão')
            p.goto(base+'/gestao/vagas?vaga=117')
            botao('Simular indisponibilidade')
            p.goto(base+'/gestao/entrada?cliente_id='+lia+'&placa=EV200')
            assert numeros() == [] and 'Carregador indisponível' in p.content()
            p.goto(base+'/gestao/vagas?vaga=117')
            botao('Restabelecer carregador')
            portal('Cliente')
            p.goto(base+'/cliente/disponibilidade')
            registro = p.locator('.registro').filter(has_text='EV200')
            acionar(registro.get_by_role('button',name='Cancelar reserva'))
            p.goto(base+'/cliente/disponibilidade?placa=EV200&numero=3&vip=1')
            acionar(p.locator('.grade-vagas a'))
            botao('Confirmar reserva')
            portal('Gestão')
            p.goto(base+'/gestao/vagas?destinacao=vip')
            assert p.locator('.grade-vagas a').count()==2
            foto('vip')
            p.goto(base+'/gestao/clientes/'+lia)
            form = p.locator('form[action$="/autorizacoes"]')
            form.locator('[name=placa]').select_option('EV200')
            form.locator('[name=grupo]').select_option('gestante')
            form.locator('[name=beneficiario]').select_option('passageiro')
            form.locator('[name=numero_beneficiario]').fill('5')
            form.locator('[name=conferencia]').select_option('administrativa')
            from datetime import date, timedelta
            form.locator('[name=validade]').fill((date.today()+timedelta(days=7)).isoformat())
            botao('Registrar conferência')
            revogar = p.locator('.registro-evento').filter(has_text='Gestante').get_by_role('button',name='Revogar')
            acionar(revogar)
            assert revogar.count()==0
            print('Recarga, avaria, recuperação, cancelamento, VIP e conferência/revogação aprovados.',flush=True)
        assert not erros, erros
        print(f'Jornada {w} × {h} · {tema} aprovada.',flush=True)
        return resultados


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chrome', required=True)
    parser.add_argument('--axe',type=Path,required=True)
    parser.add_argument('--capturas',type=Path,required=True)
    args=parser.parse_args()
    args.capturas.mkdir(parents=True,exist_ok=True)
    problemas=[]
    with sync_playwright() as pw, pw.chromium.launch(executable_path=args.chrome) as browser:
        print('Chrome',browser.version,flush=True)
        for d in TELAS:
            for tema in ('light','dark'):
                with TemporaryDirectory() as tmp, demonstracao(Path(tmp)/'demo') as dados:
                    problemas.extend(percorrer(browser,*dados,d,tema,args.capturas,args.axe))
    if problemas:
        raise SystemExit(f'{len(problemas)} ocorrências axe na amostra')


if __name__=='__main__':
    main()
