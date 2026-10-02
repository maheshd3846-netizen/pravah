"""Multi-Objective Cost Formulation for Tactical Supply Chain Allocation."""

from __future__ import annotations
from typing import Dict, Any, List, Tuple
import numpy as np

from optimization.types import ObjectiveWeights
from optimization.model import OptimizationProblem
from optimization.variables import VariableRegistry


class ObjectiveBuilder:
    """Constructs transparent, multi-criteria cost vectors for LP/MILP solvers."""

    def __init__(self, weights: ObjectiveWeights):
        self.weights = weights

    def build_cost_vector(
        self,
        problem: OptimizationProblem,
        registry: VariableRegistry,
    ) -> np.ndarray:
        """Constructs 1D cost coefficient vector c where min Z = c^T x."""
        n_vars = registry.total_variables
        c = np.zeros(n_vars, dtype=np.float64)

        # 1. Flow variables: x[i, j, r, k]
        for (src_id, dst_id, route_id, item), flow_entry in registry.flow_vars.items():
            route = problem.routes.get(route_id)
            distance = getattr(route, "distance_km", route.get("distance_km", 50.0) if isinstance(route, dict) else 50.0)
            base_hours = getattr(route, "base_travel_hours", route.get("base_travel_hours", 2.0) if isinstance(route, dict) else 2.0)
            eff_hours = getattr(route, "effective_travel_hours", route.get("effective_travel_hours", base_hours) if isinstance(route, dict) else base_hours)
            delay_hours = max(0.0, eff_hours - base_hours)

            # Route risk score
            route_risk = problem.route_risks.get(route_id, 0.1)

            # Route status penalty if DEGRADED
            status = getattr(route, "status", route.get("status", "AVAILABLE") if isinstance(route, dict) else "AVAILABLE")
            degraded_penalty = 15.0 if status == "DEGRADED" else 0.0

            # Component cost per unit
            transport_cost = self.weights.transport_weight * (distance / 50.0)
            delay_cost = self.weights.delay_weight * delay_hours
            risk_cost = self.weights.risk_weight * (route_risk * 10.0 + degraded_penalty)

            effective_unit_cost = transport_cost + delay_cost + risk_cost
            c[flow_entry.var_index] = effective_unit_cost

        # 2. Shortage variables: u[j, k]
        for (node_id, item), shortage_entry in registry.shortage_vars.items():
            node = problem.nodes.get(node_id)
            priority = getattr(node, "priority", node.get("priority", 3) if isinstance(node, dict) else 3)
            node_risk = problem.node_risks.get(node_id, 0.2)

            # Priority scaling: Higher priority (5: Forward Post) gets much heavier shortage penalty
            # Base penalty multiplied by priority multiplier (1.0 to 3.0)
            priority_factor = 1.0 + (priority - 1.0) * 0.5
            risk_amplifier = 1.0 + node_risk

            shortage_unit_cost = (
                self.weights.shortage_weight
                * priority_factor
                * risk_amplifier
            )
            c[shortage_entry.var_index] = shortage_unit_cost

        # 3. Vehicle assignment variables (if any)
        for (v_id, r_id), v_entry in registry.vehicle_vars.items():
            # Small fixed dispatch cost to discourage deploying extra unnecessary vehicles
            c[v_entry.var_index] = 1.0

        return c

    def compute_breakdown(
        self,
        problem: OptimizationProblem,
        registry: VariableRegistry,
        sol_vec: np.ndarray,
    ) -> Dict[str, float]:
        """Calculates explicit cost component values from the solved variable vector."""
        transport_total = 0.0
        delay_total = 0.0
        risk_total = 0.0
        shortage_total = 0.0

        # Flow variables
        for (src_id, dst_id, route_id, item), flow_entry in registry.flow_vars.items():
            qty = sol_vec[flow_entry.var_index]
            if qty <= 1e-4:
                continue

            route = problem.routes.get(route_id)
            distance = getattr(route, "distance_km", route.get("distance_km", 50.0) if isinstance(route, dict) else 50.0)
            base_hours = getattr(route, "base_travel_hours", route.get("base_travel_hours", 2.0) if isinstance(route, dict) else 2.0)
            eff_hours = getattr(route, "effective_travel_hours", route.get("effective_travel_hours", base_hours) if isinstance(route, dict) else base_hours)
            delay_hours = max(0.0, eff_hours - base_hours)
            route_risk = problem.route_risks.get(route_id, 0.1)

            transport_total += qty * (distance / 50.0) * self.weights.transport_weight
            delay_total += qty * delay_hours * self.weights.delay_weight
            risk_total += qty * (route_risk * 10.0) * self.weights.risk_weight

        # Shortage variables
        for (node_id, item), shortage_entry in registry.shortage_vars.items():
            shortage_qty = sol_vec[shortage_entry.var_index]
            shortage_total += shortage_qty

        total_obj = (
            transport_total
            + delay_total
            + risk_total
            + (shortage_total * self.weights.shortage_weight)
        )

        return {
            "transport_cost": round(transport_total, 2),
            "delay_cost": round(delay_total, 2),
            "risk_cost": round(risk_total, 2),
            "total_shortage": round(shortage_total, 2),
            "objective_value": round(total_obj, 2),
        }
