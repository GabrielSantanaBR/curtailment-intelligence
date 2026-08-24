"""Prepare the local synthetic demo in an idempotent way."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import delete

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import settings  # noqa: E402
from app.core.db import Base, SessionLocal, engine  # noqa: E402
from app.models import OptimizationScenario, Plant, PredictionLog  # noqa: E402
from ml.modeling import train_models  # noqa: E402
from ml.synthetic import generate_synthetic_dataset  # noqa: E402


def _model_artifacts_exist(model_dir: Path) -> bool:
    required = [
        model_dir / "curtailment_classifier.joblib",
        model_dir / "curtailed_energy_regressor.joblib",
        model_dir / "metrics.json",
    ]
    return all(path.exists() for path in required)


def prepare_data(data_path: Path, *, force: bool) -> object:
    if force or not data_path.exists():
        print(f"Generating synthetic demo dataset -> {data_path}")
        return generate_synthetic_dataset(data_path, periods=4100, seed=42)

    print(f"Using existing demo dataset -> {data_path}")
    import pandas as pd

    return pd.read_csv(data_path)


def seed_database(df, *, reset_history: bool) -> None:
    Base.metadata.create_all(engine)
    plants = df[["plant_code", "plant_name", "source", "region", "capacity_mw"]].drop_duplicates()

    with SessionLocal() as db:
        if reset_history:
            db.execute(delete(PredictionLog))
            db.execute(delete(OptimizationScenario))

        existing = {plant.code: plant for plant in db.query(Plant).all()}
        for row in plants.itertuples(index=False):
            plant = existing.get(row.plant_code)
            if plant is None:
                db.add(
                    Plant(
                        code=row.plant_code,
                        name=row.plant_name,
                        source=row.source,
                        region=row.region,
                        capacity_mw=float(row.capacity_mw),
                    )
                )
            else:
                plant.name = row.plant_name
                plant.source = row.source
                plant.region = row.region
                plant.capacity_mw = float(row.capacity_mw)
        db.commit()

    print(f"Database ready with {len(plants)} demo plants.")


def main(
    *,
    skip_train: bool = False,
    force_data: bool = False,
    force_models: bool = False,
    reset_history: bool = False,
) -> None:
    data_path = settings.resolve(settings.demo_data_path)
    model_dir = settings.resolve(settings.model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)

    df = prepare_data(data_path, force=force_data)

    if skip_train:
        print("Skipping model training by request.")
    elif force_models or not _model_artifacts_exist(model_dir):
        print(f"Training demo models -> {model_dir}")
        metrics = train_models(df, model_dir)
        print(
            "Selected model:",
            metrics["selected_classifier"],
            "| PR-AUC:",
            round(metrics["classifier"]["pr_auc"], 4),
            "| F1:",
            round(metrics["classifier"]["f1"], 4),
        )
    else:
        print(f"Using existing model artifacts -> {model_dir}")

    seed_database(df, reset_history=reset_history)
    print(f"Demo ready: {len(df):,} rows.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare the local synthetic demo.")
    parser.add_argument("--skip-train", action="store_true", help="Do not train model artifacts.")
    parser.add_argument("--force-data", action="store_true", help="Regenerate synthetic data.")
    parser.add_argument("--force-models", action="store_true", help="Retrain demo models.")
    parser.add_argument(
        "--reset-history",
        action="store_true",
        help="Delete saved prediction and optimization history.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Regenerate data, retrain models and clear demo history.",
    )
    args = parser.parse_args()

    main(
        skip_train=args.skip_train,
        force_data=args.force_data or args.reset,
        force_models=args.force_models or args.reset,
        reset_history=args.reset_history or args.reset,
    )
