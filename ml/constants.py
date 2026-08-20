NUMERIC_FEATURES = [
    "hour_sin",
    "hour_cos",
    "dow_sin",
    "dow_cos",
    "month_sin",
    "month_cos",
    "capacity_mw",
    "available_generation_mw",
    "capacity_factor",
    "system_load_mw",
    "renewable_share_pct",
    "network_stress_index",
    "recent_curtailment_rate_24h",
    "recent_curtailment_mwh_24h",
    "wind_speed_ms",
    "solar_irradiance_wm2",
    "temperature_c",
]
CATEGORICAL_FEATURES = ["source", "region"]
MODEL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TARGET_CLASS = "curtailment_next_6h"
TARGET_REGRESSION = "curtailed_energy_next_6h_mwh"
FORECAST_HORIZON_HOURS = 6
