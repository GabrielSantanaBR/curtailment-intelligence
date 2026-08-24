"""Helpers for adapting public ONS/competition CSV schemas.

The adapter intentionally uses conservative alias matching. A detected field is a
starting point for inspection, not proof that the variable is valid for modeling.
"""

from __future__ import annotations

import re
import unicodedata

import pandas as pd


def normalize_name(name: str) -> str:
    value = (
        unicodedata.normalize("NFKD", str(name))
        .encode("ascii", "ignore")
        .decode()
        .lower()
    )
    return re.sub(r"[^a-z0-9]+", "_", value).strip("_")


ALIASES = {
    "timestamp": [
        "din_instante",
        "data_hora",
        "datahora",
        "timestamp",
        "instante",
        "din_referencia",
    ],
    "plant_code": [
        "id_ons",
        "cod_ons",
        "codigo_usina",
        "ceg",
        "id_usina",
        "nom_conjunto",
    ],
    "plant_name": ["nom_usina", "nome_usina", "usina", "nom_conjunto"],
    "region": ["nom_subsistema", "subsistema", "regiao"],
    "available_generation_mw": [
        "val_geracao_disponivel",
        "geracao_disponivel",
        "val_geracaoprogramada",
        "geracao_programada",
    ],
    "actual_generation_mw": [
        "val_geracao",
        "geracao_verificada",
        "geracao_realizada",
        "val_geracaoverificada",
    ],
    "curtailed_energy_mwh": [
        "val_energia_restrita",
        "energia_restrita",
        "energia_cortada",
        "curtailment_mwh",
    ],
    "restriction_reason": [
        "cod_razaorestricao",
        "razao_restricao",
        "motivo_restricao",
        "tip_restricao",
    ],
}


def detect_mapping(columns) -> dict[str, str]:
    normalized = {normalize_name(column): column for column in columns}
    mapping: dict[str, str] = {}

    for target, aliases in ALIASES.items():
        for alias in [target, *aliases]:
            if alias in normalized:
                mapping[target] = normalized[alias]
                break

    return mapping


def inspect_dataframe(df: pd.DataFrame) -> tuple[dict[str, str], list[str]]:
    mapping = detect_mapping(df.columns)
    warnings: list[str] = []

    for field in ["timestamp", "plant_code"]:
        if field not in mapping:
            warnings.append(
                f"Could not detect required field '{field}'. "
                "Confirm the ONS dictionary/competition schema."
            )

    if "curtailed_energy_mwh" not in mapping and "actual_generation_mw" not in mapping:
        warnings.append("No obvious curtailment-energy or actual-generation field was detected.")

    return mapping, warnings


def read_csv_flexible(path_or_buffer) -> pd.DataFrame:
    errors: list[str] = []

    for separator in [";", ",", "\t"]:
        try:
            dataframe = pd.read_csv(path_or_buffer, sep=separator, encoding="utf-8")
            if len(dataframe.columns) > 1:
                return dataframe
        except (UnicodeDecodeError, pd.errors.ParserError) as exc:
            errors.append(str(exc))

        if hasattr(path_or_buffer, "seek"):
            path_or_buffer.seek(0)

    detail = " | ".join(errors[-2:])
    raise ValueError(f"Could not parse CSV. {detail}".strip())


def normalize_ons_frame(df: pd.DataFrame) -> pd.DataFrame:
    mapping, _warnings = inspect_dataframe(df)
    output = df.copy()

    for target, source in mapping.items():
        if target not in output.columns:
            output[target] = output[source]

    return output
