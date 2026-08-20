from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import argparse
from pathlib import Path
from sqlalchemy import delete
from app.core.config import settings
from app.core.db import Base, engine, SessionLocal
from app.models import Plant, PredictionLog, OptimizationScenario
from ml.synthetic import generate_synthetic_dataset
from ml.modeling import train_models


def main(skip_train=False):
    data_path=settings.resolve(settings.demo_data_path)
    model_dir=settings.resolve(settings.model_dir)
    df=generate_synthetic_dataset(data_path,periods=4100,seed=42)
    if not skip_train:
        metrics=train_models(df,model_dir)
        print("Selected model:",metrics["selected_classifier"])
        print("PR-AUC:",round(metrics["classifier"]["pr_auc"],4),"F1:",round(metrics["classifier"]["f1"],4))
    Base.metadata.create_all(engine)
    plants=df[["plant_code","plant_name","source","region","capacity_mw"]].drop_duplicates()
    with SessionLocal() as db:
        db.execute(delete(PredictionLog)); db.execute(delete(OptimizationScenario)); db.execute(delete(Plant))
        for r in plants.itertuples(index=False):
            db.add(Plant(code=r.plant_code,name=r.plant_name,source=r.source,region=r.region,capacity_mw=float(r.capacity_mw)))
        db.commit()
    print(f"Demo ready: {len(df):,} rows, {len(plants)} plants")

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--skip-train',action='store_true')
    args=parser.parse_args(); main(skip_train=args.skip_train)
