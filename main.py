from view.ui_texto import menu
from persistence.caminhos import historico_local
from persistence.exclusividade import EscritorLocal

if __name__ == "__main__":
    historico = historico_local()
    escritor = EscritorLocal(historico)
    try:
        escritor.abrir()
        menu(historico)
    except (EOFError, KeyboardInterrupt):
        raise SystemExit("Terminal interrompido. Confira o histórico ao reabrir.") from None
    except OSError as erro:
        raise SystemExit(str(erro)) from erro
    finally:
        escritor.fechar()
