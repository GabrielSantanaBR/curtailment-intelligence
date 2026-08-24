"""Data access helpers for the synthetic demo dataset."""

from functools import lru_cache

import pandas as pd

from app.core.config import settings


@lru_cache(maxsize=1)
def load_demo_data() -> pd.DataFrame:
    path = settings.resolve(settings.demo_data_path)
    if not path.exists():
        from ml.synthetic import generate_synthetic_dataset

        generate_synthetic_dataset(path, periods=2500)

    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df


def clear_demo_data_cache() -> None:
    """Clear the in-process DataFrame cache after replacing the demo dataset."""
    load_demo_data.cache_clear()


def latest_row(plant_code: str) -> dict:
    df = load_demo_data()
    rows = df[df["plant_code"] == plant_code]
    if rows.empty:
        raise KeyError(plant_code)
    return rows.iloc[-1].to_dict()


def plant_history(plant_code: str, limit: int = 168) -> list[dict]:
    df = load_demo_data()
    rows = df[df["plant_code"] == plant_code].sort_values("timestamp").tail(limit)
    if rows.empty:
        raise KeyError(plant_code)

    return [
        {
            "timestamp": row.timestamp.isoformat(),
            "curtailment_event": int(row.curtailment_event),
            "curtailed_energy_mwh": float(row.curtailed_energy_mwh),
            "actual_generation_mw": float(row.actual_generation_mw),
            "available_generation_mw": float(row.available_generation_mw),
            "network_stress_index": float(row.network_stress_index),
            "renewable_share_pct": float(row.renewable_share_pct),
        }
        for row in rows.itertuples()
    ]
