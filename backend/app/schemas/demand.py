"""Pydantic Schemas for Tactical Demand."""

from __future__ import annotations
from typing import Dict, List
from pydantic import BaseModel


class DemandPointResponse(BaseModel):
    node_id: str
    node_code: str
    item: str
    timestamp_hour: int
    requested_demand: float
    fulfilled_demand: float
    unmet_demand: float


class DemandOverviewResponse(BaseModel):
    total_requested: float
    total_fulfilled: float
    total_unmet: float
    overall_fulfillment_rate: float
    by_category: Dict[str, Dict[str, float]]
    recent_sample: List[DemandPointResponse]
