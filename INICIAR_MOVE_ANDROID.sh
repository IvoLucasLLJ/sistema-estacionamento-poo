#!/system/bin/sh
set -eu
if [ ! -x /system/bin/getprop ] || [ -z "${PREFIX:-}" ]; then
    echo 'Abra este inicializador dentro do Termux no Android 15 ou superior.' >&2
    exit 1
fi
raiz=$(CDPATH= cd -P "$(dirname "$0")" && pwd) || exit 1
python=${MOVE_PYTHON:-"$PREFIX/bin/python"}
if [ ! -x "$python" ]; then
    echo 'Python adequado não encontrado. No Termux, execute: pkg install python python-pip python-ensurepip-wheels' >&2
    exit 1
fi
exec "$python" -IB "$raiz/iniciar_move.py" --termux "$@"
