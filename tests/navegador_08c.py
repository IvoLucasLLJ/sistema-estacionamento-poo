"""Jornadas pessoais em dois contextos Chromium e um histórico temporário por largura."""
import argparse
import json
from pathlib import Path
from secrets import token_urlsafe
from tempfile import TemporaryDirectory
from threading import Thread
from unittest.mock import patch
from uuid import UUID

from werkzeug.serving import make_server

from tests.cenario_gestao import preparar_p0
from web import create_app


def preparar_servidor(pasta, senha):
    # A Gestão executará as duas entradas na interface. Usa-se o prefixo válido anterior a elas.
    with TemporaryDirectory() as origem:
        base = Path(origem) / 'base.json'
        preparar_p0(base)
        eventos = json.loads(base.read_text())
    assert [(e['acao'], e['estadia_id']) for e in eventos[-2:]] == [
        ('entrada_cliente', 22), ('entrada_cliente', 23)]
    historico = pasta / 'historico.json'
    with historico.open('x') as destino:
        json.dump(eventos[:-2], destino)
    app = create_app(dict(DADOS=pasta, HISTORICO=historico, CONTAS=pasta / 'contas.json',
                          SECRET_KEY=None, SESSION_COOKIE_SECURE=False))
    auth = app.extensions['autenticacao']
    auth.provisionar('gestor.demo', senha, 'gestao')
    for numero, nome in [(1, 'lia.demo'), (3, 'noa.demo'), (4, 'iara.demo')]:
        auth.provisionar(nome, senha, 'cliente', str(UUID(int=numero)))
    return app


def login(pagina, nome, senha):
    pagina.get_by_label('Usuário', exact=True).fill(nome)
    pagina.get_by_label('Senha', exact=True).fill(senha)
    pagina.get_by_role('button', name='Entrar', exact=True).click()


def destino(pagina, nome):
    nav = pagina.get_by_role('navigation')
    link = nav.get_by_role('link', name=nome, exact=True)
    if not link.is_visible():
        nav.get_by_role('button', name='Mais', exact=True).click()
    link.click()


def entrada(gestao, url, placa, vaga):
    gestao.goto(url + '/gestao/entrada')
    gestao.get_by_label('Cliente', exact=True).select_option(str(UUID(int=1)))
    gestao.get_by_role('button', name='Consultar veículos').click()
    gestao.get_by_label('Veículo vinculado').select_option(placa)
    gestao.get_by_label('Vaga livre').select_option(str(vaga))
    gestao.get_by_role('button', name='Revisar entrada').click()
    gestao.get_by_role('button', name='Confirmar entrada').click()


def jornadas(browser, app, url, senha, largura, capturas):
    config = dict(viewport={'width': largura, 'height': 900}, has_touch=largura < 768,
                  is_mobile=largura < 768, color_scheme='light', locale='pt-BR')
    with browser.new_context(**config) as admin, browser.new_context(**config) as pessoal:
        gestao, cliente = admin.new_page(), pessoal.new_page()
        erros = []
        for pagina in (gestao, cliente):
            pagina.set_default_timeout(6000)
            pagina.on('pageerror', lambda erro: erros.append(str(erro)))

        def conteudo():
            return cliente.locator('main').inner_text()

        def foto(nome):
            if capturas:
                cliente.evaluate('document.fonts.ready')
                cliente.screenshot(path=capturas / f'08c-{largura}-{nome}.png', full_page=True)

        def abrir_estadia():
            cliente.locator('main').get_by_role('link', name='AV1 · Vaga 2').click()
            assert cliente.url.endswith('/cliente/estadias/22')

        def sem_terceiros():
            html = cliente.content()
            for texto in ('LEG9', 'CB3', 'NM4', 'R$ 40,01', 'R$ 46,14', '/gestao/', str(UUID(int=2))):
                assert texto not in html, (cliente.url, texto)

        gestao.goto(url)
        login(gestao, 'gestor.demo', senha)
        cliente.goto(url)
        login(cliente, 'lia.demo', senha)
        assert 'Nenhuma estadia ativa' in conteudo()
        entrada(gestao, url, 'AV1', 2)
        entrada(gestao, url, 'AM2', 5)
        cliente.reload()
        assert 'AV1' in conteudo() and 'AM2' in conteudo()
        assert 'R$' not in conteudo()
        sem_terceiros()
        foto('inicio-p0')

        destino(cliente, 'Estadias')
        abrir_estadia()
        assert 'Sem pagamento confirmado' in conteudo()
        destino(cliente, 'Veículos')
        cliente.get_by_role('link', name='Ver estadia 22 · Vaga 2').click()
        assert cliente.url.endswith('/cliente/estadias/22')
        destino(cliente, 'Disponibilidade')
        cliente.get_by_role('link', name='Atualizar', exact=True).click()
        assert '30% de ocupação' in conteudo() and '7 de 10 vagas livres' in conteudo()
        sem_terceiros()

        gestao.goto(url + '/gestao/estadias/22/saida')
        gestao.get_by_label('Duração em horas').fill('1,225')
        gestao.get_by_role('button', name='Consultar cobrança').click()
        gestao.get_by_role('link', name='Revisar pagamento').click()
        gestao.get_by_role('button', name='Confirmar pagamento simulado').click()
        gestao.goto(url + '/gestao/')
        assert 'R$ 40,01' in gestao.locator('#financeiro').inner_text()
        cliente.reload()
        assert '30% de ocupação' in conteudo()
        destino(cliente, 'Estadias')
        assert 'R$ 6,13' in conteudo() and 'Sem pagamento confirmado' in conteudo()
        foto('estadias-p1')
        abrir_estadia()
        assert 'ainda estacionado na vaga 2' in conteudo()
        assert cliente.locator('.conta dd').all_inner_texts() == ['1,225 h', 'R$ 12,25', 'R$ 6,13', 'R$ 6,13']

        gestao.goto(url + '/gestao/estadias/22')
        gestao.get_by_role('button', name='Concluir saída paga').click()
        gestao.goto(url + '/gestao/')
        assert 'R$ 46,14' in gestao.locator('#financeiro').inner_text()
        destino(cliente, 'Disponibilidade')
        assert '20% de ocupação' in conteudo()
        destino(cliente, 'Estadias')
        assert 'AM2' in conteudo() and 'AV1' not in conteudo()
        destino(cliente, 'Meu histórico')
        cliente.locator('.filtros-pessoais summary').click()
        cliente.get_by_label('Situação', exact=True).select_option('paga')
        cliente.get_by_role('button', name='Filtrar', exact=True).click()
        cliente.get_by_role('link', name='Estadia 22 · AV1').click()
        cliente.get_by_role('link', name='Ver comprovante').click()
        assert 'Saída paga' in conteudo()
        for texto in ('1,225 h', 'R$ 12,25', 'Desconto', 'R$ 6,13', 'Sem valor fiscal'):
            assert texto in conteudo()
        sem_terceiros()
        # A prévia nativa e Page.printToPDF são operações de impressão distintas no Chromium.
        with pessoal.new_page() as previa:
            previa.goto(cliente.url)
            previa.evaluate("window.addEventListener('beforeprint', () => document.body.dataset.imprimiu = 'sim')")
            previa.get_by_role('button', name='Imprimir comprovante').click()
            previa.wait_for_function("document.body.dataset.imprimiu === 'sim'")
        cliente.emulate_media(media='print')
        assert not cliente.locator('nav').is_visible()
        assert cliente.pdf(format='A4').startswith(b'%PDF-')
        foto('comprovante')
        cliente.emulate_media(media='screen')

        destino(cliente, 'Tarifas e benefícios')
        assert '50% de desconto' in conteudo()
        cliente.get_by_role('link', name='Ver meu perfil').click()
        cliente.locator('.tema label').filter(has_text='Escuro').click()
        destino(cliente, 'Meu histórico')
        assert cliente.locator('html').get_attribute('data-tema') == 'escuro'
        foto('historico-escuro')
        for w in (320, 390, 768, 1440):
            cliente.set_viewport_size(dict(width=w, height=900))
            for rota in ('', 'estadias', 'veiculos', 'disponibilidade', 'tarifas', 'historico',
                         'estadias/22/comprovante', 'perfil'):
                res = cliente.goto(url + '/cliente/' + rota)
                assert res.status == 200
                assert cliente.evaluate('document.documentElement.scrollWidth <= innerWidth'), (w, rota)
                assert cliente.locator('html').get_attribute('data-tema') == 'escuro'
            if w == 320:
                destino(cliente, 'Início')
                cliente.locator('[data-mais]').click()
                assert cliente.get_by_role('link', name='Meu perfil', exact=True).is_visible()
                cliente.keyboard.press('Escape')
                assert cliente.locator('[data-mais]').evaluate("el => el === document.activeElement")
        cliente.set_viewport_size(config['viewport'])
        destino(cliente, 'Meu perfil')
        cliente.locator('.tema label').filter(has_text='Sistema').click()
        cliente.emulate_media(color_scheme='dark')
        cliente.wait_for_function("document.documentElement.dataset.tema === 'escuro'")
        cliente.get_by_role('button', name='Encerrar sessão').click()
        assert cliente.url.endswith('/entrar')
        login(cliente, 'lia.demo', senha)
        with patch('web.seguranca.agora', return_value=10**10):
            assert cliente.goto(url + '/cliente/estadias/22/comprovante').status == 401
        cliente.get_by_role('link', name='Entrar novamente').click()
        login(cliente, 'lia.demo', senha)
        destino(cliente, 'Meu histórico')
        assert 'Estadia 22' in conteudo()
        assert cliente.goto(url + '/cliente/estadias/19/comprovante').status == 404
        mensagem = conteudo()
        assert cliente.goto(url + '/cliente/estadias/9999/comprovante').status == 404
        assert mensagem == conteudo()
        assert cliente.goto(url + '/gestao/').status == 403

        for usuario, rota, evidencia in [('iara.demo', 'veiculos', 'Nenhum veículo vinculado'),
                                         ('noa.demo', 'estadias/17/comprovante', 'Saída isenta')]:
            pessoal.clear_cookies()
            cliente.goto(url)
            login(cliente, usuario, senha)
            cliente.goto(url + '/cliente/' + rota)
            assert evidencia in conteudo()
        assert not erros, erros
        print(f'Sete jornadas pessoais e ciclo Gestão–Cliente aprovados em {largura} px · {url}')


def main():
    from playwright.sync_api import sync_playwright

    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--chrome', help='Executável Chrome/Chromium já instalado.')
    cli.add_argument('--capturas', type=Path, help='Diretório externo para os PNGs.')
    args = cli.parse_args()
    if args.capturas:
        args.capturas.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw, pw.chromium.launch(executable_path=args.chrome) as browser:
        for largura in (1440, 390):
            with TemporaryDirectory(prefix='move-portal-') as tmp:
                senha = token_urlsafe(32)
                app = preparar_servidor(Path(tmp), senha)
                with make_server('127.0.0.1', 0, app, threaded=True) as servidor:
                    thread = Thread(target=servidor.serve_forever)
                    thread.start()
                    try:
                        jornadas(browser, app, f'http://127.0.0.1:{servidor.server_port}', senha, largura, args.capturas)
                    finally:
                        servidor.shutdown()
                        thread.join()
                        app.extensions['escritor'].fechar()
        print(f'Chromium {browser.version}')


if __name__ == '__main__':
    main()
