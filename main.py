from view.ui_texto import menu
from persistence.exclusividade import EscritorLocal

if __name__ == "__main__":
    escritor = EscritorLocal("historico.json")
    try:
        escritor.abrir()
        menu()
    except OSError as erro:
        raise SystemExit(str(erro)) from erro
    finally:
        escritor.fechar()
