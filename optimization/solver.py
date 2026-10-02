"""Linear and Mixed-Integer Solver Adapters using SciPy HiGHS."""

from __future__ import annotations
import time
import uuid
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from scipy.optimize import linprog

from optimization.types import (
    DemandPolicy,
    SolverType,
    OptimizationStatus,
    MovementDecision,
    OptimizationResult,
    ReasonCode,
)
from optimization.model import OptimizationProblem, OptimizationPlan
from optimization.variables import VariableRegistry
from optimization.objective import ObjectiveBuilder
from optimization.constraints import ConstraintBuilder, validate_constraints
from optimization.heuristic import PriorityHeuristicSolver


class SolverAdapter:
    """Base interface for mathematical solvers."""

    def solve(self, problem: OptimizationProblem) -> OptimizationResult:
        raise NotImplementedError


class MilpSolver(SolverAdapter):
    """High-performance Linear / MILP solver utilizing SciPy HiGHS engine."""

    def __init__(self, allow_fallback: bool = True):
        self.allow_fallback = allow_fallback
        self.heuristic_solver = PriorityHeuristicSolver()

    def solve(self, problem: OptimizationProblem) -> OptimizationResult:
        start_time = time.time()
        registry = VariableRegistry()

        # Group available vehicles by source node or global fleet
        available_vehicles = [
            v for v in problem.vehicles.values()
            if getattr(v, "status", v.get("status", "AVAILABLE") if isinstance(v, dict) else "AVAILABLE") == "AVAILABLE"
        ]
        veh_caps = {
            getattr(v, "id", v.get("id") if isinstance(v, dict) else ""): float(getattr(v, "capacity", v.get("capacity", 500.0) if isinstance(v, dict) else 500.0))
            for v in available_vehicles
        }
        max_single_veh_cap = max(veh_caps.values()) if veh_caps else 500.0

        # 1. Register decision variables
        # Flow variables x[i, j, r, k] for usable routes
        for r_id, r in problem.routes.items():
            src = getattr(r, "source_node_id", r.get("source_node_id") if isinstance(r, dict) else None)
            dst = getattr(r, "destination_node_id", r.get("destination_node_id") if isinstance(r, dict) else None)
            status = getattr(r, "status", r.get("status", "AVAILABLE") if isinstance(r, dict) else "AVAILABLE")
            cap = getattr(r, "max_capacity", r.get("max_capacity", 5000.0) if isinstance(r, dict) else 5000.0)

            # Blocked routes are assigned 0 upper bound
            effective_cap = 0.0 if status == "BLOCKED" else float(cap)

            if src and dst:
                for item in problem.items:
                    # Upper bound bounded by available supply at source and route capacity
                    src_supply = problem.available_supply.get(src, {}).get(item, 0.0)
                    ub = min(src_supply, effective_cap)
                    registry.add_flow_variable(
                        source_id=src,
                        destination_id=dst,
                        route_id=r_id,
                        item=item,
                        upper_bound=ub,
                    )

        # Shortage variables u[j, k]
        for dst_id, item_map in problem.required_demand.items():
            for item, req_dem in item_map.items():
                registry.add_shortage_variable(
                    node_id=dst_id,
                    item=item,
                    required_demand=req_dem,
                )

        if registry.total_variables == 0:
            exec_time_ms = (time.time() - start_time) * 1000.0
            return OptimizationResult(
                run_id=f"RUN_{uuid.uuid4().hex[:8].upper()}",
                status=OptimizationStatus.INFEASIBLE,
                solver_type=SolverType.MILP,
                objective_value=0.0,
                execution_time_ms=round(exec_time_ms, 2),
                demand_policy=problem.demand_policy,
                total_transport_cost=0.0,
                total_shortage=0.0,
                total_delay=0.0,
                total_risk_cost=0.0,
                infeasibility_reasons=["No feasible variables could be registered from network topology."],
            )

        # 2. Build cost vector c
        obj_builder = ObjectiveBuilder(problem.objective_weights)
        c = obj_builder.build_cost_vector(problem, registry)

        # 3. Build linear constraints A_ub * z <= b_ub
        A_ub, b_ub = ConstraintBuilder.build_constraints(problem, registry)

        bounds = list(zip(registry.lower_bounds, registry.upper_bounds))

        # 4. Invoke SciPy HiGHS solver
        try:
            res = linprog(
                c=c,
                A_ub=A_ub if len(A_ub) > 0 else None,
                b_ub=b_ub if len(b_ub) > 0 else None,
                bounds=bounds,
                method="highs",
            )
            success = res.success
            status_str = res.status
        except Exception as e:
            success = False
            status_str = str(e)

        exec_time_ms = (time.time() - start_time) * 1000.0

        if not success or res.x is None:
            # Check for infeasibility or error
            opt_status = OptimizationStatus.INFEASIBLE if "infeasible" in str(status_str).lower() else OptimizationStatus.ERROR
            if self.allow_fallback:
                fallback_res = self.heuristic_solver.solve(problem)
                fallback_res.metadata["fallback_used"] = True
                fallback_res.metadata["milp_failure_status"] = str(status_str)
                return fallback_res

            return OptimizationResult(
                run_id=f"RUN_{uuid.uuid4().hex[:8].upper()}",
                status=opt_status,
                solver_type=SolverType.MILP,
                objective_value=float("inf"),
                execution_time_ms=round(exec_time_ms, 2),
                demand_policy=problem.demand_policy,
                total_transport_cost=0.0,
                total_shortage=0.0,
                total_delay=0.0,
                total_risk_cost=0.0,
                infeasibility_reasons=[f"Solver reported failure: {status_str}"],
            )

        # 5. Extract solution and parse decisions
        sol_vec = res.x
        breakdown = obj_builder.compute_breakdown(problem, registry, sol_vec)

        decisions: List[MovementDecision] = []
        route_loads: Dict[str, float] = {}
        veh_idx = 0

        for (src_id, dst_id, route_id, item), flow_entry in registry.flow_vars.items():
            qty = float(sol_vec[flow_entry.var_index])
            if qty > 1e-3:
                route_loads[route_id] = route_loads.get(route_id, 0.0) + qty

                # Vehicle assignment
                if available_vehicles:
                    veh = available_vehicles[veh_idx % len(available_vehicles)]
                    veh_id = getattr(veh, "id", veh.get("id") if isinstance(veh, dict) else f"V_{veh_idx}")
                    veh_cap = veh_caps.get(veh_id, max_single_veh_cap)
                    veh_idx += 1
                else:
                    veh_id = "V_DEFAULT"
                    veh_cap = max_single_veh_cap

                # Split across multiple dispatches if quantity exceeds single vehicle capacity
                remaining_to_dispatch = qty
                while remaining_to_dispatch > 1e-3:
                    batch_qty = min(remaining_to_dispatch, veh_cap)

                    # Reason codes
                    reasons = [ReasonCode.HIGH_PRIORITY_NODE.value]
                    route_obj = problem.routes.get(route_id)
                    r_risk = problem.route_risks.get(route_id, 0.0)
                    r_status = getattr(route_obj, "status", "AVAILABLE")

                    if r_status == "DEGRADED":
                        reasons.append(ReasonCode.LOWER_RISK_DETOUR.value)
                    if problem.node_risks.get(dst_id, 0.0) > 0.4:
                        reasons.append(ReasonCode.STOCKOUT_RISK.value)

                    decisions.append(
                        MovementDecision(
                            decision_id=f"DEC_OPT_{len(decisions)+1:03d}",
                            source_node_id=src_id,
                            destination_node_id=dst_id,
                            item=item,
                            quantity=round(batch_qty, 1),
                            route_id=route_id,
                            vehicle_id=veh_id,
                            dispatch_hour=0,
                            estimated_arrival_hour=4,
                            priority=getattr(problem.nodes.get(dst_id), "priority", 3),
                            reason_codes=reasons,
                            rationale=f"Optimal multi-commodity allocation satisfying {batch_qty:.1f} units {item} to {dst_id}.",
                        )
                    )
                    remaining_to_dispatch -= batch_qty

        # Route utilization
        route_util = {}
        for r_id, r in problem.routes.items():
            max_cap = getattr(r, "max_capacity", 5000.0)
            load = route_loads.get(r_id, 0.0)
            route_util[r_id] = round(min(1.0, load / max(1.0, float(max_cap))), 3)

        return OptimizationResult(
            run_id=f"RUN_{uuid.uuid4().hex[:8].upper()}",
            status=OptimizationStatus.OPTIMAL,
            solver_type=SolverType.MILP,
            objective_value=breakdown["objective_value"],
            execution_time_ms=round(exec_time_ms, 2),
            demand_policy=problem.demand_policy,
            total_transport_cost=breakdown["transport_cost"],
            total_shortage=breakdown["total_shortage"],
            total_delay=breakdown["delay_cost"],
            total_risk_cost=breakdown["risk_cost"],
            route_utilization=route_util,
            decisions=decisions,
            metadata={
                "problem_id": problem.problem_id,
                "solver_method": "scipy-highs",
                "solver_classification": "HYBRID_LP_FLOW_HEURISTIC_DISPATCH",
                "is_pure_milp": False,
                "iterations": getattr(res, "nit", 0),
            },
        )


class LogisticsSolver:
    """Unified entry point providing MILP or Heuristic optimization."""

    def __init__(self, solver_type: SolverType = SolverType.MILP):
        self.solver_type = solver_type
        self.milp_solver = MilpSolver(allow_fallback=True)
        self.heuristic_solver = PriorityHeuristicSolver()

    def solve(self, problem: OptimizationProblem) -> OptimizationResult:
        if self.solver_type == SolverType.HEURISTIC:
            return self.heuristic_solver.solve(problem)
        return self.milp_solver.solve(problem)

    def solve_plan(self, problem: OptimizationProblem) -> OptimizationPlan:
        """Backwards-compatible method returning OptimizationPlan."""
        res = self.solve(problem)
        initial_shortage = sum(
            qty for item_map in problem.required_demand.values() for qty in item_map.values()
        )
        return OptimizationPlan(
            plan_id=res.run_id,
            solver_name=res.solver_type.value,
            decisions=res.decisions,
            projected_unmet_before=initial_shortage,
            projected_unmet_after=res.total_shortage,
            mitigation_percentage=round(
                max(0.0, (initial_shortage - res.total_shortage) / max(1.0, initial_shortage)) * 100.0, 1
            ),
            execution_time_ms=res.execution_time_ms,
            result=res,
        )
