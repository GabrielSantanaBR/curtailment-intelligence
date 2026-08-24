#!/usr/bin/env sh
set -eu

# Runtime bootstrap seeds the database currently configured by DATABASE_URL.
python scripts/bootstrap_demo.py --skip-train

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
