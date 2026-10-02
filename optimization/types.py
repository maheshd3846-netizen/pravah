"""Core Types, Enums, and Data Contracts for PRAVAH Logistics Optimization Core."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class DemandPolicy(str, Enum):
    """Demand quantile policy driving required optimization demand."""
    P50 = "P50"
    P80 = "P80"
    P95 = "P95"


class SolverType(str, Enum):
    """Optimization solver engine types."""
    MILP = "MILP"
    HEURISTIC = "HEURISTIC"


class OptimizationStatus(str, Enum):
    """Status outcomes from mathematical solver execution."""
    OPTIMAL = "OPTIMAL"
    FEASIBLE = "FEASIBLE"
    INFEASIBLE = "INFEASIBLE"
    UNBOUNDED = "UNBOUNDED"
    TIME_LIMIT = "TIME_LIMIT"
    ERROR = "ERROR"


class ReasonCode(str, Enum):
    """Deterministic military operational reason codes explaining decisions."""
    STOCKOUT_RISK = "STOCKOUT_RISK"
    SAFETY_STOCK_BREACH = "SAFETY_STOCK_BREACH"
    HIGH_PRIORITY_NODE = "HIGH_PRIORITY_NODE"
    ROUTE_RISK = "ROUTE_RISK"
    ROUTE_BLOCKED = "ROUTE_BLOCKED"
    LOWER_RISK_DETOUR = "LOWER_RISK_DETOUR"
    VEHICLE_CAPACITY = "VEHICLE_CAPACITY"
    DEMAND_SURGE = "DEMAND_SURGE"
    CRITICAL_INVENTORY = "CRITICAL_INVENTORY"


@dataclass
class ObjectiveWeights:
    """Configurable weights governing tradeoffs in the multi-objective function."""
    transport_weight: float = 1.0       # Cost per unit-distance
    shortage_weight: float = 50.0       # Penalty per unit of unmet critical demand
    delay_weight: float = 3.0           # Penalty per unit-hour of transit delay
    risk_weight: float = 10.0           # Penalty for traversing risky route corridors
    imbalance_weight: float = 1.0       # Penalty for post-fulfillment supply imbalance

    def to_dict(self) -> Dict[str, float]:
        return {
            "transport": self.transport_weight,
            "shortage": self.shortage_weight,
            "delay": self.delay_weight,
            "risk": self.risk_weight,
            "imbalance": self.imbalance_weight,
        }


@dataclass
class MovementDecision:
    """Concrete, executable logistics movement dispatch order."""
    decision_id: str
    source_node_id: str
    destination_node_id: str
    item: str
    quantity: float
    route_id: str
    vehicle_id: str
    dispatch_hour: int
    estimated_arrival_hour: int
    priority: int = 3
    reason_codes: List[str] = field(default_factory=list)
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "source_node_id": self.source_node_id,
            "destination_node_id": self.destination_node_id,
            "item": self.item,
            "quantity": round(self.quantity, 2),
            "route_id": self.route_id,
            "vehicle_id": self.vehicle_id,
            "dispatch_hour": self.dispatch_hour,
            "estimated_arrival_hour": self.estimated_arrival_hour,
            "priority": self.priority,
            "reason_codes": self.reason_codes,
            "rationale": self.rationale,
        }


@dataclass
class OptimizationResult:
    """Comprehensive, auditable optimization result bundle."""
    run_id: str
    status: OptimizationStatus
    solver_type: SolverType
    objective_value: float
    execution_time_ms: float
    demand_policy: DemandPolicy
    total_transport_cost: float
    total_shortage: float
    total_delay: float
    total_risk_cost: float
    vehicle_utilization: Dict[str, float] = field(default_factory=dict)
    route_utilization: Dict[str, float] = field(default_factory=dict)
    decisions: List[MovementDecision] = field(default_factory=list)
    infeasibility_reasons: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status.value,
            "solver_type": self.solver_type.value,
            "objective_value": round(self.objective_value, 2),
            "execution_time_ms": round(self.execution_time_ms, 2),
            "demand_policy": self.demand_policy.value,
            "total_transport_cost": round(self.total_transport_cost, 2),
            "total_shortage": round(self.total_shortage, 2),
            "total_delay": round(self.total_delay, 2),
            "total_risk_cost": round(self.total_risk_cost, 2),
            "vehicle_utilization": {k: round(v, 3) for k, v in self.vehicle_utilization.items()},
            "route_utilization": {k: round(v, 3) for k, v in self.route_utilization.items()},
            "decisions": [d.to_dict() for d in self.decisions],
            "infeasibility_reasons": self.infeasibility_reasons,
            "metadata": self.metadata,
        }
