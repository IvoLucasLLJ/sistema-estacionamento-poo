#!/bin/sh
# Entrada compartilhada para ambientes Unix.
set -eu
raiz=$(CDPATH= cd -P "$(dirname "$0")" && pwd) || { echo "Não foi possível abrir a pasta do MOVE." >&2; exit 1; }
cd "$raiz"
if [ "$(uname -s)" = Darwin ]; then
    PATH="${PATH}:/opt/homebrew/bin:/usr/local/bin:/Library/Frameworks/Python.framework/Versions/Current/bin"
    export PATH
fi

if [ -n "${MOVE_PYTHON:-}" ]; then
    set_python=$MOVE_PYTHON
    if ! "$set_python" -IB -c 'import sys; sys.exit(not (3, 11) <= sys.version_info[:2] <= (3, 14))' 2>/dev/null; then
        echo "Python adequado não encontrado em MOVE_PYTHON. Indique o executável nativo do Python 3.14 ou 3.12." >&2
        exit 1
    fi
else
    set_python=
    for candidato in "$raiz/.venv/bin/python" python3.14 python3.12 python3 python3.13 python3.11; do
        if "$candidato" -IB -c 'import sys; sys.exit(not (3, 11) <= sys.version_info[:2] <= (3, 14))' 2>/dev/null; then
            set_python=$candidato
            break
        fi
    done
fi
if [ -z "$set_python" ]; then
    echo "Python adequado não encontrado. Instale Python 3.14 com venv e pip ou indique seu executável em MOVE_PYTHON." >&2
    exit 1
fi
exec "$set_python" -IB "$raiz/iniciar_move.py" "$@"
