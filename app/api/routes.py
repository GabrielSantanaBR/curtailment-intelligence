"""HTTP API routes.

Routes should stay thin: validate HTTP input, call a service and persist relevant
results. Business/model logic belongs in `app.services` or `ml`.
"""

from __future__ import annotations

import io
import json

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import OptimizationScenario, Plant, PredictionLog
from app.schemas import (
    CsvInspectionResponse,
    DispatchInputs,
    OptimizationResponse,
    PlantOut,
    PredictionRequest,
    PredictionResponse,
)
from app.services import analytics
from app.services.data_service import plant_history
from app.services.model_service import artifacts, predict
from app.services.optimizer import optimize_dispatch
from ml.ons_adapter import inspect_dataframe, normalize_name

router = APIRouter(prefix="/api/v1")
MAX_CSV_BYTES = 25_000_000


def _save_prediction(db: Session, plant_code: str, result: dict, request_json: str) -> None:
    db.add(
        PredictionLog(
            plant_code=plant_code,
            risk_probability=result["risk_probability"],
            predicted_curtailed_mwh=result["predicted_curtailed_mwh"],
            model_version=result["model_version"],
            request_json=request_json,
        )
    )
    db.commit()


def _parse_uploaded_csv(raw: bytes) -> pd.DataFrame:
    for separator in [";", ",", "\t"]:
        try:
            candidate = pd.read_csv(io.BytesIO(raw), sep=separator, encoding="utf-8")
        except (UnicodeDecodeError, pd.errors.ParserError):
            continue
        if len(candidate.columns) > 1:
            return candidate
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Could not parse CSV. Expected UTF-8 with comma, semicolon or tab delimiter.",
    )


@router.get("/overview")
def get_overview() -> dict:
    return analytics.overview()


@router.get("/plants", response_model=list[PlantOut])
def get_plants(db: Session = Depends(get_db)) -> list[PlantOut]:
    rows = db.scalars(select(Plant).order_by(Plant.code)).all()
    return [
        PlantOut(
            code=plant.code,
            name=plant.name,
            source=plant.source,
            region=plant.region,
            capacity_mw=plant.capacity_mw,
        )
        for plant in rows
    ]


@router.get("/plants/{plant_code}/history")
def get_history(plant_code: str, limit: int = 168) -> dict:
    safe_limit = min(max(limit, 24), 1000)
    try:
        points = plant_history(plant_code, safe_limit)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Plant not found") from exc
    return {"plant_code": plant_code, "points": points}


@router.get("/plants/{plant_code}/forecast", response_model=PredictionResponse)
def get_forecast(
    plant_code: str,
    db: Session = Depends(get_db),
) -> PredictionResponse:
    try:
        result = predict(plant_code)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Plant not found") from exc

    _save_prediction(db, plant_code, result, request_json="{}")
    return PredictionResponse(**result)


@router.post("/predict", response_model=PredictionResponse)
def post_predict(
    payload: PredictionRequest,
    db: Session = Depends(get_db),
) -> PredictionResponse:
    features = payload.features.model_dump() if payload.features else None
    try:
        result = predict(payload.plant_code, features)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Plant not found") from exc

    _save_prediction(db, payload.plant_code, result, payload.model_dump_json())
    return PredictionResponse(**result)


@router.post("/optimize", response_model=OptimizationResponse)
def post_optimize(
    payload: DispatchInputs,
    db: Session = Depends(get_db),
) -> OptimizationResponse:
    try:
        result = optimize_dispatch(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    db.add(
        OptimizationScenario(
            plant_code=payload.plant_code,
            recovered_mwh=result["recovered_mwh"],
            lost_mwh=result["lost_mwh"],
            recovery_rate_pct=result["recovery_rate_pct"],
            strategy_summary=result["strategy_summary"],
            input_json=payload.model_dump_json(),
            result_json=json.dumps(result),
        )
    )
    db.commit()
    return OptimizationResponse(**result)


@router.get("/scenarios")
def get_scenarios(limit: int = 20, db: Session = Depends(get_db)) -> list[dict]:
    safe_limit = min(max(limit, 1), 100)
    rows = db.scalars(
        select(OptimizationScenario)
        .order_by(OptimizationScenario.id.desc())
        .limit(safe_limit)
    ).all()
    return [
        {
            "id": row.id,
            "created_at": row.created_at,
            "plant_code": row.plant_code,
            "recovered_mwh": row.recovered_mwh,
            "lost_mwh": row.lost_mwh,
            "recovery_rate_pct": row.recovery_rate_pct,
            "strategy_summary": row.strategy_summary,
        }
        for row in rows
    ]


@router.get("/analytics/patterns")
def get_patterns() -> dict:
    return analytics.patterns()


@router.get("/model/metrics")
def get_metrics() -> dict:
    return artifacts()[2]


@router.post("/data/inspect-csv", response_model=CsvInspectionResponse)
async def inspect_csv(file: UploadFile = File(...)) -> CsvInspectionResponse:
    raw = await file.read()
    if len(raw) > MAX_CSV_BYTES:
        raise HTTPException(status_code=413, detail="CSV is too large for inspection endpoint")

    dataframe = _parse_uploaded_csv(raw)
    mapping, warnings = inspect_dataframe(dataframe)
    return CsvInspectionResponse(
        rows=len(dataframe),
        columns=list(map(str, dataframe.columns)),
        normalized_columns=[normalize_name(column) for column in dataframe.columns],
        detected_mapping=mapping,
        warnings=warnings,
    )
