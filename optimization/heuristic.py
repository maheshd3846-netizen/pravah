"""Deterministic Priority-Ranked Heuristic Solver for Tactical Resupply."""

from __future__ import annotations
import time
import uuid
from typing import Dict, List, Any
from optimization.model import OptimizationProblem, OptimizationPlan, SupplyDecision


class PriorityHeuristicSolver:
    """Heuristic optimization solving vehicle allocation and route detour selection."""

    def __init__(self, name: str = "PriorityGreedyHeuristic"):
        self.name = name

    def solve(self, problem: OptimizationProblem) -> OptimizationPlan:
        start_time = time.time()
        decisions: List[SupplyDecision] = []

        # Identify deficit nodes by comparing current stock against projected demand over horizon
        stock_copy: Dict[str, Dict[str, float]] = {
            nid: dict(items) for nid, items in problem.current_inventory.items()
        }

        # Calculate demand per node & item
        total_demand: Dict[tuple, float] = {}
        for d in problem.projected_demands:
            key = (d.node_id, d.item)
            total_demand[key] = total_demand.get(key, 0.0) + d.requested_demand

        # Identify deficits
        deficits: List[Dict[str, Any]] = []
        for (nid, item), dem in total_demand.items():
            curr = stock_copy.get(nid, {}).get(item, 0.0)
            if curr < dem:
                node = problem.nodes.get(nid)
                priority = getattr(node, "priority", 3) if node else 3
                deficits.append({
                    "node_id": nid,
                    "item": item,
                    "deficit": dem - curr,
                    "priority": priority,
                })

        # Sort deficits by node priority (higher priority number = more critical forward post)
        deficits.sort(key=lambda x: (x["priority"], x["deficit"]), reverse=True)

        unmet_before = sum(d["deficit"] for d in deficits)
        allocated_relief = 0.0

        # Available vehicles stationed at depot or hubs
        available_vehicles = [
            v for v in problem.vehicles.values()
            if getattr(v, "status", "AVAILABLE") == "AVAILABLE"
        ]

        # Candidate suppliers: Central Depot and Regional Hubs
        supplier_candidates = [
            nid for nid, node in problem.nodes.items()
            if getattr(node, "type", "") in ["CENTRAL_DEPOT", "REGIONAL_HUB"]
        ]

        decision_idx = 1
        for def_info in deficits:
            if not available_vehicles:
                break

            target_nid = def_info["node_id"]
            item = def_info["item"]
            needed = def_info["deficit"]

            for src_id in supplier_candidates:
                if src_id == target_nid:
                    continue

                src_avail = stock_copy.get(src_id, {}).get(item, 0.0)
                if src_avail < 50.0:
                    continue

                # Find valid unblocked route
                valid_route = None
                for rid, r in problem.routes.items():
                    if (r.source_node_id == src_id and r.destination_node_id == target_nid
                            and getattr(r, "status", "AVAILABLE") != "BLOCKED"):
                        valid_route = r
                        break

                if not valid_route:
                    # Check alternate routes or staging base links
                    for rid, r in problem.routes.items():
                        if getattr(r, "status", "AVAILABLE") != "BLOCKED":
                            if r.destination_node_id == target_nid:
                                valid_route = r
                                src_id = r.source_node_id
                                break

                if valid_route and available_vehicles:
                    veh = available_vehicles.pop(0)
                    alloc_qty = min(needed, getattr(veh, "capacity", 5000.0), src_avail * 0.75)
                    if alloc_qty < 10.0:
                        available_vehicles.append(veh)
                        continue

                    # Update stock copy
                    stock_copy[src_id][item] -= alloc_qty
                    allocated_relief += alloc_qty

                    eta = int(round(valid_route.base_travel_hours)) + 1
                    dec = SupplyDecision(
                        decision_id=f"DEC_{decision_idx:03d}",
                        source_node_id=src_id,
                        destination_node_id=target_nid,
                        item=item,
                        quantity=round(alloc_qty, 1),
                        route_id=valid_route.id,
                        vehicle_id=veh.id,
                        dispatch_hour=1,
                        estimated_arrival_hour=1 + eta,
                        rationale=f"Mitigate critical deficit of {item} at high-priority forward node {target_nid} via bypass route {valid_route.route_code}.",
                    )
                    decisions.append(dec)
                    decision_idx += 1
                    break

        unmet_after = max(0.0, unmet_before - allocated_relief)
        mitigation = round(((unmet_before - unmet_after) / max(1.0, unmet_before)) * 100.0, 1)
        exec_ms = round((time.time() - start_time) * 1000.0, 2)

        return OptimizationPlan(
            plan_id=f"PLAN_{uuid.uuid4().hex[:8]}",
            solver_name=self.name,
            decisions=decisions,
            projected_unmet_before=round(unmet_before, 1),
            projected_unmet_after=round(unmet_after, 1),
            mitigation_percentage=mitigation,
            execution_time_ms=exec_ms,
        )
