"""Constraint Generation and Mathematical Feasibility Validation."""

from __future__ import annotations
from typing import Dict, List, Tuple, Any, Optional
import numpy as np

from optimization.types import MovementDecision
from optimization.model import OptimizationProblem
from optimization.variables import VariableRegistry


class ConstraintBuilder:
    """Builds matrix linear constraints for scipy.optimize (A_ub, b_ub, A_eq, b_eq)."""

    @staticmethod
    def build_constraints(
        problem: OptimizationProblem,
        registry: VariableRegistry,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Constructs inequality constraints A_ub * z <= b_ub."""
        n_vars = registry.total_variables
        row_list: List[np.ndarray] = []
        b_list: List[float] = []

        # ----------------------------------------------------------------------
        # 1. Supply Constraints: sum_{(j,r)} x[i, j, r, k] <= AvailableSupply[i, k]
        # ----------------------------------------------------------------------
        for src_id, item_map in problem.available_supply.items():
            for item, avail_qty in item_map.items():
                row = np.zeros(n_vars, dtype=np.float64)
                has_outflow = False

                for (s, d, r, it), flow_entry in registry.flow_vars.items():
                    if s == src_id and it == item:
                        row[flow_entry.var_index] = 1.0
                        has_outflow = True

                if has_outflow:
                    row_list.append(row)
                    b_list.append(float(avail_qty))

        # ----------------------------------------------------------------------
        # 2. Destination Demand Satisfaction: sum_{(i,r)} x[i, j, r, k] + u[j, k] >= ReqDemand[j, k]
        #    Rewritten in standard <= form: -sum x - u <= -ReqDemand
        # ----------------------------------------------------------------------
        for dst_id, item_map in problem.required_demand.items():
            for item, req_qty in item_map.items():
                if req_qty <= 0.0:
                    continue

                row = np.zeros(n_vars, dtype=np.float64)

                # Inflow flows to dst_id
                for (s, d, r, it), flow_entry in registry.flow_vars.items():
                    if d == dst_id and it == item:
                        row[flow_entry.var_index] = -1.0

                # Shortage variable u[dst_id, item]
                if (dst_id, item) in registry.shortage_vars:
                    u_idx = registry.shortage_vars[(dst_id, item)].var_index
                    row[u_idx] = -1.0

                row_list.append(row)
                b_list.append(-float(req_qty))

        # ----------------------------------------------------------------------
        # 3. Route Capacity Constraints: sum_k x[i, j, r, k] <= RouteCapacity[r]
        # ----------------------------------------------------------------------
        # Group flow variables by route_id
        route_to_flows: Dict[str, List[int]] = {}
        for (s, d, r, it), flow_entry in registry.flow_vars.items():
            route_to_flows.setdefault(r, []).append(flow_entry.var_index)

        for route_id, flow_indices in route_to_flows.items():
            route = problem.routes.get(route_id)
            status = getattr(route, "status", route.get("status", "AVAILABLE") if isinstance(route, dict) else "AVAILABLE")
            max_cap = getattr(route, "max_capacity", route.get("max_capacity", 5000.0) if isinstance(route, dict) else 5000.0)

            # Blocked route has 0 capacity
            if status == "BLOCKED":
                effective_cap = 0.0
            elif status == "DEGRADED":
                effective_cap = float(max_cap) * 0.60
            else:
                effective_cap = float(max_cap)

            row = np.zeros(n_vars, dtype=np.float64)
            for var_idx in flow_indices:
                row[var_idx] = 1.0

            row_list.append(row)
            b_list.append(effective_cap)

        if not row_list:
            return np.zeros((0, n_vars)), np.zeros(0)

        A_ub = np.array(row_list, dtype=np.float64)
        b_ub = np.array(b_list, dtype=np.float64)
        return A_ub, b_ub


def validate_constraints(
    decisions: List[MovementDecision],
    source_inventories: Dict[str, Dict[str, float]],
    vehicle_capacities: Dict[str, float],
    route_statuses: Dict[str, str],
    route_capacities: Optional[Dict[str, float]] = None,
) -> Tuple[bool, List[str]]:
    """Validates that proposed decisions satisfy physical supply and routing constraints."""
    violations: List[str] = []

    # 1. Source supply depletion checks
    consumed: Dict[Tuple[str, str], float] = {}
    for d in decisions:
        consumed[(d.source_node_id, d.item)] = consumed.get((d.source_node_id, d.item), 0.0) + d.quantity

    for (src, item), qty in consumed.items():
        avail = source_inventories.get(src, {}).get(item, 0.0)
        if qty > avail + 1e-4:
            violations.append(f"Source {src} lacks sufficient {item}: required {qty:.1f}, available {avail:.1f}")

    # 2. Vehicle capacity checks
    for d in decisions:
        max_cap = vehicle_capacities.get(d.vehicle_id, float("inf"))
        if d.quantity > max_cap + 1e-4:
            violations.append(f"Vehicle {d.vehicle_id} capacity exceeded: load {d.quantity:.1f} > max {max_cap:.1f}")

    # 3. Route accessibility checks (blocked routes cannot be dispatched on)
    for d in decisions:
        status = route_statuses.get(d.route_id, "AVAILABLE")
        if status == "BLOCKED":
            violations.append(f"Proposed route {d.route_id} is BLOCKED; cannot dispatch")

    # 4. Route capacity checks
    if route_capacities:
        route_loads: Dict[str, float] = {}
        for d in decisions:
            route_loads[d.route_id] = route_loads.get(d.route_id, 0.0) + d.quantity

        for r_id, total_load in route_loads.items():
            cap = route_capacities.get(r_id, float("inf"))
            if total_load > cap + 1e-4:
                violations.append(f"Route {r_id} capacity exceeded: load {total_load:.1f} > capacity {cap:.1f}")

    return (len(violations) == 0, violations)
