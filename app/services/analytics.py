"""Aggregated analytics used by the dashboard."""

from app.services.data_service import load_demo_data


def overview() -> dict:
    df = load_demo_data()
    curtailed = df[df["curtailment_event"] == 1]
    total = float(curtailed["curtailed_energy_mwh"].sum())
    top = (
        curtailed.groupby(["plant_code", "plant_name"], as_index=False)
        .agg(
            events=("curtailment_event", "sum"),
            curtailed_mwh=("curtailed_energy_mwh", "sum"),
        )
        .sort_values("curtailed_mwh", ascending=False)
        .head(5)
    )

    return {
        "rows": len(df),
        "plants": int(df["plant_code"].nunique()),
        "event_rate_pct": round(100 * float(df["curtailment_event"].mean()), 2),
        "curtailed_mwh": round(total, 2),
        "top_plants": top.round(2).to_dict(orient="records"),
        "data_mode": "synthetic_demo",
    }


def patterns() -> dict:
    df = load_demo_data().copy()
    df["hour"] = df["timestamp"].dt.hour

    hourly = (
        df.groupby("hour")
        .agg(
            event_rate=("curtailment_event", "mean"),
            curtailed_mwh=("curtailed_energy_mwh", "sum"),
        )
        .reset_index()
    )
    reasons = (
        df[df["curtailment_event"] == 1]
        .groupby("restriction_reason")
        .agg(events=("curtailment_event", "sum"), mwh=("curtailed_energy_mwh", "sum"))
        .reset_index()
    )
    regions = (
        df.groupby("region")
        .agg(event_rate=("curtailment_event", "mean"), mwh=("curtailed_energy_mwh", "sum"))
        .reset_index()
    )

    return {
        "hourly": [
            {
                "hour": int(row.hour),
                "event_rate_pct": round(100 * float(row.event_rate), 2),
                "curtailed_mwh": round(float(row.curtailed_mwh), 2),
            }
            for row in hourly.itertuples()
        ],
        "reasons": reasons.round(2).to_dict(orient="records"),
        "regions": [
            {
                "region": row.region,
                "event_rate_pct": round(100 * float(row.event_rate), 2),
                "mwh": round(float(row.mwh), 2),
            }
            for row in regions.itertuples()
        ],
    }
