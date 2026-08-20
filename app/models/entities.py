from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base


def utcnow():
    return datetime.now(timezone.utc)


class Plant(Base):
    __tablename__ = "plants"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(180))
    source: Mapped[str] = mapped_column(String(20), index=True)
    region: Mapped[str] = mapped_column(String(20), index=True)
    capacity_mw: Mapped[float] = mapped_column(Float)


class PredictionLog(Base):
    __tablename__ = "prediction_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plant_code: Mapped[str] = mapped_column(String(80), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    risk_probability: Mapped[float] = mapped_column(Float)
    predicted_curtailed_mwh: Mapped[float] = mapped_column(Float)
    model_version: Mapped[str] = mapped_column(String(80))
    request_json: Mapped[str] = mapped_column(Text)


class OptimizationScenario(Base):
    __tablename__ = "optimization_scenarios"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    plant_code: Mapped[str] = mapped_column(String(80), index=True)
    recovered_mwh: Mapped[float] = mapped_column(Float)
    lost_mwh: Mapped[float] = mapped_column(Float)
    recovery_rate_pct: Mapped[float] = mapped_column(Float)
    strategy_summary: Mapped[str] = mapped_column(String(200))
    input_json: Mapped[str] = mapped_column(Text)
    result_json: Mapped[str] = mapped_column(Text)
