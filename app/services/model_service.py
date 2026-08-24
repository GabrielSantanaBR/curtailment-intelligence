"""Load trained artifacts and expose application-level prediction helpers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from functools import lru_cache

import joblib
import pandas as pd

from app.core.config import settings
from app.services.data_service import latest_row
from ml.features import model_frame

LABELS = {
    "network_stress_index": "Estresse da rede",
    "renewable_share_pct": "Participação renovável",
    "recent_curtailment_rate_24h": "Frequência recente de cortes",
    "recent_curtailment_mwh_24h": "Energia restringida nas últimas 24h",
    "available_generation_mw": "Geração disponível",
    "capacity_factor": "Fator de capacidade",
    "system_load_mw": "Carga do sistema",
    "wind_speed_ms": "Velocidade do vento",
    "solar_irradiance_wm2": "Irradiância solar",
    "temperature_c": "Temperatura",
}


@lru_cache(maxsize=1)
def artifacts():
    """Load model artifacts, creating demo artifacts lazily when absent."""
    path = settings.resolve(settings.model_dir)
    classifier_path = path / "curtailment_classifier.joblib"
    regressor_path = path / "curtailed_energy_regressor.joblib"
    metrics_path = path / "metrics.json"

    if not classifier_path.exists() or not regressor_path.exists() or not metrics_path.exists():
        from ml.modeling import train_models
        from ml.synthetic import generate_synthetic_dataset

        data = generate_synthetic_dataset(
            settings.resolve(settings.demo_data_path),
            periods=3000,
        )
        train_models(data, path)

    return (
        joblib.load(classifier_path),
        joblib.load(regressor_path),
        json.loads(metrics_path.read_text(encoding="utf-8")),
    )


def clear_artifact_cache() -> None:
    artifacts.cache_clear()


def risk_level(probability: float) -> str:
    if probability >= 0.80:
        return "critical"
    if probability >= 0.60:
        return "high"
    if probability >= 0.35:
        return "moderate"
    return "low"


def _predict_probability(classifier, row: dict) -> float:
    frame = model_frame(pd.DataFrame([row]))
    return float(classifier.predict_proba(frame)[:, 1][0])


def explain_local(
    classifier,
    row: dict,
    base_probability: float,
    top_k: int = 6,
) -> list[dict]:
    """Model-agnostic local perturbation explanation.

    Effects describe changes in the model output when one value is perturbed.
    They are not causal effects.
    """
    perturbations = {
        "network_stress_index": 0.15,
        "renewable_share_pct": 12.0,
        "recent_curtailment_rate_24h": 0.15,
        "recent_curtailment_mwh_24h": 20.0,
        "available_generation_mw": max(10.0, float(row.get("capacity_mw", 100)) * 0.15),
        "system_load_mw": 5000.0,
        "wind_speed_ms": 2.0,
        "solar_irradiance_wm2": 150.0,
        "temperature_c": 4.0,
    }

    items: list[dict] = []
    for feature, delta in perturbations.items():
        if feature not in row:
            continue

        changed = dict(row)
        value = float(changed[feature])
        if feature == "temperature_c":
            changed[feature] = value - delta
        else:
            changed[feature] = max(0, value - delta)

        try:
            alternative_probability = _predict_probability(classifier, changed)
        except (TypeError, ValueError, KeyError):
            continue

        effect = base_probability - alternative_probability
        items.append(
            {
                "feature": feature,
                "label": LABELS.get(feature, feature),
                "effect": round(float(effect), 4),
                "direction": "increases_risk" if effect > 0 else "decreases_risk",
                "current_value": round(value, 3),
            }
        )

    return sorted(items, key=lambda item: abs(item["effect"]), reverse=True)[:top_k]


def predict(plant_code: str, features: dict | None = None) -> dict:
    classifier, regressor, metrics = artifacts()
    row = dict(features or latest_row(plant_code))
    row.setdefault("timestamp", datetime.now(timezone.utc).isoformat())

    probability = _predict_probability(classifier, row)
    magnitude = max(
        0.0,
        float(regressor.predict(model_frame(pd.DataFrame([row])))[0]),
    )

    # Expected curtailed energy = event probability × conditional event magnitude.
    expected_energy = magnitude * probability

    return {
        "plant_code": plant_code,
        "timestamp": pd.to_datetime(row["timestamp"], utc=True).to_pydatetime(),
        "risk_probability": round(probability, 4),
        "risk_level": risk_level(probability),
        "decision_threshold": round(float(metrics["decision_threshold"]), 4),
        "predicted_curtailed_mwh": round(expected_energy, 3),
        "explanation": explain_local(classifier, row, probability),
        "model_version": metrics["model_version"],
        "data_mode": "synthetic_demo" if features is None else "user_supplied_features",
    }
