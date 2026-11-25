#!/bin/sh
set -eu
raiz=$(CDPATH= cd -P "$(dirname "$0")" && pwd) || { echo "Não foi possível abrir a pasta do MOVE." >&2; exit 1; }
exec /bin/sh "$raiz/INICIAR_MOVE_LINUX.sh" "$@"
