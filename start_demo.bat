@echo off
setlocal

where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher "py" nao encontrado. Instale Python 3.11+.
  exit /b 1
)

if not exist .venv (
  echo Criando ambiente virtual...
  py -m venv .venv
)

call .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts\bootstrap_demo.py
python -m uvicorn app.main:app --reload
