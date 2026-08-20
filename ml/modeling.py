import json
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score, roc_auc_score, precision_recall_fscore_support,
    brier_score_loss, mean_absolute_error, root_mean_squared_error
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from ml.constants import NUMERIC_FEATURES, CATEGORICAL_FEATURES, TARGET_CLASS, TARGET_REGRESSION
from ml.features import model_frame


def _preprocessor(scale: bool = False):
    num_steps=[("imputer",SimpleImputer(strategy="median"))]
    if scale: num_steps.append(("scaler",StandardScaler()))
    return ColumnTransformer([
        ("num",Pipeline(num_steps),NUMERIC_FEATURES),
        ("cat",Pipeline([
            ("imputer",SimpleImputer(strategy="most_frequent")),
            ("onehot",OneHotEncoder(handle_unknown="ignore",sparse_output=False))
        ]),CATEGORICAL_FEATURES)
    ])


def _best_threshold(y_true, p):
    best=(0.5,-1)
    for t in np.linspace(0.12,0.80,69):
        pred=(p>=t).astype(int)
        _,_,f1,_=precision_recall_fscore_support(y_true,pred,average="binary",zero_division=0)
        if f1>best[1]: best=(float(t),float(f1))
    return best[0]


def train_models(df: pd.DataFrame, output_dir: str | Path):
    out=Path(output_dir); out.mkdir(parents=True,exist_ok=True)
    ordered=df.sort_values("timestamp").reset_index(drop=True)
    n=len(ordered); a=int(n*0.70); b=int(n*0.85)
    train,val,test=ordered.iloc[:a],ordered.iloc[a:b],ordered.iloc[b:]
    Xtr,Xv,Xt=model_frame(train),model_frame(val),model_frame(test)
    ytr,yv,yt=train[TARGET_CLASS],val[TARGET_CLASS],test[TARGET_CLASS]

    baseline=Pipeline([
        ("prep",_preprocessor(scale=True)),
        ("model",LogisticRegression(max_iter=1500,class_weight="balanced",C=0.8))
    ])
    baseline.fit(Xtr,ytr)

    # Dense one-hot + histogram boosting keeps the demo dependency footprint small.
    boosted=Pipeline([
        ("prep",_preprocessor(scale=False)),
        ("model",HistGradientBoostingClassifier(max_iter=220,learning_rate=0.06,max_leaf_nodes=25,l2_regularization=1.0,random_state=42))
    ])
    boosted.fit(Xtr,ytr)

    candidates={"logistic_baseline":baseline,"hist_gradient_boosting":boosted}
    scores={}
    best_name=None; best_pr=-1
    for name,model in candidates.items():
        pv=model.predict_proba(Xv)[:,1]
        pr=average_precision_score(yv,pv)
        scores[name] = {"validation_pr_auc":float(pr),"validation_roc_auc":float(roc_auc_score(yv,pv))}
        if pr>best_pr: best_name,best_pr=name,pr
    classifier=candidates[best_name]
    pval=classifier.predict_proba(Xv)[:,1]
    threshold=_best_threshold(yv,pval)
    ptest=classifier.predict_proba(Xt)[:,1]
    yhat=(ptest>=threshold).astype(int)
    precision,recall,f1,_=precision_recall_fscore_support(yt,yhat,average="binary",zero_division=0)

    positive=train[train[TARGET_REGRESSION]>0].copy()
    Xr=model_frame(positive); yr=positive[TARGET_REGRESSION]
    regressor=Pipeline([
        ("prep",_preprocessor(scale=False)),
        ("model",RandomForestRegressor(n_estimators=100,min_samples_leaf=4,max_features=0.75,n_jobs=-1,random_state=42))
    ])
    regressor.fit(Xr,yr)
    positive_test=test[test[TARGET_REGRESSION]>0]
    if len(positive_test):
        rp=regressor.predict(model_frame(positive_test))
        mae=float(mean_absolute_error(positive_test[TARGET_REGRESSION],rp))
        rmse=float(root_mean_squared_error(positive_test[TARGET_REGRESSION],rp))
    else: mae=rmse=0.0

    version=datetime.now(timezone.utc).strftime("demo-%Y%m%d%H%M%S")
    metrics={
        "model_version":version,
        "selected_classifier":best_name,
        "decision_threshold":threshold,
        "dataset_rows":int(n),
        "train_rows":len(train),"validation_rows":len(val),"test_rows":len(test),
        "test_event_rate":float(yt.mean()),
        "classifier":{
            "pr_auc":float(average_precision_score(yt,ptest)),
            "roc_auc":float(roc_auc_score(yt,ptest)),
            "precision":float(precision),"recall":float(recall),"f1":float(f1),
            "brier":float(brier_score_loss(yt,ptest)),
        },
        "regressor":{"mae_mwh":mae,"rmse_mwh":rmse},
        "candidate_validation_scores":scores,
        "split_strategy":"chronological 70/15/15",
        "data_mode":"synthetic_demo"
    }
    joblib.dump(classifier,out/'curtailment_classifier.joblib')
    joblib.dump(regressor,out/'curtailed_energy_regressor.joblib')
    (out/'metrics.json').write_text(json.dumps(metrics,indent=2,ensure_ascii=False),encoding='utf-8')
    return metrics
