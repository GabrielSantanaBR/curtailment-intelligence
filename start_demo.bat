@echo off
setlocal
if not exist .venv (
  py -m venv .venv
)
call .venv\Scripts\activate
python -m pip install -r requirements.txt
if not exist artifacts\curtailment_classifier.joblib python scripts\bootstrap_demo.py
python -m uvicorn app.main:app --reload
