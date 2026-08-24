"""Training and evaluation pipeline for the synthetic curtailment demo."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    mean_absolute_error,
    precision_recall_fscore_support,
    roc_auc_score,
    root_mean_squared_error,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ml.constants import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    TARGET_CLASS,
    TARGET_REGRESSION,
)
from ml.features import model_frame


def _preprocessor(*, scale: bool = False) -> ColumnTransformer:
    numeric_steps = [("imputer", SimpleImputer(strategy="median"))]
    if scale:
        numeric_steps.append(("scaler", StandardScaler()))

    return ColumnTransformer(
        [
            ("num", Pipeline(numeric_steps), NUMERIC_FEATURES),
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        (
                            "onehot",
                            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                        ),
                    ]
                ),
                CATEGORICAL_FEATURES,
            ),
        ]
    )


def _best_threshold(y_true, probabilities) -> float:
    best_threshold = 0.5
    best_f1 = -1.0

    for threshold in np.linspace(0.12, 0.80, 69):
        predictions = (probabilities >= threshold).astype(int)
        _, _, f1, _ = precision_recall_fscore_support(
            y_true,
            predictions,
            average="binary",
            zero_division=0,
        )
        if f1 > best_f1:
            best_threshold = float(threshold)
            best_f1 = float(f1)

    return best_threshold


def _build_classifier_candidates() -> dict[str, Pipeline]:
    baseline = Pipeline(
        [
            ("prep", _preprocessor(scale=True)),
            (
                "model",
                LogisticRegression(
                    max_iter=1500,
                    class_weight="balanced",
                    C=0.8,
                ),
            ),
        ]
    )

    # Dense one-hot + histogram boosting keeps the demo dependency footprint small.
    boosted = Pipeline(
        [
            ("prep", _preprocessor(scale=False)),
            (
                "model",
                HistGradientBoostingClassifier(
                    max_iter=220,
                    learning_rate=0.06,
                    max_leaf_nodes=25,
                    l2_regularization=1.0,
                    random_state=42,
                ),
            ),
        ]
    )

    return {
        "logistic_baseline": baseline,
        "hist_gradient_boosting": boosted,
    }


def train_models(df: pd.DataFrame, output_dir: str | Path) -> dict:
    """Train classifier/regressor artifacts with chronological 70/15/15 splits."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    ordered = df.sort_values("timestamp").reset_index(drop=True)
    row_count = len(ordered)
    train_end = int(row_count * 0.70)
    validation_end = int(row_count * 0.85)

    train = ordered.iloc[:train_end]
    validation = ordered.iloc[train_end:validation_end]
    test = ordered.iloc[validation_end:]

    train_features = model_frame(train)
    validation_features = model_frame(validation)
    test_features = model_frame(test)
    train_target = train[TARGET_CLASS]
    validation_target = validation[TARGET_CLASS]
    test_target = test[TARGET_CLASS]

    candidates = _build_classifier_candidates()
    validation_scores: dict[str, dict[str, float]] = {}
    best_name: str | None = None
    best_pr_auc = -1.0

    for name, model in candidates.items():
        model.fit(train_features, train_target)
        probabilities = model.predict_proba(validation_features)[:, 1]
        pr_auc = float(average_precision_score(validation_target, probabilities))
        validation_scores[name] = {
            "validation_pr_auc": pr_auc,
            "validation_roc_auc": float(roc_auc_score(validation_target, probabilities)),
        }
        if pr_auc > best_pr_auc:
            best_name = name
            best_pr_auc = pr_auc

    if best_name is None:
        raise RuntimeError("Could not select a classifier candidate.")

    classifier = candidates[best_name]
    validation_probabilities = classifier.predict_proba(validation_features)[:, 1]
    threshold = _best_threshold(validation_target, validation_probabilities)

    test_probabilities = classifier.predict_proba(test_features)[:, 1]
    test_predictions = (test_probabilities >= threshold).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(
        test_target,
        test_predictions,
        average="binary",
        zero_division=0,
    )

    positive_train = train[train[TARGET_REGRESSION] > 0].copy()
    regressor = Pipeline(
        [
            ("prep", _preprocessor(scale=False)),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=100,
                    min_samples_leaf=4,
                    max_features=0.75,
                    n_jobs=-1,
                    random_state=42,
                ),
            ),
        ]
    )
    regressor.fit(model_frame(positive_train), positive_train[TARGET_REGRESSION])

    positive_test = test[test[TARGET_REGRESSION] > 0]
    if len(positive_test):
        regression_predictions = regressor.predict(model_frame(positive_test))
        mae = float(mean_absolute_error(positive_test[TARGET_REGRESSION], regression_predictions))
        rmse = float(
            root_mean_squared_error(
                positive_test[TARGET_REGRESSION],
                regression_predictions,
            )
        )
    else:
        mae = 0.0
        rmse = 0.0

    version = datetime.now(timezone.utc).strftime("demo-%Y%m%d%H%M%S")
    metrics = {
        "model_version": version,
        "selected_classifier": best_name,
        "decision_threshold": threshold,
        "dataset_rows": int(row_count),
        "train_rows": len(train),
        "validation_rows": len(validation),
        "test_rows": len(test),
        "test_event_rate": float(test_target.mean()),
        "classifier": {
            "pr_auc": float(average_precision_score(test_target, test_probabilities)),
            "roc_auc": float(roc_auc_score(test_target, test_probabilities)),
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "brier": float(brier_score_loss(test_target, test_probabilities)),
        },
        "regressor": {
            "mae_mwh": mae,
            "rmse_mwh": rmse,
        },
        "candidate_validation_scores": validation_scores,
        "split_strategy": "chronological 70/15/15",
        "data_mode": "synthetic_demo",
    }

    joblib.dump(classifier, output / "curtailment_classifier.joblib")
    joblib.dump(regressor, output / "curtailed_energy_regressor.joblib")
    (output / "metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return metrics
