"""Deterministic Priority-Ranked Heuristic Solver for Tactical Resupply."""

from __future__ import annotations
import time
import uuid
from typing import Dict, List, Any, Tuple
import networkx as nx

from optimization.types import (
    SolverType,
    OptimizationStatus,
    MovementDecision,
    OptimizationResult,
    ReasonCode,
)
from optimization.model import OptimizationProblem, OptimizationPlan


class PriorityHeuristicSolver:
    """Greedy priority-ranked heuristic allocating inventory along safest feasible routes."""

    def __init__(self, name: str = "PriorityGreedyHeuristic"):
        self.name = name

    def solve(self, problem: OptimizationProblem) -> OptimizationResult:
        start_time = time.time()
        decisions: List[MovementDecision] = []

        # Local mutable copy of available supply at source nodes
        supply_copy: Dict[str, Dict[str, float]] = {
            nid: dict(item_map) for nid, item_map in problem.available_supply.items()
        }

        # Local mutable copy of required demand
        demand_copy: Dict[str, Dict[str, float]] = {
            nid: dict(item_map) for nid, item_map in problem.required_demand.items()
        }

        # Track remaining route capacity
        route_caps: Dict[str, float] = {}
        for rid, r in problem.routes.items():
            status = getattr(r, "status", r.get("status", "AVAILABLE") if isinstance(r, dict) else "AVAILABLE")
            cap = getattr(r, "max_capacity", r.get("max_capacity", 5000.0) if isinstance(r, dict) else 5000.0)
            if status == "BLOCKED":
                route_caps[rid] = 0.0
            elif status == "DEGRADED":
                route_caps[rid] = float(cap) * 0.60
            else:
                route_caps[rid] = float(cap)

        # Vehicle fleet state: match vehicle availability
        available_vehicles = [
            v for v in problem.vehicles.values()
            if getattr(v, "status", v.get("status", "AVAILABLE") if isinstance(v, dict) else "AVAILABLE") == "AVAILABLE"
        ]

        # Vehicle capacity map
        veh_caps: Dict[str, float] = {
            getattr(v, "id", v.get("id") if isinstance(v, dict) else ""): float(getattr(v, "capacity", v.get("capacity", 500.0) if isinstance(v, dict) else 500.0))
            for v in available_vehicles
        }
        veh_idx = 0

        # Construct deficit list: (node_id, item, deficit, priority, risk)
        deficits: List[Dict[str, Any]] = []
        for nid, item_map in demand_copy.items():
            node = problem.nodes.get(nid)
            priority = getattr(node, "priority", node.get("priority", 3) if isinstance(node, dict) else 3)
            node_risk = problem.node_risks.get(nid, 0.0)

            for item, req_dem in item_map.items():
                if req_dem > 0:
                    deficits.append({
                        "node_id": nid,
                        "item": item,
                        "deficit": req_dem,
                        "priority": priority,
                        "node_risk": node_risk,
                    })

        # Rank deficits: Highest priority nodes first (priority 5 -> priority 1), then higher deficit
        deficits.sort(key=lambda x: (x["priority"], x["node_risk"], x["deficit"]), reverse=True)

        total_shortage_before = sum(d["deficit"] for d in deficits)

        # Build route graph for shortest/safest path lookup
        graph = nx.DiGraph()
        for r_id, r in problem.routes.items():
            status = getattr(r, "status", r.get("status", "AVAILABLE") if isinstance(r, dict) else "AVAILABLE")
            if status == "BLOCKED":
                continue

            src = getattr(r, "source_node_id", r.get("source_node_id") if isinstance(r, dict) else None)
            dst = getattr(r, "destination_node_id", r.get("destination_node_id") if isinstance(r, dict) else None)
            dist = getattr(r, "distance_km", r.get("distance_km", 50.0) if isinstance(r, dict) else 50.0)
            r_risk = problem.route_risks.get(r_id, 0.1)

            # Combined cost weight: distance + risk penalty
            weight = dist * (1.0 + r_risk * 5.0)
            if status == "DEGRADED":
                weight *= 1.5

            if src and dst and route_caps.get(r_id, 0.0) > 0:
                graph.add_edge(src, dst, route_id=r_id, weight=weight)

        # Identify suppliers: Central Depot and Regional Hubs
        supplier_nodes = [
            nid for nid, node in problem.nodes.items()
            if getattr(node, "type", node.get("type", "") if isinstance(node, dict) else "") in ["CENTRAL_DEPOT", "REGIONAL_HUB"]
        ]

        # Allocate supply greedily
        for def_info in deficits:
            target_nid = def_info["node_id"]
            item = def_info["item"]
            needed = def_info["deficit"]

            if needed <= 0.0:
                continue

            # Find closest/safest supplier with available stock
            best_supplier = None
            best_path = None
            best_cost = float("inf")

            for sup_id in supplier_nodes:
                avail = supply_copy.get(sup_id, {}).get(item, 0.0)
                if avail <= 0:
                    continue

                if nx.has_path(graph, sup_id, target_nid):
                    try:
                        cost = nx.shortest_path_length(graph, sup_id, target_nid, weight="weight")
                        if cost < best_cost:
                            best_cost = cost
                            best_supplier = sup_id
                            best_path = nx.shortest_path(graph, sup_id, target_nid, weight="weight")
                    except nx.NetworkXNoPath:
                        continue

            if not best_supplier or not best_path:
                continue

            # Identify routes along path
            # For direct or multi-hop movement, allocate on first leg or direct route
            if len(best_path) >= 2:
                hop_src = best_path[0]
                hop_dst = best_path[1]
                chosen_route_id = graph[hop_src][hop_dst]["route_id"]

                avail_qty = supply_copy[best_supplier][item]
                route_cap = route_caps.get(chosen_route_id, 0.0)

                # Select vehicle
                if not available_vehicles:
                    continue

                veh = available_vehicles[veh_idx % len(available_vehicles)]
                veh_id = getattr(veh, "id", veh.get("id") if isinstance(veh, dict) else f"V_{veh_idx}")
                veh_cap = veh_caps.get(veh_id, 500.0)

                # Allocatable quantity bounded by demand, supply, route cap, vehicle cap
                alloc_qty = min(needed, avail_qty, route_cap, veh_cap)

                if alloc_qty > 0.1:
                    supply_copy[best_supplier][item] -= alloc_qty
                    route_caps[chosen_route_id] -= alloc_qty
                    demand_copy[target_nid][item] -= alloc_qty
                    def_info["deficit"] -= alloc_qty

                    # Generate reason codes
                    reasons = [ReasonCode.HIGH_PRIORITY_NODE.value]
                    if def_info["node_risk"] > 0.5:
                        reasons.append(ReasonCode.STOCKOUT_RISK.value)

                    route_obj = problem.routes.get(chosen_route_id)
                    r_status = getattr(route_obj, "status", "AVAILABLE")
                    if r_status == "DEGRADED":
                        reasons.append(ReasonCode.LOWER_RISK_DETOUR.value)

                    # Compute realistic arrival from route travel time
                    r_obj = problem.routes.get(chosen_route_id)
                    travel_h = getattr(r_obj, "base_travel_hours", 4.0) if r_obj else 4.0
                    est_arrival = max(1, int(round(travel_h)))

                    decisions.append(
                        MovementDecision(
                            decision_id=f"DEC_HEUR_{len(decisions)+1:03d}",
                            source_node_id=best_supplier,
                            destination_node_id=target_nid,
                            item=item,
                            quantity=round(alloc_qty, 1),
                            route_id=chosen_route_id,
                            vehicle_id=veh_id,
                            dispatch_hour=0,
                            estimated_arrival_hour=est_arrival,
                            priority=def_info["priority"],
                            reason_codes=reasons,
                            rationale=f"Heuristic allocation to relieve {alloc_qty:.1f} units shortage at {target_nid}.",
                        )
                    )
                    veh_idx += 1

        exec_time_ms = (time.time() - start_time) * 1000.0
        remaining_shortage = sum(
            max(0.0, qty) for n_map in demand_copy.values() for qty in n_map.values()
        )

        # Vehicle and route utilization
        route_util = {}
        for r_id, r in problem.routes.items():
            orig_cap = getattr(r, "max_capacity", 5000.0)
            rem = route_caps.get(r_id, orig_cap)
            route_util[r_id] = max(0.0, (orig_cap - rem) / max(1.0, orig_cap))

        result = OptimizationResult(
            run_id=f"RUN_{uuid.uuid4().hex[:8].upper()}",
            status=OptimizationStatus.FEASIBLE if decisions else OptimizationStatus.INFEASIBLE,
            solver_type=SolverType.HEURISTIC,
            objective_value=round(remaining_shortage * problem.objective_weights.shortage_weight, 2),
            execution_time_ms=round(exec_time_ms, 2),
            demand_policy=problem.demand_policy,
            total_transport_cost=round(len(decisions) * 25.0, 2),
            total_shortage=round(remaining_shortage, 2),
            total_delay=0.0,
            total_risk_cost=0.0,
            route_utilization=route_util,
            decisions=decisions,
            metadata={"problem_id": problem.problem_id},
        )
        return result
