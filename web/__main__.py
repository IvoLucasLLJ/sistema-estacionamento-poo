from web import create_app


def main():
    app = create_app()
    escritor = app.extensions['escritor']
    try:
        escritor.abrir()
        app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False, threaded=True, processes=1)
    except OSError as erro:
        raise SystemExit(str(erro)) from erro
    finally:
        escritor.fechar()


if __name__ == '__main__':
    main()
