"""Audit an ONS/competition CSV before feature engineering."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.ons_adapter import inspect_dataframe, normalize_name, read_csv_flexible  # noqa: E402

LEAKAGE_HINTS = (
    "restr",
    "curtail",
    "corte",
    "energia_restr",
    "motivo",
    "razao",
    "causa",
    "geracao_realizada",
    "geracao_verificada",
)


def audit(path: Path) -> dict:
    with path.open("rb") as handle:
        df = read_csv_flexible(handle)

    mapping, warnings = inspect_dataframe(df)
    normalized = {str(column): normalize_name(column) for column in df.columns}
    leakage = [
        original
        for original, normalized_name in normalized.items()
        if any(hint in normalized_name for hint in LEAKAGE_HINTS)
    ]

    report = {
        "file": str(path),
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(map(str, df.columns)),
        "detected_mapping": mapping,
        "warnings": warnings,
        "potential_post_event_or_leakage_fields": leakage,
        "missing_pct": {
            str(column): round(float(df[column].isna().mean() * 100), 3)
            for column in df.columns
        },
        "duplicate_rows": int(df.duplicated().sum()),
    }

    timestamp_column = mapping.get("timestamp")
    if timestamp_column:
        parsed = pd.to_datetime(df[timestamp_column], errors="coerce", utc=True)
        report["timestamp_parse_success_pct"] = round(float(parsed.notna().mean() * 100), 3)
        if parsed.notna().any():
            report["time_range"] = [parsed.min().isoformat(), parsed.max().isoformat()]

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", help="CSV to audit.")
    parser.add_argument("--out", default="artifacts/data_audit.json")
    args = parser.parse_args()

    source = Path(args.csv)
    if not source.exists():
        raise SystemExit(f"File not found: {source}")

    result = audit(source)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
