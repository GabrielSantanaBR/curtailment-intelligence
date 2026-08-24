"""Download monthly public ONS constrained-off CSVs.

This helper is intentionally separate from model training. Always inspect the
schema and the competition data dictionary before using a field as a predictor.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import requests

URLS = {
    "wind": (
        "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/"
        "restricao_coff_eolica_tm/RESTRICAO_COFF_EOLICA_{year}_{month:02d}.csv"
    ),
    "solar": (
        "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/"
        "restricao_coff_fotovoltaica_tm/RESTRICAO_COFF_FOTOVOLTAICA_{year}_{month:02d}.csv"
    ),
}


def download(source: str, year: int, month: int, destination: str | Path) -> Path:
    url = URLS[source].format(year=year, month=month)
    output = Path(destination) / f"ons_{source}_{year}_{month:02d}.csv"
    output.parent.mkdir(parents=True, exist_ok=True)

    response = requests.get(url, timeout=120)
    response.raise_for_status()
    output.write_bytes(response.content)
    print(f"Downloaded {len(response.content) / 1024 / 1024:.1f} MiB -> {output}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", choices=["wind", "solar"])
    parser.add_argument("year", type=int)
    parser.add_argument("month", type=int, choices=range(1, 13))
    parser.add_argument("--dest", default="data/raw")
    args = parser.parse_args()

    download(args.source, args.year, args.month, args.dest)


if __name__ == "__main__":
    main()
