"""Counterfactual Outcome Metrics, Deltas, and Tradeoff Analytics."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class MetricDirection(str, Enum):
    IMPROVED = "IMPROVED"
    DEGRADED = "DEGRADED"
    UNCHANGED = "UNCHANGED"


class EvaluationStatus(str, Enum):
    IMPROVED = "IMPROVED"
    DEGRADED = "DEGRADED"
    MIXED = "MIXED"
    INCONCLUSIVE = "INCONCLUSIVE"
    INVALID = "INVALID"


@dataclass
class MetricDelta:
    """Rigorous before/after comparative delta for a single KPI."""
    metric_name: str
    baseline: float
    optimized: float
    absolute_delta: float
    relative_delta_percent: float
    direction: MetricDirection
    is_better: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "baseline": round(self.baseline, 2),
            "optimized": round(self.optimized, 2),
            "absolute_delta": round(self.absolute_delta, 2),
            "relative_delta_percent": round(self.relative_delta_percent, 2),
            "direction": self.direction.value,
            "is_better": self.is_better,
        }


@dataclass
class SimulationRunMetrics:
    """Comprehensive performance metrics extracted from a single simulation trajectory."""
    total_requested_demand: float
    total_fulfilled_demand: float
    total_unmet_demand: float
    fulfillment_rate_percent: float
    total_stockout_events: int
    stockout_duration_hours: int
    nodes_affected_stockout: int
    items_affected_stockout: int
    safety_stock_breaches: int
    safety_stock_breach_hours: int
    initial_inventory_total: float
    final_inventory_total: float
    minimum_inventory_total: float
    average_inventory_total: float
    total_transport_distance_km: float
    total_transit_hours: float
    average_delay_hours: float
    maximum_delay_hours: float
    vehicle_utilization_rate: float
    active_fleet_count: int
    critical_node_metrics: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_requested_demand": round(self.total_requested_demand, 1),
            "total_fulfilled_demand": round(self.total_fulfilled_demand, 1),
            "total_unmet_demand": round(self.total_unmet_demand, 1),
            "fulfillment_rate_percent": round(self.fulfillment_rate_percent, 2),
            "total_stockout_events": self.total_stockout_events,
            "stockout_duration_hours": self.stockout_duration_hours,
            "nodes_affected_stockout": self.nodes_affected_stockout,
            "items_affected_stockout": self.items_affected_stockout,
            "safety_stock_breaches": self.safety_stock_breaches,
            "safety_stock_breach_hours": self.safety_stock_breach_hours,
            "initial_inventory_total": round(self.initial_inventory_total, 1),
            "final_inventory_total": round(self.final_inventory_total, 1),
            "minimum_inventory_total": round(self.minimum_inventory_total, 1),
            "average_inventory_total": round(self.average_inventory_total, 1),
            "total_transport_distance_km": round(self.total_transport_distance_km, 1),
            "total_transit_hours": round(self.total_transit_hours, 1),
            "average_delay_hours": round(self.average_delay_hours, 2),
            "maximum_delay_hours": round(self.maximum_delay_hours, 2),
            "vehicle_utilization_rate": round(self.vehicle_utilization_rate, 3),
            "active_fleet_count": self.active_fleet_count,
            "critical_node_metrics": self.critical_node_metrics,
        }


@dataclass
class ShipmentExecutionTrace:
    """Audit trace of planned vs actual physical movement execution."""
    decision_id: str
    item: str
    planned_quantity: float
    actual_dispatched_quantity: float
    actual_arrival_quantity: float
    source_node: str
    destination_node: str
    route_id: str
    vehicle_id: str
    departure_hour: int
    arrival_hour: int
    transit_delay_hours: float
    status: str  # DELIVERED, IN_TRANSIT, FAILED
    failure_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "item": self.item,
            "planned_quantity": round(self.planned_quantity, 1),
            "actual_dispatched_quantity": round(self.actual_dispatched_quantity, 1),
            "actual_arrival_quantity": round(self.actual_arrival_quantity, 1),
            "source_node": self.source_node,
            "destination_node": self.destination_node,
            "route_id": self.route_id,
            "vehicle_id": self.vehicle_id,
            "departure_hour": self.departure_hour,
            "arrival_hour": self.arrival_hour,
            "transit_delay_hours": round(self.transit_delay_hours, 1),
            "status": self.status,
            "failure_reason": self.failure_reason,
        }


@dataclass
class PlanEvaluationResult:
    """Complete, auditable comparative evaluation report."""
    evaluation_id: str
    optimization_run_id: str
    scenario_id: str
    status: EvaluationStatus
    horizon_hours: int
    seed: int
    initial_state_hash: str
    baseline: SimulationRunMetrics
    optimized: SimulationRunMetrics
    deltas: Dict[str, MetricDelta]
    tradeoffs: Dict[str, str]
    critical_nodes: List[Dict[str, Any]]
    shipment_trace: List[ShipmentExecutionTrace]
    plan_validation_status: str
    plan_validation_violations: List[str]
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "optimization_run_id": self.optimization_run_id,
            "scenario_id": self.scenario_id,
            "status": self.status.value,
            "horizon_hours": self.horizon_hours,
            "seed": self.seed,
            "initial_state_hash": self.initial_state_hash,
            "baseline": self.baseline.to_dict(),
            "optimized": self.optimized.to_dict(),
            "deltas": {k: v.to_dict() for k, v in self.deltas.items()},
            "tradeoffs": self.tradeoffs,
            "critical_nodes": self.critical_nodes,
            "shipment_trace": [t.to_dict() for t in self.shipment_trace],
            "plan_validation": {
                "status": self.plan_validation_status,
                "violations": self.plan_validation_violations,
            },
            "created_at": self.created_at,
        }
