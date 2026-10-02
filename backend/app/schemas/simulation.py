"""Pydantic Schemas for Simulation Execution and State Inspection."""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from backend.app.schemas.scenarios import DisruptionSchema


class SimulationRunRequest(BaseModel):
    scenario_name: str = "COMPOUND_DISRUPTION"
    seed: int = 42
    start_hour: int = 0
    horizon_hours: int = 336
    auto_replenish: bool = True
    custom_disruptions: Optional[List[DisruptionSchema]] = None


class CriticalNodeSummary(BaseModel):
    node_code: str
    unmet_demand: float


class SimulationRunResponse(BaseModel):
    run_id: str
    scenario_name: str
    seed: int
    horizon_hours: int
    total_requested_demand: float
    total_fulfilled_demand: float
    total_unmet_demand: float
    fulfillment_rate_percent: float
    total_stockout_events: int
    stockout_hours_total: int
    critical_nodes: List[CriticalNodeSummary]
    earliest_stockout_hour: Optional[int]
    active_disruptions_count: int
    summary_metrics: Dict[str, Any]
    shipment_count: int


class SimulationStateResponse(BaseModel):
    run_id: str
    current_hour: int
    horizon_hours: int
    is_completed: bool
    summary: Dict[str, Any]
    active_disruptions: List[Dict[str, Any]]
    active_shipments: List[Dict[str, Any]]
    completed_shipments_count: int
    critical_nodes: List[Dict[str, Any]]
