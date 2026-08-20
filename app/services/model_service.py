import json
from functools import lru_cache
from pathlib import Path
from datetime import datetime, timezone
import joblib
import numpy as np
import pandas as pd
from app.core.config import settings
from ml.features import model_frame
from app.services.data_service import latest_row


LABELS={
    "network_stress_index":"Estresse da rede",
    "renewable_share_pct":"Participação renovável",
    "recent_curtailment_rate_24h":"Frequência recente de cortes",
    "recent_curtailment_mwh_24h":"Energia restringida nas últimas 24h",
    "available_generation_mw":"Geração disponível",
    "capacity_factor":"Fator de capacidade",
    "system_load_mw":"Carga do sistema",
    "wind_speed_ms":"Velocidade do vento",
    "solar_irradiance_wm2":"Irradiância solar",
    "temperature_c":"Temperatura",
}


@lru_cache(maxsize=1)
def artifacts():
    path=settings.resolve(settings.model_dir)
    classifier_path=path/'curtailment_classifier.joblib'
    regressor_path=path/'curtailed_energy_regressor.joblib'
    metrics_path=path/'metrics.json'
    if not classifier_path.exists():
        from ml.synthetic import generate_synthetic_dataset
        from ml.modeling import train_models
        data=generate_synthetic_dataset(settings.resolve(settings.demo_data_path),periods=3000)
        train_models(data,path)
    return joblib.load(classifier_path),joblib.load(regressor_path),json.loads(metrics_path.read_text(encoding='utf-8'))


def risk_level(p: float) -> str:
    if p>=0.80:return "critical"
    if p>=0.60:return "high"
    if p>=0.35:return "moderate"
    return "low"


def _predict_probability(classifier,row:dict)->float:
    return float(classifier.predict_proba(model_frame(pd.DataFrame([row])))[:,1][0])


def explain_local(classifier,row:dict,base_p:float,top_k:int=6):
    # Model-agnostic one-at-a-time perturbation. Values are not causal effects.
    perturb={
        "network_stress_index":0.15,
        "renewable_share_pct":12.0,
        "recent_curtailment_rate_24h":0.15,
        "recent_curtailment_mwh_24h":20.0,
        "available_generation_mw":max(10.0,float(row.get("capacity_mw",100))*0.15),
        "system_load_mw":5000.0,
        "wind_speed_ms":2.0,
        "solar_irradiance_wm2":150.0,
        "temperature_c":4.0,
    }
    items=[]
    for feature,delta in perturb.items():
        if feature not in row: continue
        changed=dict(row)
        value=float(changed[feature])
        changed[feature]=max(0,value-delta) if feature not in {"temperature_c"} else value-delta
        try: alt=_predict_probability(classifier,changed)
        except Exception: continue
        effect=base_p-alt
        items.append({
            "feature":feature,"label":LABELS.get(feature,feature),"effect":round(float(effect),4),
            "direction":"increases_risk" if effect>0 else "decreases_risk",
            "current_value":round(value,3)
        })
    return sorted(items,key=lambda x:abs(x["effect"]),reverse=True)[:top_k]


def predict(plant_code:str, features:dict|None=None):
    classifier,regressor,metrics=artifacts()
    row=features or latest_row(plant_code)
    row=dict(row)
    if "timestamp" not in row: row["timestamp"]=datetime.now(timezone.utc).isoformat()
    p=_predict_probability(classifier,row)
    magnitude=max(0.0,float(regressor.predict(model_frame(pd.DataFrame([row])))[0]))
    # Expected curtailed energy: event magnitude conditional on event * event probability.
    expected=magnitude*p
    explanation=explain_local(classifier,row,p)
    return {
        "plant_code":plant_code,
        "timestamp":pd.to_datetime(row["timestamp"],utc=True).to_pydatetime(),
        "risk_probability":round(p,4),
        "risk_level":risk_level(p),
        "decision_threshold":round(float(metrics["decision_threshold"]),4),
        "predicted_curtailed_mwh":round(expected,3),
        "explanation":explanation,
        "model_version":metrics["model_version"],
        "data_mode":"synthetic_demo" if features is None else "user_supplied_features",
    }
