"""Actionable Recommendation Engine for PRAVAH Logistics Decision Support.

Translates mathematical optimization plans and risk evaluations into
concrete, prioritized military logistics operational recommendations.
"""

from __future__ import annotations
from typing import Dict, List, Any
from optimization.model import OptimizationPlan


class RecommendationEngine:
    """Generates prioritized tactical directives from simulation and optimization outputs."""

    def generate_recommendations(
        self,
        plan: OptimizationPlan,
        critical_nodes: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Generates clear, actionable logistics directives answering 'What should be done?'"""
        recommendations = []

        # 1. Critical node alerts
        for cn in critical_nodes[:3]:
            node_code = cn.get("node_code", "UNKNOWN")
            unmet = cn.get("unmet_demand", 0.0)
            recommendations.append({
                "id": f"REC_ALERT_{node_code}",
                "category": "CRITICAL_DEFICIT_ALERT",
                "priority": "P1_URGENT",
                "action": f"Immediate replenishment required at {node_code}. Projected shortage: {unmet} units.",
                "expected_impact": "Prevents catastrophic operational stockout at forward line.",
                "status": "ACTIONABLE",
            })

        # 2. Convert optimization decisions to operational orders
        for idx, dec in enumerate(plan.decisions):
            recommendations.append({
                "id": f"REC_DISPATCH_{idx+1:03d}",
                "category": "CONVOY_DISPATCH",
                "priority": "P2_HIGH",
                "action": f"Dispatch vehicle {dec.vehicle_id} with {dec.quantity} units of {dec.item} from {dec.source_node_id} to {dec.destination_node_id} via route {dec.route_id}.",
                "expected_impact": dec.rationale,
                "status": "APPROVED_READY",
            })

        return recommendations
