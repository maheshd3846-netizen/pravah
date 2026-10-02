"""Optimization Data Models and Decision Structures."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class SupplyDecision:
    decision_id: str
    source_node_id: str
    destination_node_id: str
    item: str
    quantity: float
    route_id: str
    vehicle_id: str
    dispatch_hour: int
    estimated_arrival_hour: int
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "source_node_id": self.source_node_id,
            "destination_node_id": self.destination_node_id,
            "item": self.item,
            "quantity": self.quantity,
            "route_id": self.route_id,
            "vehicle_id": self.vehicle_id,
            "dispatch_hour": self.dispatch_hour,
            "estimated_arrival_hour": self.estimated_arrival_hour,
            "rationale": self.rationale,
        }


@dataclass
class OptimizationProblem:
    problem_id: str
    horizon_hours: int
    nodes: Dict[str, Any]
    routes: Dict[str, Any]
    vehicles: Dict[str, Any]
    projected_demands: List[Any]
    current_inventory: Dict[str, Dict[str, float]]
    active_disruptions: List[Any] = field(default_factory=list)


@dataclass
class OptimizationPlan:
    plan_id: str
    solver_name: str
    decisions: List[SupplyDecision]
    projected_unmet_before: float
    projected_unmet_after: float
    mitigation_percentage: float
    execution_time_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "solver_name": self.solver_name,
            "decisions": [d.to_dict() for d in self.decisions],
            "projected_unmet_before": self.projected_unmet_before,
            "projected_unmet_after": self.projected_unmet_after,
            "mitigation_percentage": self.mitigation_percentage,
            "execution_time_ms": self.execution_time_ms,
        }
