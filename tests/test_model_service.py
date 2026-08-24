from app.services.model_service import risk_level


def test_risk_level_boundaries():
    assert risk_level(0.0) == "low"
    assert risk_level(0.35) == "moderate"
    assert risk_level(0.60) == "high"
    assert risk_level(0.80) == "critical"
