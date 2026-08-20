import io, json
from pathlib import Path
import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.db import get_db
from app.models import Plant, PredictionLog, OptimizationScenario
from app.schemas import PredictionRequest, PredictionResponse, DispatchInputs, OptimizationResponse, CsvInspectionResponse, PlantOut
from app.services import analytics
from app.services.data_service import plant_history, load_demo_data
from app.services.model_service import predict, artifacts
from app.services.optimizer import optimize_dispatch
from ml.ons_adapter import normalize_name, detect_mapping, inspect_dataframe

router=APIRouter(prefix="/api/v1")

@router.get("/overview")
def get_overview(): return analytics.overview()

@router.get("/plants",response_model=list[PlantOut])
def get_plants(db:Session=Depends(get_db)):
    return [PlantOut(code=p.code,name=p.name,source=p.source,region=p.region,capacity_mw=p.capacity_mw) for p in db.scalars(select(Plant).order_by(Plant.code)).all()]

@router.get("/plants/{plant_code}/history")
def get_history(plant_code:str,limit:int=168):
    try:return {"plant_code":plant_code,"points":plant_history(plant_code,min(max(limit,24),1000))}
    except KeyError:raise HTTPException(404,"Plant not found")

@router.get("/plants/{plant_code}/forecast",response_model=PredictionResponse)
def get_forecast(plant_code:str,db:Session=Depends(get_db)):
    try: result=predict(plant_code)
    except KeyError: raise HTTPException(404,"Plant not found")
    db.add(PredictionLog(plant_code=plant_code,risk_probability=result["risk_probability"],predicted_curtailed_mwh=result["predicted_curtailed_mwh"],model_version=result["model_version"],request_json="{}")); db.commit()
    return result

@router.post("/predict",response_model=PredictionResponse)
def post_predict(payload:PredictionRequest,db:Session=Depends(get_db)):
    data=payload.features.model_dump() if payload.features else None
    try: result=predict(payload.plant_code,data)
    except KeyError: raise HTTPException(404,"Plant not found")
    db.add(PredictionLog(plant_code=payload.plant_code,risk_probability=result["risk_probability"],predicted_curtailed_mwh=result["predicted_curtailed_mwh"],model_version=result["model_version"],request_json=payload.model_dump_json())); db.commit()
    return result

@router.post("/optimize",response_model=OptimizationResponse)
def post_optimize(payload:DispatchInputs,db:Session=Depends(get_db)):
    try: result=optimize_dispatch(payload.model_dump())
    except ValueError as exc: raise HTTPException(422,str(exc))
    db.add(OptimizationScenario(plant_code=payload.plant_code,recovered_mwh=result["recovered_mwh"],lost_mwh=result["lost_mwh"],recovery_rate_pct=result["recovery_rate_pct"],strategy_summary=result["strategy_summary"],input_json=payload.model_dump_json(),result_json=json.dumps(result))); db.commit()
    return result

@router.get("/scenarios")
def get_scenarios(limit:int=20,db:Session=Depends(get_db)):
    rows=db.scalars(select(OptimizationScenario).order_by(OptimizationScenario.id.desc()).limit(min(limit,100))).all()
    return [{"id":r.id,"created_at":r.created_at,"plant_code":r.plant_code,"recovered_mwh":r.recovered_mwh,"lost_mwh":r.lost_mwh,"recovery_rate_pct":r.recovery_rate_pct,"strategy_summary":r.strategy_summary} for r in rows]

@router.get("/analytics/patterns")
def get_patterns(): return analytics.patterns()

@router.get("/model/metrics")
def get_metrics(): return artifacts()[2]

@router.post("/data/inspect-csv",response_model=CsvInspectionResponse)
async def inspect_csv(file:UploadFile=File(...)):
    raw=await file.read()
    if len(raw)>25_000_000: raise HTTPException(413,"CSV is too large for inspection endpoint")
    df=None; errors=[]
    for sep in [";",",","\t"]:
        try:
            candidate=pd.read_csv(io.BytesIO(raw),sep=sep,encoding="utf-8")
            if len(candidate.columns)>1: df=candidate; break
        except Exception as exc: errors.append(str(exc))
    if df is None: raise HTTPException(422,"Could not parse CSV")
    mapping,warnings=inspect_dataframe(df)
    return CsvInspectionResponse(rows=len(df),columns=list(map(str,df.columns)),normalized_columns=[normalize_name(c) for c in df.columns],detected_mapping=mapping,warnings=warnings)
