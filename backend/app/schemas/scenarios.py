"""Pydantic Schemas for Logistics Scenarios and Disruptions."""

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field


class DisruptionSchema(BaseModel):
    id: str
    type: str  # DEMAND_SURGE, ROUTE_BLOCKED, ROUTE_DEGRADED, WEATHER_DEGRADATION, VEHICLE_UNAVAILABLE
    target: str
    severity: float = Field(ge=0.0, le=1.0)
    start_time: int = Field(ge=0)
    duration: int = Field(gt=0)
    impact_factor: float
    description: Optional[str] = ""


class ScenarioResponse(BaseModel):
    name: str
    description: Optional[str] = ""
    horizon_hours: int = 336
    disruptions: List[DisruptionSchema] = Field(default_factory=list)


class ScenarioCreateRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    horizon_hours: int = 336
    disruptions: List[DisruptionSchema] = Field(default_factory=list)
