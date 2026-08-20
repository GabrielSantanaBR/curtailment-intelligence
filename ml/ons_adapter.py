import re
import unicodedata
from pathlib import Path
import pandas as pd


def normalize_name(name: str) -> str:
    value=unicodedata.normalize("NFKD",str(name)).encode("ascii","ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+","_",value).strip("_")


ALIASES = {
    "timestamp": ["din_instante","data_hora","datahora","timestamp","instante","din_referencia"],
    "plant_code": ["id_ons","cod_ons","codigo_usina","ceg","id_usina","nom_conjunto"],
    "plant_name": ["nom_usina","nome_usina","usina","nom_conjunto"],
    "region": ["nom_subsistema","subsistema","regiao"],
    "available_generation_mw": ["val_geracao_disponivel","geracao_disponivel","val_geracaoprogramada","geracao_programada"],
    "actual_generation_mw": ["val_geracao","geracao_verificada","geracao_realizada","val_geracaoverificada"],
    "curtailed_energy_mwh": ["val_energia_restrita","energia_restrita","energia_cortada","curtailment_mwh"],
    "restriction_reason": ["cod_razaorestricao","razao_restricao","motivo_restricao","tip_restricao"],
}


def detect_mapping(columns) -> dict[str,str]:
    normalized={normalize_name(c):c for c in columns}
    mapping={}
    for target,aliases in ALIASES.items():
        for alias in [target, *aliases]:
            if alias in normalized:
                mapping[target]=normalized[alias]; break
    return mapping


def inspect_dataframe(df: pd.DataFrame):
    mapping=detect_mapping(df.columns)
    warnings=[]
    required=["timestamp","plant_code"]
    for field in required:
        if field not in mapping:
            warnings.append(f"Could not detect required field '{field}'. Confirm ONS dictionary/competition schema.")
    if "curtailed_energy_mwh" not in mapping and "actual_generation_mw" not in mapping:
        warnings.append("No obvious curtailment-energy or actual-generation field was detected.")
    return mapping,warnings


def read_csv_flexible(path_or_buffer):
    errors=[]
    for sep in [";",",","\t"]:
        try:
            df=pd.read_csv(path_or_buffer,sep=sep,encoding="utf-8")
            if len(df.columns)>1: return df
        except Exception as exc: errors.append(str(exc))
        try:
            if hasattr(path_or_buffer,"seek"): path_or_buffer.seek(0)
        except Exception: pass
    raise ValueError("Could not parse CSV. " + " | ".join(errors[-2:]))


def normalize_ons_frame(df: pd.DataFrame) -> pd.DataFrame:
    mapping,warnings=inspect_dataframe(df)
    out=df.copy()
    for target,source in mapping.items():
        if target not in out.columns: out[target]=out[source]
    return out
