# Curtailment Intelligence

**Decision-support platform for renewable-generation curtailment** — built as a strong pre-hackathon foundation for the COPPE/UFRJ AI Hackathon 2026, Challenge 1.

The system implements the complete product loop the team proposed:

1. **Understand** where/when curtailment happens.
2. **Predict** curtailment risk and estimated curtailed energy.
3. **Explain** the prediction with human-readable drivers.
4. **Optimize** mitigation scenarios under explicit technical constraints.
5. **Measure** recovered MWh, remaining curtailed energy, estimated value preserved and avoided emissions under configurable assumptions.

> The repository can generate a realistic **synthetic renewable-operation dataset** and train demo models locally so the whole application works before the official competition dataset is available. Generated datasets and trained artifacts are intentionally not versioned. The app clearly labels synthetic/demo outputs and does **not** pretend that mock or synthetic data are ONS measurements.

## What is already implemented

- FastAPI backend with typed API and OpenAPI docs.
- SQLite out of the box; PostgreSQL-ready through `DATABASE_URL`.
- SQLAlchemy persistence for plants, predictions and optimization scenarios.
- Synthetic data generator covering wind + solar, temporal seasonality, network stress and curtailment events.
- Time-aware ML training pipeline:
  - logistic-regression baseline;
  - histogram gradient boosting classifier;
  - random-forest curtailed-energy regressor;
  - threshold selection on validation data;
  - PR-AUC, ROC-AUC, F1, precision, recall, Brier score and MAE/RMSE metrics.
- Lightweight explanation layer using local feature perturbations against the trained model.
- Scenario optimizer with hourly battery + flexible-load dispatch using linear programming (`scipy.optimize.linprog`).
- Impact module: MWh recovered, recovery %, estimated value preserved, and configurable avoided-emissions estimate.
- ONS ingestion adapter with resilient column-name normalization and a download helper for the public constrained-off datasets.
- Full dashboard served directly by FastAPI: no npm build required for the demo.
- Optional React/Vite frontend source for the team to evolve independently.
- CSV upload endpoint for testing a dataset against the normalization pipeline.
- Automated tests and GitHub Actions CI.
- Docker / Docker Compose setup.
- Architecture, API, data-contract and competition-transition documentation.

## Run locally — fastest path

Python 3.11+ is recommended.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python scripts/bootstrap_demo.py
uvicorn app.main:app --reload
```

Open:

- Dashboard: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

`bootstrap_demo.py` generates the synthetic dataset, trains the demo models and seeds the database on first setup.

## Docker

```bash
docker compose up --build
```

Default Docker stack uses PostgreSQL.

## Main API routes

```text
GET  /api/v1/overview
GET  /api/v1/plants
GET  /api/v1/plants/{plant_id}/history
GET  /api/v1/plants/{plant_id}/forecast
POST /api/v1/predict
POST /api/v1/optimize
GET  /api/v1/scenarios
GET  /api/v1/analytics/patterns
GET  /api/v1/model/metrics
POST /api/v1/data/inspect-csv
```

## Repository layout

```text
app/                  FastAPI application
  api/                REST endpoints
  core/               config + database
  models/             database tables
  services/           prediction, optimization, analytics
ml/                   feature engineering, model training, ONS adapter
data/
  demo/               generated synthetic demo data
  raw/                ignored raw official data
  processed/          ignored processed official data
artifacts/             trained demo model files + metrics
web/                   zero-build production-style demo dashboard
frontend/              optional React/Vite source for the frontend developer
scripts/               bootstrap, ONS download, retraining
notebooks/             analysis starter notebook
reference/             sample competition input/output contracts
tests/                 automated backend/ML/optimizer tests
docs/                  architecture and transition plan
```

## Competition transition

When the official competition files are available:

1. Put raw files in `data/raw/`.
2. Run the ONS adapter/inspection tools.
3. Confirm **what information is known at prediction time** to prevent data leakage.
4. Replace synthetic feature definitions with validated official-data features.
5. Retrain using chronological splits.
6. Revalidate the optimizer assumptions with the thematic specialist.
7. Keep the frontend/API contract stable — the UI does not need to be rebuilt.

Read [`docs/COMPETITION_TRANSITION.md`](docs/COMPETITION_TRANSITION.md) before using official data.

## Data source direction

The official ONS Open Data portal publishes constrained-off datasets for wind and photovoltaic plants and warns that published data can be revised as part of recurring consistency processes. The project therefore keeps raw ingestion separate from model artifacts and records model metadata/versioning.

Useful official datasets to integrate during the competition:

- constrained-off wind plants;
- constrained-off photovoltaic plants;
- hourly generation by plant;
- any additional operational/system variables explicitly allowed/provided by the challenge.

## Scientific integrity

The demo is deliberately strict about three things:

- **No leakage:** post-event fields must never become predictors of a future event.
- **No fake certainty:** risk is a model probability, not a guarantee.
- **No fictional mitigation:** optimization recommendations are scenario outputs under user-supplied technical constraints, not claims that a particular real asset can absorb the energy.

## License

MIT.
