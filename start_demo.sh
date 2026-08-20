#!/usr/bin/env bash
set -euo pipefail
if [ ! -d .venv ]; then python3 -m venv .venv; fi
source .venv/bin/activate
python -m pip install -r requirements.txt
if [ ! -f artifacts/curtailment_classifier.joblib ]; then python scripts/bootstrap_demo.py; fi
python -m uvicorn app.main:app --reload
