"""Evaluator for Counterfactual Resilience and Recommendation Impact.

Answers: Did the recommended action actually improve the outcome?
Re-runs simulation with the recommended dispatches and measures empirical delta.
"""

from __future__ import annotations
from typing import Dict, Any, List
from optimization.model import OptimizationPlan, SupplyDecision
from simulation.simulator import Simulator, SimulationConfig


class PlanEvaluator:
    """Evaluates optimization plans by comparing baseline vs counterfactual simulation metrics."""

    def evaluate_plan(
        self,
        plan: OptimizationPlan,
        base_config: SimulationConfig,
    ) -> Dict[str, Any]:
        """Runs baseline and counterfactual simulations to measure concrete delta."""
        # 1. Run baseline simulation under disruption without interventions
        sim_baseline = Simulator(config=base_config)
        res_baseline = sim_baseline.run()

        # 2. Inject plan decisions into world or simulator
        # Counterfactual: pre-position supplies or initiate planned dispatches
        sim_intervention = Simulator(config=base_config)

        # Inject planned dispatches as early shipments in intervention simulator
        for d in plan.decisions:
            route = sim_intervention.world.routes.get(d.route_id)
            if route:
                sim_intervention.shipment_counter += 1
                from simulation.world_generator import Shipment
                sh = Shipment(
                    shipment_id=f"OPT_{d.decision_id}",
                    source_node_id=d.source_node_id,
                    destination_node_id=d.destination_node_id,
                    item=d.item,
                    quantity=d.quantity,
                    route_id=d.route_id,
                    vehicle_id=d.vehicle_id,
                    departure_time=d.dispatch_hour,
                    expected_arrival=d.estimated_arrival_hour,
                    actual_arrival=d.estimated_arrival_hour,
                    status="IN_TRANSIT",
                )
                sim_intervention.world.active_shipments.append(sh)
                sim_intervention.all_shipments.append(sh)

        res_intervention = sim_intervention.run()

        unmet_delta = res_baseline.total_unmet_demand - res_intervention.total_unmet_demand
        stockout_reduction = res_baseline.total_stockout_events - res_intervention.total_stockout_events

        return {
            "baseline_unmet": res_baseline.total_unmet_demand,
            "intervention_unmet": res_intervention.total_unmet_demand,
            "unmet_demand_saved": round(max(0.0, unmet_delta), 1),
            "baseline_stockout_events": res_baseline.total_stockout_events,
            "intervention_stockout_events": res_intervention.total_stockout_events,
            "stockouts_prevented": max(0, stockout_reduction),
            "fulfillment_rate_before": res_baseline.fulfillment_rate_percent,
            "fulfillment_rate_after": res_intervention.fulfillment_rate_percent,
            "plan_verified_effective": unmet_delta > 0 or stockout_reduction > 0,
        }
