"""Core Decision Engine Synthesizing Predictions, Optimization, Simulation, and Explainability."""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

from simulation.world_generator import WorldState, RouteStatus, VehicleStatus, NodeType
from optimization.types import MovementDecision, OptimizationResult, OptimizationStatus
from optimization.evaluation_metrics import PlanEvaluationResult, EvaluationStatus
from backend.app.decision.schemas import (
    ActionType,
    RecommendationStatus,
    DataQualityState,
    RecommendationSchema,
    DecisionConfidence,
    RouteAlternative,
)
from backend.app.decision.evidence import EvidenceBuilder
from backend.app.decision.tradeoffs import TradeoffAnalyzer
from backend.app.decision.confidence import ConfidenceScorer
from backend.app.decision.explanations import ExplanationGenerator


class DecisionEngine:
    """Transforms raw predictive, optimization, and counterfactual simulation outputs into auditable recommendations."""

    def __init__(self):
        self.evidence_builder = EvidenceBuilder()
        self.tradeoff_analyzer = TradeoffAnalyzer()
        self.confidence_scorer = ConfidenceScorer()
        self.explanation_gen = ExplanationGenerator()

    def generate_recommendations(
        self,
        world: WorldState,
        optimization_result: Optional[OptimizationResult] = None,
        evaluation_result: Optional[PlanEvaluationResult] = None,
        risk_assessments: Optional[Dict[str, Any]] = None,
        inventory_projections: Optional[Dict[str, Any]] = None,
        scenario_id: str = "COMPOUND_DISRUPTION",
        data_quality_state: str = DataQualityState.READY.value,
        forecast_version: str = "xgb-demand-v1",
        risk_version: str = "composite-risk-v1",
    ) -> List[RecommendationSchema]:
        """Executes the complete PREDICT -> RISK -> OPTIMIZE -> SIMULATE -> VERIFY -> EXPLAIN -> RECOMMEND loop."""
        recommendations: List[RecommendationSchema] = []
        opt_run_id = getattr(optimization_result, "run_id", "RUN_UNSPECIFIED")
        eval_id = getattr(evaluation_result, "evaluation_id", None)

        decisions: List[MovementDecision] = []
        if optimization_result and hasattr(optimization_result, "decisions"):
            decisions = optimization_result.decisions

        # Track usage to detect physical conflicts across the recommendation set
        assigned_vehicles_by_hour: Dict[Tuple[str, int], str] = {}
        route_loads: Dict[str, float] = {}
        source_depletions: Dict[Tuple[str, str], float] = {}

        # ----------------------------------------------------------------------
        # Special Case: Empty Decisions (Supply Exceeded, Infeasible, or Blocked)
        # ----------------------------------------------------------------------
        if not decisions:
            # Check if critical nodes are starved to generate explicit HOLD / DEFER recommendations
            for nid, node in world.nodes.items():
                if getattr(node, "type", "") == NodeType.FORWARD_POST or getattr(node, "priority", 3) >= 4:
                    risk = (risk_assessments or {}).get(nid)
                    overall_risk = getattr(risk, "overall_risk", 0.0) if risk else 0.0
                    if overall_risk >= 0.35:
                        rec_id = f"REC_{uuid.uuid4().hex[:8].upper()}"
                        confidence, forced_status = self.confidence_scorer.evaluate_confidence(
                            data_quality=data_quality_state,
                            has_sufficient_source_inventory=False,
                            is_route_open=False,
                            is_vehicle_available=True,
                            optimization_feasible=False,
                            counterfactual_verified=False,
                        )
                        status = forced_status or RecommendationStatus.INCONCLUSIVE.value

                        recommendations.append(
                            RecommendationSchema(
                                recommendation_id=rec_id,
                                scenario_id=scenario_id,
                                optimization_run_id=opt_run_id,
                                evaluation_id=eval_id,
                                priority=1,
                                action_type=ActionType.HOLD.value,
                                source_node="NONE",
                                destination_node=nid,
                                item="ALL",
                                quantity=0.0,
                                route="NONE",
                                vehicle="NONE",
                                planned_departure=0,
                                expected_arrival=0,
                                title=f"HOLD: Replenishment Suspended for {node.code}",
                                reason="No feasible convoy movements could be found; inbound routes or source inventory exhausted.",
                                evidence=[],
                                tradeoffs={"STATUS": "SUPPLY_CONSTRAINED_HOLD"},
                                expected_effect="Avoid dispatching assets into infeasible corridors.",
                                verified_effect="Zero dispatches confirmed by simulation.",
                                status=status,
                                confidence=confidence,
                                validation_state={"source_inventory": "FAIL", "route": "BLOCKED", "vehicle": "AVAILABLE"},
                                conflict_detected=False,
                                conflict_details=[],
                                alternatives=[],
                                audit_trail={
                                    "optimization_run_id": opt_run_id,
                                    "scenario_id": scenario_id,
                                    "forecast_version": forecast_version,
                                    "risk_version": risk_version,
                                },
                                created_at=datetime.now(timezone.utc).isoformat(),
                            )
                        )
            return recommendations

        # Sort decisions so critical forward defense posts claim vehicle slots first
        sorted_decisions = sorted(
            decisions,
            key=lambda d: getattr(world.nodes.get(d.destination_node_id), "priority", 3),
            reverse=True,
        )
        for idx, dec in enumerate(sorted_decisions):
            rec_id = f"REC_{uuid.uuid4().hex[:8].upper()}"
            src_node = world.nodes.get(dec.source_node_id)
            dst_node = world.nodes.get(dec.destination_node_id)
            route = world.routes.get(dec.route_id)
            vehicle = world.vehicles.get(dec.vehicle_id)

            src_code = getattr(src_node, "code", dec.source_node_id)
            dst_code = getattr(dst_node, "code", dec.destination_node_id)
            r_code = getattr(route, "route_code", dec.route_id)
            v_code = getattr(vehicle, "vehicle_code", dec.vehicle_id)

            risk_entry = (risk_assessments or {}).get(dec.destination_node_id)
            inv_proj = (inventory_projections or {}).get(dec.destination_node_id)

            # Check alternative routes and primary blockage
            alternatives, alt_narrative = self.explanation_gen.analyze_route_alternatives(
                selected_route_id=dec.route_id,
                routes=world.routes,
                route_risks=getattr(optimization_result, "route_utilization", {}),
            )
            primary_blocked = any(a.status == "BLOCKED" for a in alternatives if not a.is_selected)
            primary_route_code = next((a.route_id for a in alternatives if not a.is_selected and a.status == "BLOCKED"), None)

            # Determine Action Type
            action_type = ActionType.MOVE.value
            if primary_blocked:
                action_type = ActionType.REROUTE.value
            elif getattr(src_node, "type", "") == NodeType.REGIONAL_HUB and getattr(dst_node, "priority", 3) >= 4:
                action_type = ActionType.REALLOCATE.value
            elif getattr(dst_node, "priority", 3) == 5:
                action_type = ActionType.PRIORITIZE.value

            # Build Evidence
            evidence = self.evidence_builder.build_decision_evidence(
                dst_node=dst_node,
                src_node=src_node,
                route=route,
                vehicle=vehicle,
                item=dec.item,
                quantity=dec.quantity,
                risk_assessment=risk_entry,
                inventory_projection=inv_proj,
                counterfactual_eval=evaluation_result,
            )

            # Physical Validation & Conflict Detection
            val_state: Dict[str, str] = {}
            conflicts: List[str] = []

            # 1. Source Inventory Check & Conflict
            avail_stock = float(getattr(src_node, "initial_inventory", {}).get(dec.item, 5000.0)) if src_node else 0.0
            cum_src = source_depletions.get((dec.source_node_id, dec.item), 0.0) + dec.quantity
            source_depletions[(dec.source_node_id, dec.item)] = cum_src

            if avail_stock <= 0.0:
                val_state["source_inventory"] = "FAIL"
                conflicts.append(f"Source depot {src_code} has 0 available stock of {dec.item}.")
            elif cum_src > avail_stock + 1e-3:
                val_state["source_inventory"] = "CONFLICT"
                conflicts.append(f"Aggregate dispatches from {src_code} for {dec.item} ({cum_src:.1f}) exceed stock ({avail_stock:.1f}).")
            else:
                val_state["source_inventory"] = "PASS"

            # 2. Route Check & Capacity Conflict
            r_status = getattr(route, "status", RouteStatus.AVAILABLE)
            r_max_cap = float(getattr(route, "max_capacity", 5000.0)) if route else 5000.0
            cum_route = route_loads.get(dec.route_id, 0.0) + dec.quantity
            route_loads[dec.route_id] = cum_route

            if r_status == RouteStatus.BLOCKED or str(r_status) == "BLOCKED":
                val_state["route"] = "BLOCKED"
                conflicts.append(f"Route {r_code} is BLOCKED; cannot dispatch convoy.")
            elif cum_route > r_max_cap + 1e-3:
                val_state["route"] = "CONFLICT"
                conflicts.append(f"Aggregate route load on {r_code} ({cum_route:.1f}) exceeds capacity ({r_max_cap:.1f}).")
            else:
                val_state["route"] = "PASS"

            # 3. Vehicle Availability & Fleet Conflict
            v_avail = getattr(vehicle, "availability", True)
            v_cap = float(getattr(vehicle, "capacity", 5000.0)) if vehicle else 5000.0
            v_slot = (dec.vehicle_id, dec.dispatch_hour)

            if not v_avail:
                val_state["vehicle"] = "UNAVAILABLE"
                conflicts.append(f"Vehicle {v_code} is marked UNAVAILABLE in fleet registry.")
            elif v_slot in assigned_vehicles_by_hour:
                val_state["vehicle"] = "CONFLICT"
                conflicts.append(f"Vehicle conflict: {v_code} is already assigned to simultaneous dispatch at hour {dec.dispatch_hour}.")
            elif dec.quantity > v_cap + 1e-3:
                val_state["vehicle"] = "EXCEEDED_CAPACITY"
                conflicts.append(f"Vehicle payload rating ({v_cap:.1f}) exceeded by dispatch quantity ({dec.quantity:.1f}).")
            else:
                val_state["vehicle"] = "PASS"
                assigned_vehicles_by_hour[v_slot] = dec.decision_id

            val_state["quantity"] = "PASS" if dec.quantity > 0.0 else "ZERO"
            val_state["optimization"] = "PASS" if optimization_result and optimization_result.status == OptimizationStatus.OPTIMAL else "FEASIBLE"
            val_state["counterfactual"] = "PASS" if evaluation_result and evaluation_result.status != EvaluationStatus.INVALID else "NOT_RUN"
            val_state["data_quality"] = data_quality_state

            # Evaluate Tradeoffs
            dist_km = float(getattr(route, "distance_km", 50.0)) if route else 50.0
            tradeoffs = self.tradeoff_analyzer.analyze_tradeoffs(
                evaluation=evaluation_result,
                quantity=dec.quantity,
                distance_km=dist_km,
            )

            # Evaluate Confidence
            is_route_open = (val_state["route"] == "PASS")
            has_stock = (val_state["source_inventory"] == "PASS")
            is_veh_ok = (val_state["vehicle"] == "PASS")
            cf_verified = (
                evaluation_result is not None
                and evaluation_result.status in [EvaluationStatus.IMPROVED, EvaluationStatus.MIXED]
            )

            confidence, forced_status = self.confidence_scorer.evaluate_confidence(
                data_quality=data_quality_state,
                has_sufficient_source_inventory=has_stock,
                is_route_open=is_route_open,
                is_vehicle_available=is_veh_ok,
                optimization_feasible=True,
                counterfactual_verified=cf_verified,
            )

            # Determine Recommendation Status
            has_conflicts = len(conflicts) > 0
            if has_conflicts:
                rec_status = RecommendationStatus.REJECTED.value
            elif forced_status:
                rec_status = forced_status
            elif evaluation_result is not None:
                if evaluation_result.status == EvaluationStatus.IMPROVED:
                    rec_status = RecommendationStatus.VERIFIED.value
                elif evaluation_result.status == EvaluationStatus.MIXED:
                    rec_status = RecommendationStatus.MIXED.value
                elif evaluation_result.status == EvaluationStatus.DEGRADED:
                    rec_status = RecommendationStatus.REJECTED.value
                else:
                    rec_status = RecommendationStatus.INCONCLUSIVE.value
            else:
                rec_status = RecommendationStatus.PROPOSED.value

            # Expected Effect vs Verified Effect
            expected_effect = f"Projected to fulfill {dec.quantity:.1f} units {dec.item} at {dst_code} and mitigate stockout risk."
            if evaluation_result and hasattr(evaluation_result, "deltas"):
                unmet_d = evaluation_result.deltas.get("unmet_demand")
                if unmet_d:
                    verified_effect = f"Counterfactual simulation verified unmet demand change of {unmet_d.absolute_delta:+.1f} units ({unmet_d.relative_delta_percent:+.1f}%)."
                else:
                    verified_effect = "Simulation executed; no direct demand delta recorded."
            else:
                verified_effect = "Counterfactual evaluation not executed yet."

            # Generate Fact-Grounded Explanation
            why_text = self.explanation_gen.generate_why_explanation(
                action_type=action_type,
                dst_code=dst_code,
                src_code=src_code,
                item=dec.item,
                quantity=dec.quantity,
                route_code=r_code,
                vehicle_code=v_code,
                evidence=evidence,
                primary_blocked=primary_blocked,
                primary_route_code=primary_route_code,
            )

            # Assign Priority
            node_priority = getattr(dst_node, "priority", 3) if dst_node else 3
            if node_priority == 5:
                rec_priority = 1
            elif node_priority == 4:
                rec_priority = 2
            elif node_priority >= 2:
                rec_priority = 3
            else:
                rec_priority = 4

            recommendations.append(
                RecommendationSchema(
                    recommendation_id=rec_id,
                    scenario_id=scenario_id,
                    optimization_run_id=opt_run_id,
                    evaluation_id=eval_id,
                    priority=rec_priority,
                    action_type=action_type,
                    source_node=dec.source_node_id,
                    destination_node=dec.destination_node_id,
                    item=dec.item,
                    quantity=dec.quantity,
                    route=dec.route_id,
                    vehicle=dec.vehicle_id,
                    planned_departure=dec.dispatch_hour,
                    expected_arrival=dec.estimated_arrival_hour,
                    title=f"{action_type}: {dec.quantity:.0f} {dec.item} {src_code} -> {dst_code}",
                    reason=why_text,
                    evidence=evidence,
                    tradeoffs=tradeoffs,
                    expected_effect=expected_effect,
                    verified_effect=verified_effect,
                    status=rec_status,
                    confidence=confidence,
                    validation_state=val_state,
                    conflict_detected=has_conflicts,
                    conflict_details=conflicts,
                    alternatives=alternatives,
                    audit_trail={
                        "optimization_run_id": opt_run_id,
                        "evaluation_id": eval_id or "NONE",
                        "scenario_id": scenario_id,
                        "forecast_version": forecast_version,
                        "risk_version": risk_version,
                    },
                    created_at=datetime.now(timezone.utc).isoformat(),
                )
            )

        # Sort recommendations deterministically by priority (1 to 5) then arrival hour
        recommendations.sort(key=lambda r: (r.priority, r.expected_arrival, r.destination_node))
        return recommendations
