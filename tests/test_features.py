import pandas as pd
from ml.features import model_frame

def test_model_frame_adds_temporal_features():
    df=pd.DataFrame([{"timestamp":"2026-08-20T12:00:00Z","source":"wind","region":"NE","capacity_mw":100,"available_generation_mw":70,"system_load_mw":65000,"renewable_share_pct":45,"network_stress_index":.5,"recent_curtailment_rate_24h":.2,"recent_curtailment_mwh_24h":10,"wind_speed_ms":8,"solar_irradiance_wm2":0,"temperature_c":28}])
    out=model_frame(df)
    assert "hour_sin" in out.columns and abs(out.iloc[0]["capacity_factor"]-.7)<1e-6
