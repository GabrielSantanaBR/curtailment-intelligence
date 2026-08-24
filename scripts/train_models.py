"""Train model artifacts from a CSV compatible with the current feature contract."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import settings  # noqa: E402
from ml.modeling import train_models  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Train Curtailment Intelligence model artifacts.")
    parser.add_argument(
        "--data",
        default=str(settings.demo_data_path),
        help="Input CSV path. Defaults to the synthetic demo dataset.",
    )
    parser.add_argument(
        "--output",
        default=str(settings.model_dir),
        help="Directory where model artifacts and metrics.json are saved.",
    )
    args = parser.parse_args()

    data_path = settings.resolve(args.data)
    output_path = settings.resolve(args.output)
    if not data_path.exists():
        raise SystemExit(f"Dataset not found: {data_path}")

    df = pd.read_csv(data_path)
    metrics = train_models(df, output_path)
    print(f"Model artifacts saved to: {output_path}")
    print(f"Selected classifier: {metrics['selected_classifier']}")
    print(f"Test PR-AUC: {metrics['classifier']['pr_auc']:.4f}")
    print(f"Test F1: {metrics['classifier']['f1']:.4f}")


if __name__ == "__main__":
    main()
