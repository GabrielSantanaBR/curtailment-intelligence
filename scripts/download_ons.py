from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
"""Download monthly public ONS constrained-off CSVs.

This helper is intentionally separate from model training. Always inspect the downloaded schema
and the competition-provided data dictionary before using any field as a predictor.
"""
import argparse
from pathlib import Path
import requests

URLS={
    "wind":"https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/restricao_coff_eolica_tm/RESTRICAO_COFF_EOLICA_{year}_{month:02d}.csv",
    "solar":"https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/restricao_coff_fotovoltaica_tm/RESTRICAO_COFF_FOTOVOLTAICA_{year}_{month:02d}.csv",
}

def download(source,year,month,dest):
    url=URLS[source].format(year=year,month=month)
    out=Path(dest)/f"ons_{source}_{year}_{month:02d}.csv"; out.parent.mkdir(parents=True,exist_ok=True)
    r=requests.get(url,timeout=120); r.raise_for_status(); out.write_bytes(r.content)
    print(f"Downloaded {len(r.content)/1024/1024:.1f} MiB -> {out}")

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('source',choices=['wind','solar']); p.add_argument('year',type=int); p.add_argument('month',type=int); p.add_argument('--dest',default='data/raw')
    a=p.parse_args(); download(a.source,a.year,a.month,a.dest)
