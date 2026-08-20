from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import pandas as pd
from app.core.config import settings
from ml.modeling import train_models

if __name__=='__main__':
    df=pd.read_csv(settings.resolve(settings.demo_data_path))
    print(train_models(df,settings.resolve(settings.model_dir)))
