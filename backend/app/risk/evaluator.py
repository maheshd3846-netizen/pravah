"""Risk Evaluation Service for forward supply chain vulnerability assessment."""

from __future__ import annotations
from typing import Dict, List, Any
from simulation.world_generator import WorldState, RouteStatus


class RiskEvaluator:
    """Computes isolation risk, bottleneck criticality, and stockout vulnerability."""

    def evaluate_network_risk(self, world: WorldState) -> Dict[str, Any]:
        """Calculates topological vulnerability and isolation scores for forward nodes."""
        node_risk: Dict[str, Dict[str, Any]] = {}

        for nid, node in world.nodes.items():
            # Count connected incoming routes and how many are currently available
            incoming = [r for r in world.routes.values() if r.destination_node_id == nid]
            available_incoming = [r for r in incoming if r.status == RouteStatus.AVAILABLE]

            isolation_score = (
                1.0 - (len(available_incoming) / max(1, len(incoming)))
                if incoming
                else 1.0
            )

            # High altitude multiplier
            altitude_risk = min(1.0, max(0.0, (node.elevation - 2000.0) / 3000.0))
            composite_risk = round(0.6 * isolation_score + 0.4 * altitude_risk, 2)

            level = "LOW"
            if composite_risk > 0.7:
                level = "CRITICAL"
            elif composite_risk > 0.4:
                level = "ELEVATED"

            node_risk[nid] = {
                "node_code": node.code,
                "isolation_score": round(isolation_score, 2),
                "composite_risk": composite_risk,
                "risk_level": level,
                "available_inflow_routes": len(available_incoming),
                "total_inflow_routes": len(incoming),
            }

        return node_risk
