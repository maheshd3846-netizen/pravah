"""Pydantic Request & Response Schemas for Logistics Optimization Endpoints."""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator

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

    @field_validator("solver_type", mode="before")
    @classmethod
    def normalize_solver_type(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.upper()
        return v

    @field_validator("demand_policy", mode="before")
    @classmethod
    def normalize_demand_policy(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.upper()
        return v


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


class OptimizationEvaluateRequest(BaseModel):
    """Payload to trigger counterfactual paired evaluation of an optimization plan."""
    optimization_run_id: str = Field(..., description="ID of the optimization run to evaluate")
    scenario_id: str = Field(default="COMPOUND_DISRUPTION", description="Scenario configuration identifier")
    horizon_hours: int = Field(default=72, ge=1, le=336, description="Evaluation planning horizon in hours")
    seed: int = Field(default=42, description="Random seed for deterministic paired simulation")


class MetricDeltaSchema(BaseModel):
    metric_name: str
    baseline: float
    optimized: float
    absolute_delta: float
    relative_delta_percent: float
    direction: str
    is_better: bool


class OptimizationEvaluateResponse(BaseModel):
    """Complete, auditable closed-loop comparative evaluation response."""
    evaluation_id: str
    optimization_run_id: str
    scenario_id: str
    status: str
    horizon_hours: int
    seed: int
    initial_state_hash: str
    baseline: Dict[str, Any]
    optimized: Dict[str, Any]
    deltas: Dict[str, MetricDeltaSchema]
    tradeoffs: Dict[str, str]
    critical_nodes: List[Dict[str, Any]]
    shipment_trace: List[Dict[str, Any]]
    plan_validation: Dict[str, Any]
    created_at: str
