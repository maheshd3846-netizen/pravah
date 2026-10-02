"""Optimization Plan Adapter and Pre-Simulation Feasibility Validator."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any, Optional

from optimization.types import MovementDecision, OptimizationResult
from optimization.model import OptimizationPlan
from simulation.world_generator import RouteStatus, VehicleStatus


@dataclass
class PlanValidationResult:
    """Pre-execution validation verdict on proposed optimization directives."""
    is_feasible: bool
    status: str  # PLAN_FEASIBLE or PLAN_INVALID
    violations: List[str] = field(default_factory=list)


@dataclass
class ExecutableIntervention:
    """Discrete simulation intervention ready for chronological dispatch injection."""
    intervention_id: str
    source_node_id: str
    destination_node_id: str
    item: str
    quantity: float
    route_id: str
    vehicle_id: str
    planned_departure_hour: int
    planned_eta_hour: int
    priority: int = 3
    reason_codes: List[str] = field(default_factory=list)
    rationale: str = ""


OPTIMIZER_TO_SIM_COMMODITY: Dict[str, str] = {
    "RATIONS": "FOOD",
    "AMMUNITION": "GENERAL_CRITICAL",
    "FOOD": "FOOD",
    "WATER": "WATER",
    "FUEL": "FUEL",
    "MEDICAL": "MEDICAL",
    "GENERAL_CRITICAL": "GENERAL_CRITICAL",
}


class OptimizationPlanAdapter:
    """Validates and adapts Phase 3A optimization decisions into simulation interventions."""

    @staticmethod
    def validate_plan(
        decisions: List[MovementDecision],
        initial_inventory: Dict[str, Dict[str, float]],
        routes: Dict[str, Any],
        vehicles: Dict[str, Any],
    ) -> PlanValidationResult:
        """Validates all physical constraints before simulator execution."""
        violations: List[str] = []

        # 1. Source supply depletion checks
        allocated_supply: Dict[Tuple[str, str], float] = {}
        for d in decisions:
            sim_item = OPTIMIZER_TO_SIM_COMMODITY.get(d.item, d.item)
            key = (d.source_node_id, sim_item)
            allocated_supply[key] = allocated_supply.get(key, 0.0) + d.quantity

        for (src, item), req_qty in allocated_supply.items():
            avail = initial_inventory.get(src, {}).get(item, 0.0)
            if req_qty > avail + 1e-4:
                violations.append(
                    f"Source {src} lacks sufficient {item}: planned {req_qty:.1f} > available {avail:.1f}"
                )

        # 2. Route status & capacity checks
        route_loads: Dict[str, float] = {}
        for d in decisions:
            route = routes.get(d.route_id)
            if not route:
                violations.append(f"Route {d.route_id} does not exist in network")
                continue

            r_status = getattr(route, "status", route.get("status", "AVAILABLE") if isinstance(route, dict) else "AVAILABLE")
            if r_status == RouteStatus.BLOCKED or str(r_status) == "BLOCKED":
                violations.append(f"Route {d.route_id} is BLOCKED; cannot dispatch planned shipment")

            route_loads[d.route_id] = route_loads.get(d.route_id, 0.0) + d.quantity

        for rid, load in route_loads.items():
            route = routes.get(rid)
            if route:
                max_cap = float(getattr(route, "max_capacity", route.get("max_capacity", 5000.0) if isinstance(route, dict) else 5000.0))
                if load > max_cap + 1e-4:
                    violations.append(f"Route {rid} capacity exceeded: planned load {load:.1f} > capacity {max_cap:.1f}")

        # 3. Vehicle availability & payload checks
        for d in decisions:
            veh = vehicles.get(d.vehicle_id)
            if not veh:
                violations.append(f"Vehicle {d.vehicle_id} does not exist in fleet")
                continue

            v_status = getattr(veh, "status", veh.get("status", "AVAILABLE") if isinstance(veh, dict) else "AVAILABLE")
            if str(v_status) not in ["AVAILABLE", "VehicleStatus.AVAILABLE"]:
                violations.append(f"Vehicle {d.vehicle_id} is not available (status: {v_status})")

            v_cap = float(getattr(veh, "capacity", veh.get("capacity", 500.0) if isinstance(veh, dict) else 500.0))
            if d.quantity > v_cap + 1e-4:
                violations.append(
                    f"Vehicle {d.vehicle_id} capacity exceeded: planned {d.quantity:.1f} > capacity {v_cap:.1f}"
                )

        is_feasible = (len(violations) == 0)
        return PlanValidationResult(
            is_feasible=is_feasible,
            status="PLAN_FEASIBLE" if is_feasible else "PLAN_INVALID",
            violations=violations,
        )

    @staticmethod
    def adapt_decisions(
        plan_or_result: Any,
    ) -> List[ExecutableIntervention]:
        """Extracts decision list from OptimizationResult, OptimizationPlan, or list."""
        if hasattr(plan_or_result, "decisions"):
            raw_decisions = plan_or_result.decisions
        elif isinstance(plan_or_result, list):
            raw_decisions = plan_or_result
        else:
            raw_decisions = []

        interventions: List[ExecutableIntervention] = []
        for idx, d in enumerate(raw_decisions):
            interventions.append(
                ExecutableIntervention(
                    intervention_id=getattr(d, "decision_id", f"INT_{idx+1:03d}"),
                    source_node_id=getattr(d, "source_node_id", ""),
                    destination_node_id=getattr(d, "destination_node_id", ""),
                    item=getattr(d, "item", ""),
                    quantity=float(getattr(d, "quantity", 0.0)),
                    route_id=getattr(d, "route_id", ""),
                    vehicle_id=getattr(d, "vehicle_id", ""),
                    planned_departure_hour=int(getattr(d, "dispatch_hour", 0)),
                    planned_eta_hour=int(getattr(d, "estimated_arrival_hour", 4)),
                    priority=int(getattr(d, "priority", 3)),
                    reason_codes=list(getattr(d, "reason_codes", [])),
                    rationale=str(getattr(d, "rationale", "")),
                )
            )
        return interventions
