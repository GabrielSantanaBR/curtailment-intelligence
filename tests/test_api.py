import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_curtailment.db")

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["version"]


def test_overview():
    response = client.get("/api/v1/overview")
    assert response.status_code == 200
    assert response.json()["plants"] >= 1


def test_plants():
    response = client.get("/api/v1/plants")
    assert response.status_code == 200


def test_unknown_plant_history_returns_404():
    response = client.get("/api/v1/plants/DOES-NOT-EXIST/history")
    assert response.status_code == 404


def test_optimization_endpoint():
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


def test_invalid_optimization_payload_returns_422():
    response = client.post(
        "/api/v1/optimize",
        json={"plant_code": "DEMO", "curtailed_profile_mwh": []},
    )
    assert response.status_code == 422


def test_csv_inspection_endpoint():
    csv = "din_instante;id_ons;nom_usina\n2026-01-01T00:00:00Z;X;Usina X\n"
    response = client.post(
        "/api/v1/data/inspect-csv",
        files={"file": ("sample.csv", csv, "text/csv")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["rows"] == 1
    assert payload["detected_mapping"]["timestamp"] == "din_instante"
