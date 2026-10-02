"""Multi-Dimensional Tradeoff Evaluation Engine for Logistics Recommendations."""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from backend.app.decision.schemas import RecommendationStatus


class TradeoffAnalyzer:
    """Analyzes and articulates operational compromises across multiple dimensions."""

    @staticmethod
    def analyze_tradeoffs(
        evaluation: Optional[Any] = None,
        quantity: float = 0.0,
        distance_km: float = 0.0,
    ) -> Dict[str, Any]:
        """Calculates multi-dimensional operational tradeoffs without concealing costs."""
        if not evaluation or not hasattr(evaluation, "deltas"):
            # Default estimated tradeoff before simulation
            return {
                "SERVICE": "PROJECTED_IMPROVEMENT",
                "RISK": "PROJECTED_MITIGATION",
                "TRANSPORT_COST": "MODERATE_EXPEDITION" if distance_km > 0 else "ZERO",
                "DELAY": "ESTIMATED_NORMAL",
                "FLEET_UTILIZATION": "SINGLE_ASSET_DEPLOYED",
                "NET_RESULT": "PROPOSED_TRADEOFF",
                "narrative": (
                    f"Dispatching {quantity:.1f} units over {distance_km:.1f} km projected to resolve forward stockout "
                    f"in exchange for operational transport expenditure."
                ),
            }

        deltas = evaluation.deltas
        unmet_d = deltas.get("unmet_demand")
        so_d = deltas.get("stockout_events")
        dist_d = deltas.get("transport_distance_km")
        delay_d = deltas.get("average_delay_hours")

        service_improved = (unmet_d and unmet_d.is_better) or (so_d and so_d.is_better)
        service_degraded = (unmet_d and unmet_d.direction.value == "DEGRADED")
        transport_increased = dist_d and dist_d.direction.value == "DEGRADED"  # Lower is better for distance
        delay_increased = delay_d and delay_d.direction.value == "DEGRADED"

        service_status = "IMPROVED" if service_improved else ("DEGRADED" if service_degraded else "UNCHANGED")
        risk_status = "MITIGATED" if service_improved else "UNRESOLVED"
        transport_status = "INCREASED" if transport_increased else "REDUCED_OR_EQUAL"
        delay_status = "INCREASED" if delay_increased else ("REDUCED" if (delay_d and delay_d.is_better) else "UNCHANGED")
        fleet_status = "ACTIVE_CONVOYS_DISPATCHED" if quantity > 0 else "IDLE"

        # Explicit Net Classification
        if service_improved and not transport_increased and not delay_increased:
            net_verdict = RecommendationStatus.VERIFIED.value
        elif service_improved and (transport_increased or delay_increased):
            net_verdict = RecommendationStatus.MIXED.value
        elif service_degraded:
            net_verdict = RecommendationStatus.REJECTED.value
        else:
            net_verdict = RecommendationStatus.INCONCLUSIVE.value

        dist_val = f"{dist_d.absolute_delta:+.1f} km" if dist_d else f"{distance_km:.1f} km"
        unmet_val = f"{unmet_d.absolute_delta:+.1f} units" if unmet_d else "0 units"

        narrative = (
            f"Forward service improved ({unmet_val} unmet demand) with risk {risk_status.lower()}, "
            f"requiring an intentional operational expenditure of {dist_val} in transport distance."
        )

        return {
            "SERVICE": service_status,
            "RISK": risk_status,
            "TRANSPORT_COST": transport_status,
            "DELAY": delay_status,
            "FLEET_UTILIZATION": fleet_status,
            "NET_RESULT": net_verdict,
            "narrative": narrative,
        }
