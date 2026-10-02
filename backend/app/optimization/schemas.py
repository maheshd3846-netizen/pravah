"""Pydantic Request & Response Schemas for Logistics Optimization Endpoints."""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from optimization.types import DemandPolicy, SolverType, OptimizationStatus


class OptimizationSolveRequest(BaseModel):
    """Payload to trigger risk-aware mathematical optimization."""
    scenario_id: str = Field(default="DEFAULT", description="Disruption scenario identifier")
    demand_policy: DemandPolicy = Field(default=DemandPolicy.P80, description="Demand policy: P50, P80, or P95")
    solver_type: SolverType = Field(default=SolverType.MILP, description="Solver engine: MILP or HEURISTIC")
    objective_weights: Optional[Dict[str, float]] = Field(
        default=None,
        description="Weights for transport, shortage, delay, risk, and imbalance",
    )
    horizon_hours: int = Field(default=72, ge=1, le=336, description="Planning horizon in hours")


class MovementDecisionSchema(BaseModel):
    decision_id: str
    source_node_id: str
    destination_node_id: str
    item: str
    quantity: float
    route_id: str
    vehicle_id: str
    dispatch_hour: int
    estimated_arrival_hour: int
    priority: int
    reason_codes: List[str]
    rationale: str


class OptimizationSolveResponse(BaseModel):
    """Comprehensive, auditable optimization result bundle."""
    run_id: str
    status: str
    solver_type: str
    objective_value: float
    execution_time_ms: float
    demand_policy: str
    total_transport_cost: float
    total_shortage: float
    total_delay: float
    total_risk_cost: float
    vehicle_utilization: Dict[str, float]
    route_utilization: Dict[str, float]
    decisions: List[MovementDecisionSchema]
    infeasibility_reasons: List[str]
    metadata: Dict[str, Any]
