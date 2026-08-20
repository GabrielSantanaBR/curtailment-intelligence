from pathlib import Path
import sys, argparse, json
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import pandas as pd
from ml.ons_adapter import read_csv_flexible, inspect_dataframe, normalize_name

LEAKAGE_HINTS=("restr", "curtail", "corte", "energia_restr", "motivo", "razao", "causa", "geracao_realizada", "geracao_verificada")

def audit(path:Path):
    with path.open('rb') as f: df=read_csv_flexible(f)
    mapping,warnings=inspect_dataframe(df)
    normalized={str(c):normalize_name(c) for c in df.columns}
    leakage=[orig for orig,norm in normalized.items() if any(h in norm for h in LEAKAGE_HINTS)]
    report={
        "file":str(path),"rows":len(df),"columns":len(df.columns),"column_names":list(map(str,df.columns)),
        "detected_mapping":mapping,"warnings":warnings,
        "potential_post_event_or_leakage_fields":leakage,
        "missing_pct":{str(c):round(float(df[c].isna().mean()*100),3) for c in df.columns},
        "duplicate_rows":int(df.duplicated().sum()),
    }
    ts=mapping.get('timestamp')
    if ts:
        parsed=pd.to_datetime(df[ts],errors='coerce',utc=True)
        report['timestamp_parse_success_pct']=round(float(parsed.notna().mean()*100),3)
        if parsed.notna().any(): report['time_range']=[parsed.min().isoformat(),parsed.max().isoformat()]
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description='Audit an ONS/competition CSV before feature engineering.')
    p.add_argument('csv'); p.add_argument('--out',default='artifacts/data_audit.json'); a=p.parse_args()
    result=audit(Path(a.csv)); out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
