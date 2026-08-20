from functools import lru_cache
import pandas as pd
from app.core.config import settings


@lru_cache(maxsize=1)
def load_demo_data() -> pd.DataFrame:
    path=settings.resolve(settings.demo_data_path)
    if not path.exists():
        from ml.synthetic import generate_synthetic_dataset
        generate_synthetic_dataset(path,periods=2500)
    df=pd.read_csv(path)
    df["timestamp"]=pd.to_datetime(df["timestamp"],utc=True)
    return df


def latest_row(plant_code: str) -> dict:
    df=load_demo_data()
    rows=df[df["plant_code"]==plant_code]
    if rows.empty: raise KeyError(plant_code)
    return rows.iloc[-1].to_dict()


def plant_history(plant_code: str, limit: int=168) -> list[dict]:
    df=load_demo_data()
    rows=df[df["plant_code"]==plant_code].sort_values("timestamp").tail(limit)
    return [{
        "timestamp":r.timestamp.isoformat(),
        "curtailment_event":int(r.curtailment_event),
        "curtailed_energy_mwh":float(r.curtailed_energy_mwh),
        "actual_generation_mw":float(r.actual_generation_mw),
        "available_generation_mw":float(r.available_generation_mw),
        "network_stress_index":float(r.network_stress_index),
        "renewable_share_pct":float(r.renewable_share_pct),
    } for r in rows.itertuples()]
