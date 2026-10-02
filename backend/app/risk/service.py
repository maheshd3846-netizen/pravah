"""Comprehensive Risk Intelligence Service for PRAVAH.

Coordinates multidimensional risk evaluation, network risk propagation,
node criticality analysis, and early warning alert generation.
"""

from __future__ import annotations
from typing import Dict, List, Any, Optional
from simulation.world_generator import WorldGenerator, WorldState, RouteStatus
from backend.app.risk.evaluator import RiskEvaluator, RiskWeightsConfig, NodeRiskAssessment
from backend.app.risk.propagation import NetworkRiskPropagator, PropagationConfig
from backend.app.risk.criticality import NodeCriticalityCalculator, CriticalityWeightsConfig
from backend.app.risk.alerts import EarlyWarningEngine, Alert


class RiskIntelligenceService:
    """Central risk intelligence service for real-time vulnerability tracking."""

    def __init__(
        self,
        risk_evaluator: Optional[RiskEvaluator] = None,
        propagator: Optional[NetworkRiskPropagator] = None,
        criticality_calc: Optional[NodeCriticalityCalculator] = None,
        alert_engine: Optional[EarlyWarningEngine] = None,
    ):
        self.risk_evaluator = risk_evaluator or RiskEvaluator()
        self.propagator = propagator or NetworkRiskPropagator()
        self.criticality_calc = criticality_calc or NodeCriticalityCalculator()
        self.alert_engine = alert_engine or EarlyWarningEngine()

        self._cached_assessments: Dict[str, NodeRiskAssessment] = {}
        self._cached_criticalities: Dict[str, Dict[str, Any]] = {}
        self._cached_propagated: Dict[str, Dict[str, Any]] = {}
        self._cached_alerts: List[Alert] = []

    def evaluate_world_risk(
        self,
        world: WorldState,
        inventory_projections: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Performs full risk analysis: components, propagation, criticality, and alerts."""
        node_risks: Dict[str, float] = {}
        assessments: Dict[str, NodeRiskAssessment] = {}
        criticalities: Dict[str, Dict[str, Any]] = {}
        all_alerts: List[Alert] = []

        # Find max demand in network for scaling
        max_daily_burn = 5000.0

        for nid, node in world.nodes.items():
            # 1. Inventory risk indicators
            proj = (inventory_projections or {}).get(nid, {})
            stockout_prob = proj.get("stockout_probability", 0.05)
            time_to_zero = proj.get("time_to_zero_hours")
            time_to_ss = proj.get("time_to_safety_stock_hours")

            # Check fuel/food inventory buffer
            fuel_stock = node.initial_inventory.get("FUEL", 1000.0)
            fuel_ss = node.reorder_point.get("FUEL", 500.0)

            inv_risk = self.risk_evaluator.evaluate_inventory_risk(
                stockout_probability=stockout_prob,
                time_to_zero_hours=time_to_zero,
                time_to_safety_stock_hours=time_to_ss,
                current_inventory=fuel_stock,
                safety_stock=fuel_ss,
            )

            # 2. Demand risk indicators
            demand_risk = self.risk_evaluator.evaluate_demand_risk(
                demand_growth_ratio=proj.get("demand_growth_ratio", 1.0),
                demand_volatility_cv=proj.get("demand_volatility_cv", 0.12),
                forecast_spread_ratio=proj.get("forecast_spread_ratio", 0.20),
            )

            # 3. Route risk indicators
            inflow_routes = [r for r in world.routes.values() if r.destination_node_id == nid]
            inflow_statuses = [r.status.value for r in inflow_routes]
            reliabilities = [r.reliability_score for r in inflow_routes]
            mean_rel = float(sum(reliabilities) / max(1, len(reliabilities))) if reliabilities else 0.85
            alt_count = max(0, len(inflow_routes) - 1)

            route_risk = self.risk_evaluator.evaluate_route_risk(
                inflow_routes_status=inflow_statuses,
                alternate_routes_count=alt_count,
                mean_route_reliability=mean_rel,
            )

            # 4. Transport risk indicators
            avail_veh = [v for v in world.vehicles.values() if v.status.value == "AVAILABLE"]
            fleet_ratio = len(avail_veh) / max(1, len(world.vehicles))
            trans_risk = self.risk_evaluator.evaluate_transport_risk(
                vehicle_availability_ratio=fleet_ratio,
                active_delays_count=0,
            )

            # 5. Environment risk indicators
            w_state = world.weather_by_node.get(nid)
            w_sev = w_state.severity.value if w_state else "NORMAL"
            w_wind = w_state.wind_speed if w_state else 15.0
            w_vis = w_state.visibility if w_state else 10.0
            w_temp = w_state.temperature if w_state else 0.0

            env_risk = self.risk_evaluator.evaluate_environment_risk(
                weather_severity=w_sev,
                wind_speed=w_wind,
                visibility=w_vis,
                temperature=w_temp,
            )

            # Composite overall risk
            assessment = self.risk_evaluator.calculate_overall_risk(
                node_id=nid,
                node_code=node.code,
                inventory_risk=inv_risk,
                demand_risk=demand_risk,
                route_risk=route_risk,
                transport_risk=trans_risk,
                environment_risk=env_risk,
                raw_indicators={
                    "stockout_probability": stockout_prob,
                    "inflow_routes_count": len(inflow_routes),
                    "blocked_inflows": sum(1 for s in inflow_statuses if s == "BLOCKED"),
                    "weather_severity": w_sev,
                },
            )
            assessments[nid] = assessment
            node_risks[nid] = assessment.overall_risk

            # Strategic Criticality Score
            outflow_routes = [r for r in world.routes.values() if r.source_node_id == nid]
            daily_burn = sum(node.reorder_point.values()) / max(1, node.safety_stock_days)
            crit_data = self.criticality_calc.calculate_node_criticality(
                node_priority=node.priority,
                daily_demand_volume=daily_burn,
                inflow_routes_count=len(inflow_routes),
                outflow_routes_count=len(outflow_routes),
                elevation_meters=node.elevation,
                max_demand_in_network=max_daily_burn,
            )
            criticalities[nid] = crit_data

            # Early Warning Alerts for Node
            for item in ["FUEL", "FOOD"]:
                stock = node.initial_inventory.get(item, 1000.0)
                ss = node.reorder_point.get(item, 500.0)
                item_alerts = self.alert_engine.evaluate_inventory_alerts(
                    node_id=nid,
                    node_code=node.code,
                    item=item,
                    current_inventory=stock,
                    safety_stock=ss,
                    time_to_ss_hours=time_to_ss,
                    time_to_zero_hours=time_to_zero,
                    stockout_prob=stockout_prob,
                    p95_cumulative_demand=proj.get("p95_cumulative_demand", stock * 0.8),
                    route_status="BLOCKED" if any(s == "BLOCKED" for s in inflow_statuses) else "AVAILABLE",
                    weather_severity=w_sev,
                    demand_surge_percent=30.0 if node.type.value == "FORWARD_POST" else 0.0,
                )
                all_alerts.extend(item_alerts)

        # Route Alerts
        for rid, route in world.routes.items():
            src_node = world.nodes.get(route.source_node_id)
            dst_node = world.nodes.get(route.destination_node_id)
            src_code = src_node.code if src_node else route.source_node_id
            dst_code = dst_node.code if dst_node else route.destination_node_id
            w_state = world.weather_by_node.get(route.destination_node_id)
            w_sev = w_state.severity.value if w_state else "NORMAL"

            route_alerts = self.alert_engine.evaluate_route_alerts(
                route_id=rid,
                route_code=route.route_code,
                source_code=src_code,
                dest_code=dst_code,
                status=route.status.value,
                weather_severity=w_sev,
                dependency_factor=0.60 if "R-01" in route.route_code else 0.35,
            )
            all_alerts.extend(route_alerts)

        # 4. Network Risk Propagation
        dep_graph = self.propagator.build_dependency_graph(world.nodes, world.routes)
        propagated_results = self.propagator.propagate_risk(dep_graph, node_risks)

        # Cache results
        self._cached_assessments = assessments
        self._cached_criticalities = criticalities
        self._cached_propagated = propagated_results
        self._cached_alerts = all_alerts

        # Overall network summary metrics
        high_risk_nodes = [
            a.node_code for a in assessments.values() if a.level in ["HIGH", "CRITICAL"]
        ]
        blocked_routes = [
            r.route_code for r in world.routes.values() if r.status == RouteStatus.BLOCKED
        ]

        return {
            "node_assessments": {nid: a.to_dict() for nid, a in assessments.items()},
            "criticalities": criticalities,
            "propagated_risk": propagated_results,
            "alerts": [alt.to_dict() for alt in all_alerts],
            "summary": {
                "total_nodes_assessed": len(assessments),
                "high_risk_nodes_count": len(high_risk_nodes),
                "high_risk_nodes": high_risk_nodes,
                "blocked_routes_count": len(blocked_routes),
                "blocked_routes": blocked_routes,
                "total_active_alerts": len(all_alerts),
                "critical_alerts_count": sum(1 for a in all_alerts if a.severity == "CRITICAL"),
            },
        }
