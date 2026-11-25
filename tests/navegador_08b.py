"""Ensaio administrativo em Chromium, com arquivos exclusivos por percurso."""
import argparse
from pathlib import Path
from secrets import token_urlsafe
from tempfile import TemporaryDirectory
from threading import Thread
from unittest.mock import patch

from werkzeug.serving import make_server

from controller.controller import Controller
from tests.cenario_gestao import preparar_p0
from web import create_app


def percorrer(browser, raiz, largura, capturas):
    arquivo = raiz / 'historico.json'
    s = preparar_p0(arquivo)
    app = create_app(dict(DADOS=raiz, HISTORICO=arquivo, CONTAS=raiz/'contas.json',
                          SECRET_KEY=None, SESSION_COOKIE_SECURE=False))
    auth = app.extensions['autenticacao']
    senha = token_urlsafe(32)
    auth.provisionar('gestor.demo', senha, 'gestao')
    auth.provisionar('lia.demo', senha, 'cliente', s.cliente_do_veiculo('AV1')['identificador'])
    with make_server('127.0.0.1', 0, app, threaded=True) as servidor:
        thread = Thread(target=servidor.serve_forever)
        thread.start()
        ctx = browser.new_context(viewport={'width':largura,'height':900}, is_mobile=largura<768,
                                  has_touch=largura<768, color_scheme='light', locale='pt-BR')
        p = ctx.new_page()
        p.set_default_timeout(5000)
        erros = []
        p.on('pageerror', lambda erro: erros.append(str(erro)))
        url = f'http://127.0.0.1:{servidor.server_port}'

        def titulo(nome):
            p.get_by_role('heading', name=nome, exact=True).first.wait_for()

        def clicar(nome):
            p.get_by_role('button', name=nome, exact=True).click()

        def seguir(nome):
            p.locator('main').get_by_role('link', name=nome, exact=True).first.click()

        def navegar(nome):
            menu = p.locator('[data-menu]')
            if menu.is_visible() and menu.get_attribute('aria-expanded')=='false':
                menu.click()
            p.locator('nav').get_by_role('link', name=nome, exact=True).click()

        def foto(nome):
            if capturas:
                p.evaluate('document.fonts.ready')
                p.screenshot(path=capturas/f'08b-{largura}-{nome}.png', full_page=True)

        def login(nome):
            p.get_by_label('Usuário', exact=True).fill(nome)
            p.get_by_label('Senha', exact=True).fill(senha)
            clicar('Entrar')

        def cabe():
            assert p.evaluate('document.documentElement.scrollWidth <= innerWidth'), (largura,p.url)

        try:
            p.goto(url)
            p.keyboard.press('Tab')
            assert p.locator(':focus').get_attribute('href') == '#principal'
            login('gestor.demo')
            titulo('Visão geral')
            assert 'R$ 40,005' in p.locator('#financeiro').inner_text()
            foto('dashboard')
            navegar('Mapa de vagas')
            seguir('Vaga 2 · ocupada')
            seguir('Ver estadia')
            seguir('Preparar saída')
            p.get_by_label('Duração em horas').fill('1,225')
            clicar('Consultar cobrança')
            assert all(v in p.locator('.conta').inner_text() for v in ('R$ 12,25','R$ 6,125','R$ 6,13'))
            seguir('Revisar pagamento')
            titulo('Confirmar pagamento')
            cabe()
            foto('revisao')
            salvar = Controller.salvar
            def perder_resposta(ctrl):
                salvar(ctrl)
                raise OSError('falha simulada após a publicação do arquivo temporário')
            with patch.object(Controller,'salvar',autospec=True,side_effect=perder_resposta) as tentativa:
                clicar('Confirmar pagamento simulado')
                titulo('Resultado incerto')
                foto('recuperacao')
                seguir('Consultar estado')
                assert p.url.endswith('/estadias/22?recuperar=1')
                tentativa.assert_called_once()
            titulo('Estadia 22')
            navegar('Pagamentos')
            seguir('Continuar saída')
            assert 'Veículo na vaga 2' in p.locator('main').inner_text()
            assert s.consultar_faturamento()['reais']=='40.005'
            clicar('Concluir saída paga')
            titulo('Comprovante acadêmico')
            assert s.consultar_faturamento()['reais']=='46.135'
            p.emulate_media(media='print')
            assert not p.locator('nav').is_visible()
            assert not p.locator('[data-imprimir]').is_visible()
            assert p.get_by_text('Sem valor fiscal.',exact=False).is_visible()
            assert p.pdf(format='A4').startswith(b'%PDF-')
            foto('comprovante')
            p.emulate_media(media='screen')
            navegar('Histórico')
            p.get_by_label('Tipo de evento').select_option('saida_cliente')
            p.get_by_label('Evento, estadia, placa ou cliente').fill('AV1')
            clicar('Filtrar')
            seguir('Estadia 22')
            titulo('Comprovante acadêmico')
            navegar('Relatórios')
            assert 'R$ 46,135' in p.locator('main').inner_text()
            foto('relatorios')
            navegar('Clientes')
            p.get_by_label('Nome', exact=True).fill('Dora Nuvem')
            p.get_by_label('Categoria', exact=True).select_option('comum')
            clicar('Cadastrar cliente')
            titulo('Dora Nuvem')
            identificador = p.url.rsplit('/',1)[1]
            navegar('Veículos')
            p.get_by_label('Tipo',exact=True).select_option('carro')
            p.get_by_label('Placa',exact=True).fill('NV-7')
            p.get_by_label('Modelo',exact=True).fill('Bruma')
            clicar('Cadastrar veículo')
            titulo('NV7')
            p.get_by_label('Cliente responsável').select_option(identificador)
            clicar('Vincular cliente')
            seguir('Registrar entrada')
            p.get_by_label('Vaga livre').select_option('2')
            clicar('Revisar entrada')
            clicar('Confirmar entrada')
            seguir('Preparar saída')
            p.get_by_label('Duração em horas').fill('2')
            clicar('Consultar cobrança')
            seguir('Revisar pagamento')
            clicar('Confirmar pagamento simulado')
            assert 'Veículo na vaga 2' in p.locator('main').inner_text()
            clicar('Concluir saída paga')
            titulo('Comprovante acadêmico')
            assert s.consultar_faturamento()['reais'] == '66.135'
            navegar('Veículos')
            seguir('NV7')
            seguir('Registrar entrada')
            p.get_by_label('Vaga livre').select_option('2')
            clicar('Revisar entrada')
            clicar('Confirmar entrada')
            seguir('Preparar saída')
            p.get_by_label('Duração em horas').fill('0')
            clicar('Consultar cobrança')
            clicar('Concluir saída isenta')
            titulo('Comprovante acadêmico')
            assert 'Isento' in p.locator('main').inner_text()
            assert s.consultar_faturamento()['reais'] == '66.135'
            p.locator('.tema label').filter(has_text='Escuro').click()
            navegar('Relatórios')
            assert p.locator('html').get_attribute('data-tema')=='escuro'
            foto('relatorios-escuro')
            for w in (320,390,768,1440):
                p.set_viewport_size(dict(width=w,height=900))
                cabe()
            p.locator('.tema label').filter(has_text='Sistema').click()
            p.emulate_media(color_scheme='dark')
            p.wait_for_function("document.documentElement.dataset.tema === 'escuro'")
            p.reload()
            assert p.locator('html').get_attribute('data-tema')=='escuro'
            p.locator('summary').click()
            clicar('Sair')
            login('lia.demo')
            titulo('Olá, Lia Vale')
            assert p.goto(url+'/gestao/pagamentos').status==403
            p.goto(url+'/cliente/')
            csrf = p.locator('[name=csrf_token]').first.get_attribute('value')
            resposta = ctx.request.post(url+'/gestao/estadias/22/concluir',form={'csrf_token':csrf})
            assert resposta.status==403
            assert not erros, erros
            print(f'Gestão aprovada em {largura}px · {url} · Chromium {browser.version}')
        finally:
            ctx.close()
            servidor.shutdown()
            thread.join()
            app.extensions['escritor'].fechar()


def main():
    from playwright.sync_api import sync_playwright
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--chrome', help='Executável Chrome/Chromium')
    cli.add_argument('--capturas', type=Path)
    args = cli.parse_args()
    if args.capturas:
        args.capturas.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as pw, pw.chromium.launch(executable_path=args.chrome) as browser:
        for largura in (1440,390):
            with TemporaryDirectory(prefix='move-gestao-') as pasta:
                percorrer(browser,Path(pasta),largura,args.capturas)


if __name__ == '__main__':
    main()
