import os
from pathlib import Path

import pytest

TEST_DB = Path("test_curtailment.db")
os.environ.setdefault("DATABASE_URL", f"sqlite:///./{TEST_DB}")

if TEST_DB.exists():
    TEST_DB.unlink()

from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    """Run FastAPI lifespan so database tables exist during API tests."""
    with TestClient(app) as test_client:
        yield test_client

    if TEST_DB.exists():
        TEST_DB.unlink()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["version"]


def test_overview(client):
    response = client.get("/api/v1/overview")
    assert response.status_code == 200
    assert response.json()["plants"] >= 1


def test_plants(client):
    response = client.get("/api/v1/plants")
    assert response.status_code == 200


def test_unknown_plant_history_returns_404(client):
    response = client.get("/api/v1/plants/DOES-NOT-EXIST/history")
    assert response.status_code == 404


def test_optimization_endpoint(client):
    payload = {
        "plant_code": "DEMO-WIND-01",
        "curtailed_profile_mwh": [30, 40],
        "battery_capacity_mwh": 50,
        "battery_initial_soc_mwh": 0,
        "battery_max_charge_mw": 25,
        "battery_roundtrip_efficiency": 0.9,
        "flexible_load_capacity_mw": 10,
        "flexible_load_total_mwh": 15,
        "energy_value_brl_mwh": 220,
        "grid_factor_tco2_mwh": 0.08,
    }
    response = client.post("/api/v1/optimize", json=payload)
    assert response.status_code == 200
    assert response.json()["recovered_mwh"] > 0


def test_invalid_optimization_payload_returns_422(client):
    response = client.post(
        "/api/v1/optimize",
        json={"plant_code": "DEMO", "curtailed_profile_mwh": []},
    )
    assert response.status_code == 422


def test_csv_inspection_endpoint(client):
    csv = "din_instante;id_ons;nom_usina\n2026-01-01T00:00:00Z;X;Usina X\n"
    response = client.post(
        "/api/v1/data/inspect-csv",
        files={"file": ("sample.csv", csv, "text/csv")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["rows"] == 1
    assert payload["detected_mapping"]["timestamp"] == "din_instante"
