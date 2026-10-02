"""Optimization Problem Formulation and Plan Representations for PRAVAH."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from optimization.types import (
    DemandPolicy,
    SolverType,
    OptimizationStatus,
    ObjectiveWeights,
    MovementDecision,
    OptimizationResult,
)

# Backward compatibility alias
SupplyDecision = MovementDecision


@dataclass
class OptimizationProblem:
    """Rigorous mathematical representation of the tactical forward supply network."""
    problem_id: str
    nodes: Dict[str, Any]
    routes: Dict[str, Any]
    vehicles: Dict[str, Any]
    items: List[str]
    available_supply: Dict[str, Dict[str, float]]
    required_demand: Dict[str, Dict[str, float]]
    safety_stocks: Dict[str, Dict[str, float]] = field(default_factory=dict)
    node_risks: Dict[str, float] = field(default_factory=dict)
    route_risks: Dict[str, float] = field(default_factory=dict)
    demand_policy: DemandPolicy = DemandPolicy.P80
    objective_weights: ObjectiveWeights = field(default_factory=ObjectiveWeights)
    horizon_hours: int = 72
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Backward compatibility properties
    @property
    def current_inventory(self) -> Dict[str, Dict[str, float]]:
        return self.available_supply

    @property
    def projected_demands(self) -> List[Any]:
        # Synthesize demand objects for legacy compatibility if accessed
        legacy = []
        for nid, item_map in self.required_demand.items():
            for item, dem in item_map.items():
                legacy.append(type("LegacyDemand", (), {"node_id": nid, "item": item, "requested_demand": dem}))
        return legacy


@dataclass
class OptimizationPlan:
    """Legacy and service wrapper around OptimizationResult."""
    plan_id: str
    solver_name: str
    decisions: List[SupplyDecision]
    projected_unmet_before: float
    projected_unmet_after: float
    mitigation_percentage: float
    execution_time_ms: float
    result: Optional[OptimizationResult] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "solver_name": self.solver_name,
            "decisions": [d.to_dict() for d in self.decisions],
            "projected_unmet_before": round(self.projected_unmet_before, 2),
            "projected_unmet_after": round(self.projected_unmet_after, 2),
            "mitigation_percentage": round(self.mitigation_percentage, 2),
            "execution_time_ms": round(self.execution_time_ms, 2),
        }
