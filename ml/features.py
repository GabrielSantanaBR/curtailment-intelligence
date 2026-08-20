import numpy as np
import pandas as pd
from ml.constants import MODEL_FEATURES


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True, errors="coerce")
    if out["timestamp"].isna().any():
        raise ValueError("timestamp contains invalid values")

    hour = out["timestamp"].dt.hour + out["timestamp"].dt.minute / 60
    dow = out["timestamp"].dt.dayofweek
    month = out["timestamp"].dt.month
    out["hour_sin"] = np.sin(2 * np.pi * hour / 24)
    out["hour_cos"] = np.cos(2 * np.pi * hour / 24)
    out["dow_sin"] = np.sin(2 * np.pi * dow / 7)
    out["dow_cos"] = np.cos(2 * np.pi * dow / 7)
    out["month_sin"] = np.sin(2 * np.pi * month / 12)
    out["month_cos"] = np.cos(2 * np.pi * month / 12)
    out["capacity_factor"] = (
        out["available_generation_mw"] / out["capacity_mw"].clip(lower=1e-6)
    ).clip(0, 1.4)
    return out


def model_frame(df: pd.DataFrame) -> pd.DataFrame:
    engineered = engineer_features(df)
    missing = [c for c in MODEL_FEATURES if c not in engineered.columns]
    if missing:
        raise ValueError(f"Missing model features: {missing}")
    return engineered[MODEL_FEATURES]
