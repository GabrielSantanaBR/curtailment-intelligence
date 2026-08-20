from pathlib import Path
import numpy as np
import pandas as pd


PLANTS = [
    ("DEMO-WIND-01", "Parque Eólico Serra Azul", "wind", "NE", 180.0),
    ("DEMO-WIND-02", "Parque Eólico Ventos do Norte", "wind", "NE", 240.0),
    ("DEMO-WIND-03", "Parque Eólico Pampa", "wind", "S", 150.0),
    ("DEMO-SOLAR-01", "Complexo Solar Horizonte", "solar", "NE", 210.0),
    ("DEMO-SOLAR-02", "Complexo Solar Sertão", "solar", "NE", 160.0),
    ("DEMO-SOLAR-03", "Complexo Solar Cerrado", "solar", "SE", 130.0),
]


def generate_synthetic_dataset(path: str | Path, periods: int = 4100, seed: int = 42) -> pd.DataFrame:
    """Generate hourly rows for every demo plant and derive a genuine future 6h target.

    `periods` means hourly timestamps, not final row count. With six plants, 4,100
    periods produce ~24.6k rows before the last six targetless hours are removed.
    """
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2026-03-01T00:00:00Z")
    timestamps = pd.date_range(start, periods=periods, freq="h")
    records = []
    recent = {p[0]: [] for p in PLANTS}

    for ts in timestamps:
        hour = ts.hour
        month = ts.month
        # System-level variables shared across plants for the same hour.
        system_wave = max(0, np.sin(2 * np.pi * (hour - 10) / 24))
        base_renewable = 30 + 15 * np.sin(2 * np.pi * (hour - 11) / 24)
        load = 67000 + 7500 * np.sin(2 * np.pi * (hour - 15) / 24) + 2500 * np.sin(2 * np.pi * (month - 1) / 12) + rng.normal(0, 1500)
        common_stress = np.clip(0.13 + 0.24 * system_wave + rng.normal(0, 0.04), 0, 1)

        for code, name, source, region, capacity in PLANTS:
            if source == "wind":
                seasonal = 8.2 + 2.2 * np.sin(2 * np.pi * (month - 6) / 12)
                wind = max(0.2, rng.normal(seasonal, 2.0))
                irradiance = max(0.0, rng.normal(50 if 7 <= hour <= 17 else 0, 30))
                raw_cf = min(1.05, max(0.02, (wind / 12.5) ** 2))
            else:
                daylight = max(0, np.sin(np.pi * (hour - 6) / 12)) if 6 <= hour <= 18 else 0
                irradiance = max(0, 940 * daylight + rng.normal(0, 60))
                wind = max(0.2, rng.normal(4.2, 1.1))
                raw_cf = min(1.03, max(0, irradiance / 1000)) * 0.93

            temperature = 25 + 6 * np.sin(2 * np.pi * (hour - 14) / 24) + 2 * np.sin(2 * np.pi * (month - 1) / 12) + rng.normal(0, 1.6)
            renewable_share = np.clip(base_renewable + (8 if region == "NE" else 0) + rng.normal(0, 4), 5, 78)
            stress = np.clip(common_stress + 0.40 * (renewable_share / 100) + (0.05 if region == "NE" else 0) + rng.normal(0, 0.05), 0, 1)

            history = recent[code][-24:]
            recent_rate = float(np.mean([e[0] for e in history])) if history else 0.0
            recent_mwh = float(np.sum([e[1] for e in history])) if history else 0.0
            available = capacity * raw_cf
            potential_ratio = available / max(capacity, 1)

            # Rare instantaneous events; prediction target below is "any event in next 6h".
            logit = (
                -7.0
                + 4.8 * stress
                + 2.4 * (renewable_share / 100)
                + 1.35 * potential_ratio
                + 0.7 * recent_rate
                + 0.22 * (region == "NE")
                + rng.normal(0, 0.45)
            )
            prob = 1 / (1 + np.exp(-logit))
            event = int(rng.random() < prob)
            if event:
                severity = np.clip(0.07 + 0.52 * stress + 0.20 * (renewable_share / 100) + rng.normal(0, 0.07), 0.04, 0.80)
                curtailed = available * severity
                reason = rng.choice(
                    ["transmission_constraint", "energy_balance", "operational_security"],
                    p=[0.50, 0.32, 0.18],
                )
            else:
                curtailed = 0.0
                reason = "none"
            generation = max(0, available - curtailed)
            recent[code].append((event, curtailed))

            records.append(
                {
                    "timestamp": ts.isoformat(),
                    "plant_code": code,
                    "plant_name": name,
                    "source": source,
                    "region": region,
                    "capacity_mw": round(capacity, 3),
                    "available_generation_mw": round(available, 3),
                    "actual_generation_mw": round(generation, 3),
                    "system_load_mw": round(float(load), 3),
                    "renewable_share_pct": round(float(renewable_share), 3),
                    "network_stress_index": round(float(stress), 4),
                    "recent_curtailment_rate_24h": round(recent_rate, 4),
                    "recent_curtailment_mwh_24h": round(recent_mwh, 3),
                    "wind_speed_ms": round(float(wind), 3),
                    "solar_irradiance_wm2": round(float(irradiance), 3),
                    "temperature_c": round(float(temperature), 3),
                    "curtailment_event": event,
                    "curtailed_energy_mwh": round(float(curtailed), 3),
                    "restriction_reason": reason,
                    "synthetic_instant_risk_truth": round(float(prob), 4),
                }
            )

    df = pd.DataFrame(records).sort_values(["plant_code", "timestamp"]).reset_index(drop=True)
    # True forward-looking labels. At timestamp T, label only looks at T+1 ... T+6.
    groups = []
    horizon = 6
    for _, g in df.groupby("plant_code", sort=False):
        g = g.copy().reset_index(drop=True)
        future_events = sum(g["curtailment_event"].shift(-step).fillna(0) for step in range(1, horizon + 1))
        future_energy = sum(g["curtailed_energy_mwh"].shift(-step).fillna(0) for step in range(1, horizon + 1))
        g["curtailment_next_6h"] = (future_events > 0).astype(int)
        g["curtailed_energy_next_6h_mwh"] = future_energy.astype(float)
        # Last horizon rows do not have a complete forecast window.
        g = g.iloc[:-horizon].copy()
        groups.append(g)
    df = pd.concat(groups, ignore_index=True).sort_values("timestamp").reset_index(drop=True)

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return df
