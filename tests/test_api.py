import os
os.environ.setdefault("DATABASE_URL","sqlite:///./test_curtailment.db")
from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)
def test_health(): assert client.get('/health').status_code==200
def test_overview():
    r=client.get('/api/v1/overview'); assert r.status_code==200; assert r.json()["plants"]>=1
def test_plants(): assert client.get('/api/v1/plants').status_code==200
def test_optimization_endpoint():
    p={"plant_code":"DEMO-WIND-01","curtailed_profile_mwh":[30,40],"battery_capacity_mwh":50,"battery_initial_soc_mwh":0,"battery_max_charge_mw":25,"battery_roundtrip_efficiency":.9,"flexible_load_capacity_mw":10,"flexible_load_total_mwh":15,"energy_value_brl_mwh":220,"grid_factor_tco2_mwh":.08}
    r=client.post('/api/v1/optimize',json=p); assert r.status_code==200; assert r.json()["recovered_mwh"]>0
