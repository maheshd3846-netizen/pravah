"""Adapter Translating Phase 1/2 World State and Intelligence into Optimization Problems."""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from optimization.types import DemandPolicy, ObjectiveWeights
from optimization.model import OptimizationProblem


class OptimizationInputAdapter:
    """Extracts, formats, and validates inputs from Simulation and Intelligence layers."""

    @staticmethod
    def create_problem(
        world: Any,
        demand_forecasts: Optional[Dict[str, Dict[str, Dict[str, float]]]] = None,
        risk_assessments: Optional[Dict[str, Any]] = None,
        demand_policy: DemandPolicy = DemandPolicy.P80,
        objective_weights: Optional[ObjectiveWeights] = None,
        horizon_hours: int = 72,
        scenario_id: str = "DEFAULT",
        forecast_version: str = "xgb-demand-v1",
        feature_version: str = "demand-features-v1",
    ) -> OptimizationProblem:
        """Constructs an auditable OptimizationProblem instance."""
        weights = objective_weights or ObjectiveWeights()
        problem_id = f"OPT_PROB_{uuid.uuid4().hex[:8].upper()}"

        nodes = world.nodes if hasattr(world, "nodes") else world.get("nodes", {})
        routes = world.routes if hasattr(world, "routes") else world.get("routes", {})
        vehicles = world.vehicles if hasattr(world, "vehicles") else world.get("vehicles", {})

        # Identify items
        items = ["FUEL", "RATIONS", "AMMUNITION", "MEDICAL", "WATER"]

        # 1. Available Supply at source depots/hubs
        available_supply: Dict[str, Dict[str, float]] = {}
        for nid, n in nodes.items():
            init_inv = getattr(n, "current_inventory", getattr(n, "initial_inventory", {}))
            available_supply[nid] = {}
            for item in items:
                available_supply[nid][item] = float(init_inv.get(item, 1000.0 if getattr(n, "type", "") in ["CENTRAL_DEPOT", "REGIONAL_HUB"] else 200.0))

        # 2. Required Demand based on chosen demand policy
        required_demand: Dict[str, Dict[str, float]] = {}
        for nid, n in nodes.items():
            required_demand[nid] = {}
            for item in items:
                # If forecasts provided, extract policy quantile (P50, P80, P95)
                if demand_forecasts and nid in demand_forecasts and item in demand_forecasts[nid]:
                    fc_vals = demand_forecasts[nid][item]
                    if demand_policy == DemandPolicy.P50:
                        val = fc_vals.get("p50", 15.0)
                    elif demand_policy == DemandPolicy.P95:
                        val = fc_vals.get("p95", 45.0)
                    else:  # P80 default
                        val = fc_vals.get("p80", 25.0)
                    required_demand[nid][item] = float(val)
                else:
                    # Realistic synthetic demand baseline for forward defense posts
                    ntype = getattr(n, "type", "")
                    base_rate = 25.0 if ntype == "FORWARD_POST" else (10.0 if ntype == "TRANSIT_POINT" else 0.0)
                    mult = 1.0 if demand_policy == DemandPolicy.P50 else (1.4 if demand_policy == DemandPolicy.P80 else 2.0)
                    required_demand[nid][item] = round(base_rate * mult, 1)

        # 3. Node and Route risks
        node_risks: Dict[str, float] = {}
        if risk_assessments and hasattr(risk_assessments, "items"):
            for nid, assessment in risk_assessments.items():
                node_risks[nid] = float(getattr(assessment, "overall_risk", assessment.get("overall_risk", 0.2) if isinstance(assessment, dict) else 0.2))
        else:
            for nid in nodes:
                node_risks[nid] = 0.2

        route_risks: Dict[str, float] = {}
        for rid, r in routes.items():
            status = getattr(r, "status", r.get("status", "AVAILABLE") if isinstance(r, dict) else "AVAILABLE")
            if status == "BLOCKED":
                route_risks[rid] = 1.0
            elif status == "DEGRADED":
                route_risks[rid] = 0.65
            else:
                rel = getattr(r, "reliability", 0.90)
                route_risks[rid] = round(1.0 - rel, 2)

        return OptimizationProblem(
            problem_id=problem_id,
            nodes=nodes,
            routes=routes,
            vehicles=vehicles,
            items=items,
            available_supply=available_supply,
            required_demand=required_demand,
            node_risks=node_risks,
            route_risks=route_risks,
            demand_policy=demand_policy,
            objective_weights=weights,
            horizon_hours=horizon_hours,
            metadata={
                "scenario_id": scenario_id,
                "demand_policy": demand_policy.value,
                "forecast_version": forecast_version,
                "feature_version": feature_version,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )
