import pytest

from app.services.optimizer import optimize_dispatch


def payload(**kwargs):
    base = {
        "plant_code": "X",
        "curtailed_profile_mwh": [50, 50],
        "battery_capacity_mwh": 60,
        "battery_initial_soc_mwh": 0,
        "battery_max_charge_mw": 30,
        "battery_roundtrip_efficiency": 1.0,
        "flexible_load_capacity_mw": 10,
        "flexible_load_total_mwh": 20,
        "energy_value_brl_mwh": 200,
        "grid_factor_tco2_mwh": 0.1,
    }
    base.update(kwargs)
    return base


def test_optimizer_respects_energy_balance():
    result = optimize_dispatch(payload())
    assert result["recovered_mwh"] + result["lost_mwh"] == result["total_available_mwh"]
    assert result["recovered_mwh"] <= 80.0001


def test_optimizer_no_resources_recovers_zero():
    result = optimize_dispatch(
        payload(
            battery_capacity_mwh=0,
            battery_max_charge_mw=0,
            flexible_load_capacity_mw=0,
            flexible_load_total_mwh=0,
        )
    )
    assert result["recovered_mwh"] == 0
    assert result["strategy_summary"] == "no mitigation resource"


def test_optimizer_rejects_negative_curtailment_profile():
    with pytest.raises(ValueError):
        optimize_dispatch(payload(curtailed_profile_mwh=[10, -1]))
