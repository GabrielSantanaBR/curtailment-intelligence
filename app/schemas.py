"""Pydantic request/response contracts used by the API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class PlantOut(BaseModel):
    code: str
    name: str
    source: str
    region: str
    capacity_mw: float


class FeaturePayload(BaseModel):
    timestamp: datetime
    source: str = Field(pattern="^(wind|solar)$")
    region: str
    capacity_mw: float = Field(gt=0)
    available_generation_mw: float = Field(ge=0)
    system_load_mw: float = Field(gt=0)
    renewable_share_pct: float = Field(ge=0, le=100)
    network_stress_index: float = Field(ge=0, le=1)
    recent_curtailment_rate_24h: float = Field(ge=0, le=1)
    recent_curtailment_mwh_24h: float = Field(ge=0)
    wind_speed_ms: float = Field(ge=0)
    solar_irradiance_wm2: float = Field(ge=0)
    temperature_c: float


class PredictionRequest(BaseModel):
    plant_code: str
    features: FeaturePayload | None = None


class ExplanationItem(BaseModel):
    feature: str
    label: str
    effect: float
    direction: str
    current_value: float | str


class PredictionResponse(BaseModel):
    plant_code: str
    timestamp: datetime
    risk_probability: float
    risk_level: str
    decision_threshold: float
    predicted_curtailed_mwh: float
    explanation: list[ExplanationItem]
    model_version: str
    data_mode: str


class DispatchInputs(BaseModel):
    plant_code: str = "DEMO-WIND-01"
    curtailed_profile_mwh: list[float] = Field(min_length=1, max_length=48)
    battery_capacity_mwh: float = Field(default=80, ge=0)
    battery_initial_soc_mwh: float = Field(default=10, ge=0)
    battery_max_charge_mw: float = Field(default=40, ge=0)
    battery_roundtrip_efficiency: float = Field(default=0.90, gt=0, le=1)
    flexible_load_capacity_mw: float = Field(default=20, ge=0)
    flexible_load_total_mwh: float = Field(default=40, ge=0)
    energy_value_brl_mwh: float = Field(default=220, ge=0)
    grid_factor_tco2_mwh: float = Field(default=0.08, ge=0)

    @field_validator("curtailed_profile_mwh")
    @classmethod
    def validate_profile(cls, values: list[float]) -> list[float]:
        if any(value < 0 for value in values):
            raise ValueError("curtailed_profile_mwh cannot contain negative values")
        return values

    @model_validator(mode="after")
    def validate_battery_state(self):
        if self.battery_initial_soc_mwh > self.battery_capacity_mwh:
            raise ValueError("battery_initial_soc_mwh cannot exceed battery_capacity_mwh")
        return self


class HourDispatch(BaseModel):
    hour: int
    available_mwh: float
    battery_charge_mwh: float
    flexible_load_mwh: float
    recovered_mwh: float
    lost_mwh: float
    battery_soc_mwh: float


class OptimizationResponse(BaseModel):
    plant_code: str
    total_available_mwh: float
    recovered_mwh: float
    lost_mwh: float
    recovery_rate_pct: float
    estimated_value_preserved_brl: float
    estimated_avoided_tco2: float
    strategy_summary: str
    dispatch: list[HourDispatch]
    assumptions: list[str]


class CsvInspectionResponse(BaseModel):
    rows: int
    columns: list[str]
    normalized_columns: list[str]
    detected_mapping: dict[str, str]
    warnings: list[str]
