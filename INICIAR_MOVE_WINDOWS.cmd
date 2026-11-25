@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "PYTHON_MANAGER_AUTOMATIC_INSTALL=false"
set "PYLAUNCHER_ALLOW_INSTALL="
set "PYLAUNCHER_ALWAYS_INSTALL="
pushd "%~dp0" || exit /b 1
if defined MOVE_PYTHON goto indicado
if exist ".venv\Scripts\python.exe" goto existente
py -3.14 -I -c "import sys" >nul 2>&1 && goto py314
py -3.12 -I -c "import sys" >nul 2>&1 && goto py312
python -I -c "import sys" >nul 2>&1 && goto padrao
goto ausente
:indicado
"%MOVE_PYTHON%" -I -c "import sys" >nul 2>&1 || goto ausente
"%MOVE_PYTHON%" -X utf8 -IB "iniciar_move.py" %*
goto fim
:existente
".venv\Scripts\python.exe" -I -c "import sys" >nul 2>&1 || goto invalida
".venv\Scripts\python.exe" -X utf8 -IB "iniciar_move.py" %*
goto fim
:py314
py -3.14 -X utf8 -IB "iniciar_move.py" %*
goto fim
:py312
py -3.12 -X utf8 -IB "iniciar_move.py" %*
goto fim
:padrao
python -X utf8 -IB "iniciar_move.py" %*
goto fim
:invalida
echo A .venv existente e incompativel. Preserve-a com outro nome e abra o MOVE novamente. 1>&2
popd
exit /b 1
:ausente
echo Python adequado nao encontrado. Instale Python 3.14 ou 3.12 para Windows ou confira MOVE_PYTHON. 1>&2
popd
exit /b 1
:fim
set "resultado=%errorlevel%"
popd
exit /b %resultado%
