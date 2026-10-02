"""Counterfactual Plan Evaluator and Closed-Loop Validation Engine for PRAVAH.

Executes paired, controlled simulations starting from identical state snapshots to
definitively evaluate whether an optimizer plan improves simulated logistics outcomes.
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

from simulation.world_generator import (
    RouteStatus,
    VehicleStatus,
    Shipment,
    NodeType,
)
from simulation.simulator import Simulator, SimulationConfig, SimulationResult
from simulation.state_snapshot import StateSnapshot
from optimization.types import MovementDecision
from optimization.plan_adapter import (
    OptimizationPlanAdapter,
    ExecutableIntervention,
    OPTIMIZER_TO_SIM_COMMODITY,
)
from optimization.evaluation_metrics import (
    MetricDirection,
    EvaluationStatus,
    MetricDelta,
    SimulationRunMetrics,
    ShipmentExecutionTrace,
    PlanEvaluationResult,
)


class PlanEvaluator:
    """Evaluates optimization plans by comparing baseline vs counterfactual simulation metrics."""

    def __init__(self):
        pass

    def _extract_metrics(
        self,
        sim: Simulator,
        res: SimulationResult,
    ) -> SimulationRunMetrics:
        """Extracts multidimensional operational KPIs from completed simulation trajectory."""
        inv_snapshots = res.snapshots
        total_initial_inv = 0.0
        total_final_inv = 0.0
        min_inv = float("inf")
        avg_inv_sum = 0.0

        if inv_snapshots:
            hours = sorted(list(set(s.timestamp_hour for s in inv_snapshots)))
            first_h = hours[0]
            last_h = hours[-1]
            total_initial_inv = sum(s.starting_inventory for s in inv_snapshots if s.timestamp_hour == first_h)
            total_final_inv = sum(s.ending_inventory for s in inv_snapshots if s.timestamp_hour == last_h)

            hourly_totals = [
                sum(s.ending_inventory for s in inv_snapshots if s.timestamp_hour == h)
                for h in hours
            ]
            min_inv = min(hourly_totals) if hourly_totals else 0.0
            avg_inv = sum(hourly_totals) / max(1, len(hourly_totals)) if hourly_totals else 0.0
        else:
            avg_inv = 0.0
            min_inv = 0.0

        # Stockout KPIs
        stockouts = res.stockout_events
        stockout_count = len(stockouts)
        stockout_duration = res.stockout_hours_total
        affected_nodes = len(set(e.node_id for e in stockouts))
        affected_items = len(set(e.item for e in stockouts))

        # Transport & delay KPIs
        shipments = res.shipments
        total_dist = 0.0
        total_transit_hrs = 0.0
        delays = []
        for s in shipments:
            r = sim.world.routes.get(s.route_id)
            if r:
                total_dist += r.distance_km
            transit_time = max(0, s.actual_arrival - s.departure_time)
            total_transit_hrs += transit_time
            delay = max(0, s.actual_arrival - s.expected_arrival)
            delays.append(delay)

        avg_delay = float(sum(delays) / max(1, len(delays))) if delays else 0.0
        max_delay = float(max(delays)) if delays else 0.0

        # Fleet utilization
        total_vehs = len(sim.world.vehicles)
        busy_vehs = sum(1 for v in sim.world.vehicles.values() if v.status == VehicleStatus.IN_TRANSIT)
        utilization = busy_vehs / max(1, total_vehs)

        # Critical node analysis
        critical_details = {}
        for nid, node in sim.world.nodes.items():
            if node.type in [NodeType.FORWARD_POST, NodeType.REGIONAL_HUB]:
                node_code = node.code
                # Check earliest stockout hour for this node
                node_stockouts = [e for e in stockouts if e.node_id == nid]
                earliest_so = min((e.timestamp_hour for e in node_stockouts), default=None)
                critical_details[node_code] = {
                    "node_id": nid,
                    "node_code": node_code,
                    "priority": node.priority,
                    "stockout_occurred": len(node_stockouts) > 0,
                    "earliest_stockout_hour": earliest_so,
                    "stockout_events_count": len(node_stockouts),
                }

        return SimulationRunMetrics(
            total_requested_demand=res.total_requested_demand,
            total_fulfilled_demand=res.total_fulfilled_demand,
            total_unmet_demand=res.total_unmet_demand,
            fulfillment_rate_percent=res.fulfillment_rate_percent,
            total_stockout_events=stockout_count,
            stockout_duration_hours=stockout_duration,
            nodes_affected_stockout=affected_nodes,
            items_affected_stockout=affected_items,
            safety_stock_breaches=stockout_count,  # Proxy in standard simulator
            safety_stock_breach_hours=stockout_duration,
            initial_inventory_total=total_initial_inv,
            final_inventory_total=total_final_inv,
            minimum_inventory_total=min_inv if min_inv != float("inf") else 0.0,
            average_inventory_total=avg_inv,
            total_transport_distance_km=total_dist,
            total_transit_hours=total_transit_hrs,
            average_delay_hours=avg_delay,
            maximum_delay_hours=max_delay,
            vehicle_utilization_rate=utilization,
            active_fleet_count=total_vehs,
            critical_node_metrics=critical_details,
        )

    def _compute_delta(
        self,
        metric_name: str,
        base_val: float,
        opt_val: float,
        lower_is_better: bool = True,
    ) -> MetricDelta:
        """Calculates absolute delta, relative percentage, and qualitative direction."""
        abs_delta = opt_val - base_val
        if abs(base_val) > 1e-4:
            rel_delta = (abs_delta / abs(base_val)) * 100.0
        else:
            rel_delta = 0.0 if abs(abs_delta) < 1e-4 else 100.0

        if abs(abs_delta) < 1e-3 or abs(rel_delta) < 0.1:
            direction = MetricDirection.UNCHANGED
            is_better = False
        elif (abs_delta < 0 and lower_is_better) or (abs_delta > 0 and not lower_is_better):
            direction = MetricDirection.IMPROVED
            is_better = True
        else:
            direction = MetricDirection.DEGRADED
            is_better = False

        return MetricDelta(
            metric_name=metric_name,
            baseline=base_val,
            optimized=opt_val,
            absolute_delta=abs_delta,
            relative_delta_percent=rel_delta,
            direction=direction,
            is_better=is_better,
        )

    def evaluate_plan(
        self,
        plan_or_result: Any,
        base_config: Optional[SimulationConfig] = None,
        scenario_id: str = "COMPOUND_DISRUPTION",
        horizon_hours: int = 72,
        seed: int = 42,
        initial_state: Optional[StateSnapshot] = None,
    ) -> PlanEvaluationResult:
        """Executes strictly paired simulations and measures concrete counterfactual deltas."""
        eval_id = f"EVAL_{uuid.uuid4().hex[:8].upper()}"
        opt_run_id = getattr(plan_or_result, "run_id", getattr(plan_or_result, "plan_id", "PLAN_001"))

        cfg = base_config or SimulationConfig(
            seed=seed,
            horizon_hours=horizon_hours,
            scenario_name=scenario_id,
            auto_replenish=True,
        )

        # ----------------------------------------------------------------------
        # Step 1: Initialize Baseline Simulator and Capture State Snapshot
        # ----------------------------------------------------------------------
        sim_baseline = Simulator(config=cfg)
        if initial_state is not None:
            initial_state.restore_into(sim_baseline)
            snapshot_baseline = StateSnapshot.capture(sim_baseline)
        else:
            snapshot_baseline = StateSnapshot.capture(sim_baseline)
        initial_hash = snapshot_baseline.hash()

        # ----------------------------------------------------------------------
        # Step 2: Validate Optimization Decisions against Pre-Simulation Snapshot
        # ----------------------------------------------------------------------
        if hasattr(plan_or_result, "decisions"):
            raw_decisions = plan_or_result.decisions
        elif isinstance(plan_or_result, list):
            raw_decisions = plan_or_result
        else:
            raw_decisions = []

        validation = OptimizationPlanAdapter.validate_plan(
            decisions=raw_decisions,
            initial_inventory=snapshot_baseline.inventory_data,
            routes=sim_baseline.world.routes,
            vehicles=sim_baseline.world.vehicles,
        )

        # ----------------------------------------------------------------------
        # Step 3: Run Baseline Simulation (No Optimizer Intervention)
        # ----------------------------------------------------------------------
        res_baseline = sim_baseline.run()
        baseline_metrics = self._extract_metrics(sim_baseline, res_baseline)

        # ----------------------------------------------------------------------
        # Step 4: Handle Invalid Plan Early
        # ----------------------------------------------------------------------
        if not validation.is_feasible:
            return PlanEvaluationResult(
                evaluation_id=eval_id,
                optimization_run_id=opt_run_id,
                scenario_id=scenario_id,
                status=EvaluationStatus.INVALID,
                horizon_hours=horizon_hours,
                seed=seed,
                initial_state_hash=initial_hash,
                baseline=baseline_metrics,
                optimized=baseline_metrics,
                deltas={},
                tradeoffs={"STATUS": "Plan rejected during pre-simulation constraint validation."},
                critical_nodes=[],
                shipment_trace=[],
                plan_validation_status="PLAN_INVALID",
                plan_validation_violations=validation.violations,
                created_at=datetime.now(timezone.utc).isoformat(),
            )

        # ----------------------------------------------------------------------
        # Step 5: Initialize Paired Intervention Simulator from Identical Snapshot
        # ----------------------------------------------------------------------
        sim_intervention = Simulator(config=cfg)
        snapshot_baseline.restore_into(sim_intervention)

        # State Hash Integrity Verification
        snapshot_intervention = StateSnapshot.capture(sim_intervention)
        intervention_hash = snapshot_intervention.hash()

        if initial_hash != intervention_hash:
            return PlanEvaluationResult(
                evaluation_id=eval_id,
                optimization_run_id=opt_run_id,
                scenario_id=scenario_id,
                status=EvaluationStatus.INVALID,
                horizon_hours=horizon_hours,
                seed=seed,
                initial_state_hash=initial_hash,
                baseline=baseline_metrics,
                optimized=baseline_metrics,
                deltas={},
                tradeoffs={"STATUS": "State snapshot hash mismatch between baseline and intervention."},
                critical_nodes=[],
                shipment_trace=[],
                plan_validation_status="PLAN_INVALID",
                plan_validation_violations=["Initial world state altered prior to intervention execution."],
                created_at=datetime.now(timezone.utc).isoformat(),
            )

        # ----------------------------------------------------------------------
        # Step 6: Inject Planned Movements as Real Physical Shipments
        # ----------------------------------------------------------------------
        shipment_trace: List[ShipmentExecutionTrace] = []

        for d in raw_decisions:
            route = sim_intervention.world.routes.get(d.route_id)
            veh = sim_intervention.world.vehicles.get(d.vehicle_id)

            if not route or not veh:
                shipment_trace.append(
                    ShipmentExecutionTrace(
                        decision_id=d.decision_id,
                        item=d.item,
                        planned_quantity=d.quantity,
                        actual_dispatched_quantity=0.0,
                        actual_arrival_quantity=0.0,
                        source_node=d.source_node_id,
                        destination_node=d.destination_node_id,
                        route_id=d.route_id,
                        vehicle_id=d.vehicle_id,
                        departure_hour=d.dispatch_hour,
                        arrival_hour=d.estimated_arrival_hour,
                        transit_delay_hours=0.0,
                        status="FAILED",
                        failure_reason="Route or vehicle not found during physical dispatch injection.",
                    )
                )
                continue

            # Deduct inventory at source immediately
            sim_item = OPTIMIZER_TO_SIM_COMMODITY.get(d.item, d.item)
            current_src_stock = sim_intervention.inventory_engine.current_inventory.get(d.source_node_id, {}).get(sim_item, 0.0)
            dispatch_qty = min(d.quantity, current_src_stock)

            if dispatch_qty <= 0.0:
                shipment_trace.append(
                    ShipmentExecutionTrace(
                        decision_id=d.decision_id,
                        item=d.item,
                        planned_quantity=d.quantity,
                        actual_dispatched_quantity=0.0,
                        actual_arrival_quantity=0.0,
                        source_node=d.source_node_id,
                        destination_node=d.destination_node_id,
                        route_id=d.route_id,
                        vehicle_id=d.vehicle_id,
                        departure_hour=d.dispatch_hour,
                        arrival_hour=d.estimated_arrival_hour,
                        transit_delay_hours=0.0,
                        status="FAILED",
                        failure_reason=f"Source node {d.source_node_id} depleted before dispatch.",
                    )
                )
                continue

            sim_intervention.inventory_engine.current_inventory[d.source_node_id][sim_item] -= dispatch_qty

            # Calculate physical arrival based on simulated route and weather
            dest_node = sim_intervention.world.nodes.get(d.destination_node_id)
            w_state = sim_intervention.weather_gen.generate_weather(dest_node, d.dispatch_hour) if dest_node else None
            eff_hours = sim_intervention.weather_gen.calculate_effective_travel_time(route, w_state) if w_state else route.base_travel_hours

            if route.status == RouteStatus.DEGRADED:
                eff_hours = round(eff_hours * 1.8, 2)

            actual_arrival = d.dispatch_hour + max(1, int(round(eff_hours)))
            delay = max(0.0, float(actual_arrival - d.estimated_arrival_hour))

            sim_intervention.shipment_counter += 1
            sh = Shipment(
                shipment_id=f"OPT_{d.decision_id}",
                source_node_id=d.source_node_id,
                destination_node_id=d.destination_node_id,
                item=sim_item,
                quantity=round(dispatch_qty, 1),
                route_id=d.route_id,
                vehicle_id=d.vehicle_id,
                departure_time=d.dispatch_hour,
                expected_arrival=d.estimated_arrival_hour,
                actual_arrival=actual_arrival,
                status="IN_TRANSIT",
            )

            # Reserve vehicle
            veh.status = VehicleStatus.IN_TRANSIT
            veh.availability = False
            veh.current_node_id = d.destination_node_id

            sim_intervention.world.active_shipments.append(sh)
            sim_intervention.all_shipments.append(sh)

            shipment_trace.append(
                ShipmentExecutionTrace(
                    decision_id=d.decision_id,
                    item=d.item,
                    planned_quantity=d.quantity,
                    actual_dispatched_quantity=dispatch_qty,
                    actual_arrival_quantity=dispatch_qty,
                    source_node=d.source_node_id,
                    destination_node=d.destination_node_id,
                    route_id=d.route_id,
                    vehicle_id=d.vehicle_id,
                    departure_hour=d.dispatch_hour,
                    arrival_hour=actual_arrival,
                    transit_delay_hours=delay,
                    status="DELIVERED" if actual_arrival <= horizon_hours else "IN_TRANSIT",
                )
            )

        # ----------------------------------------------------------------------
        # Step 7: Execute Intervention Simulation
        # ----------------------------------------------------------------------
        res_intervention = sim_intervention.run()
        optimized_metrics = self._extract_metrics(sim_intervention, res_intervention)

        # ----------------------------------------------------------------------
        # Step 8: Compute KPIs and Metric Deltas
        # ----------------------------------------------------------------------
        deltas = {
            "unmet_demand": self._compute_delta(
                "unmet_demand",
                baseline_metrics.total_unmet_demand,
                optimized_metrics.total_unmet_demand,
                lower_is_better=True,
            ),
            "stockout_events": self._compute_delta(
                "stockout_events",
                float(baseline_metrics.total_stockout_events),
                float(optimized_metrics.total_stockout_events),
                lower_is_better=True,
            ),
            "stockout_duration_hours": self._compute_delta(
                "stockout_duration_hours",
                float(baseline_metrics.stockout_duration_hours),
                float(optimized_metrics.stockout_duration_hours),
                lower_is_better=True,
            ),
            "fulfillment_rate_percent": self._compute_delta(
                "fulfillment_rate_percent",
                baseline_metrics.fulfillment_rate_percent,
                optimized_metrics.fulfillment_rate_percent,
                lower_is_better=False,
            ),
            "transport_distance_km": self._compute_delta(
                "transport_distance_km",
                baseline_metrics.total_transport_distance_km,
                optimized_metrics.total_transport_distance_km,
                lower_is_better=True,
            ),
            "transit_hours": self._compute_delta(
                "transit_hours",
                baseline_metrics.total_transit_hours,
                optimized_metrics.total_transit_hours,
                lower_is_better=True,
            ),
            "average_delay_hours": self._compute_delta(
                "average_delay_hours",
                baseline_metrics.average_delay_hours,
                optimized_metrics.average_delay_hours,
                lower_is_better=True,
            ),
        }

        # ----------------------------------------------------------------------
        # Step 9: Tradeoff Analysis & Status Classification
        # ----------------------------------------------------------------------
        service_improved = (
            deltas["unmet_demand"].is_better or deltas["stockout_events"].is_better or deltas["fulfillment_rate_percent"].is_better
        )
        service_degraded = (
            deltas["unmet_demand"].direction == MetricDirection.DEGRADED and deltas["stockout_events"].direction == MetricDirection.DEGRADED
        )
        transport_increased = deltas["transport_distance_km"].direction == MetricDirection.DEGRADED

        tradeoffs = {
            "SERVICE": "IMPROVED" if service_improved else ("DEGRADED" if service_degraded else "UNCHANGED"),
            "RISK": "MITIGATED" if service_improved else "UNRESOLVED",
            "TRANSPORT_COST": "INCREASED" if transport_increased else "REDUCED_OR_EQUAL",
            "DELAY": "REDUCED" if deltas["average_delay_hours"].is_better else "UNCHANGED_OR_INCREASED",
            "FLEET_UTILIZATION": "ACTIVE_CONVOYS_DISPATCHED" if len(raw_decisions) > 0 else "NO_CONVOYS",
        }

        # Transparent verdict classification
        if not raw_decisions:
            overall_status = EvaluationStatus.INCONCLUSIVE
        elif service_improved and not transport_increased:
            overall_status = EvaluationStatus.IMPROVED
        elif service_improved and transport_increased:
            overall_status = EvaluationStatus.MIXED
        elif service_degraded:
            overall_status = EvaluationStatus.DEGRADED
        else:
            overall_status = EvaluationStatus.INCONCLUSIVE

        # ----------------------------------------------------------------------
        # Step 10: Critical Nodes Comparison
        # ----------------------------------------------------------------------
        critical_comparison: List[Dict[str, Any]] = []
        for code, b_data in baseline_metrics.critical_node_metrics.items():
            o_data = optimized_metrics.critical_node_metrics.get(code, {})
            b_so = b_data.get("earliest_stockout_hour")
            o_so = o_data.get("earliest_stockout_hour")

            if b_so is not None and o_so is not None:
                survival_diff = o_so - b_so
            elif b_so is not None and o_so is None:
                survival_diff = horizon_hours - b_so  # Completely avoided stockout
            elif b_so is None and o_so is None:
                survival_diff = 0
            else:
                survival_diff = -1

            critical_comparison.append({
                "node_code": code,
                "priority": b_data.get("priority", 3),
                "baseline_stockout": b_data.get("stockout_occurred", False),
                "baseline_earliest_stockout_hour": b_so,
                "optimized_stockout": o_data.get("stockout_occurred", False),
                "optimized_earliest_stockout_hour": o_so,
                "survival_hours_difference": survival_diff,
                "stockout_prevented": (b_data.get("stockout_occurred") and not o_data.get("stockout_occurred")),
            })

        return PlanEvaluationResult(
            evaluation_id=eval_id,
            optimization_run_id=opt_run_id,
            scenario_id=scenario_id,
            status=overall_status,
            horizon_hours=horizon_hours,
            seed=seed,
            initial_state_hash=initial_hash,
            baseline=baseline_metrics,
            optimized=optimized_metrics,
            deltas=deltas,
            tradeoffs=tradeoffs,
            critical_nodes=critical_comparison,
            shipment_trace=shipment_trace,
            plan_validation_status="PLAN_FEASIBLE",
            plan_validation_violations=[],
            created_at=datetime.now(timezone.utc).isoformat(),
        )
