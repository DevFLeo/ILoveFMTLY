@echo off
rem Instala o que faltar, roda os testes (rodar.log) e abre o ILoveFMTLY.
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe python -m venv .venv
echo Instalando dependencias... > rodar.log
.venv\Scripts\python -m pip install -q -r requirements.txt >> rodar.log 2>&1
echo Rodando testes... >> rodar.log
.venv\Scripts\python -m pytest -q >> rodar.log 2>&1
echo FIM DOS TESTES >> rodar.log
start "" .venv\Scripts\pythonw.exe app.py
