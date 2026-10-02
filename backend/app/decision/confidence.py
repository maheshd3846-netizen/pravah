"""Evidence-Derived Confidence Scoring and Data Quality Gating."""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Tuple
from backend.app.decision.schemas import (
    ConfidenceLevel,
    DataQualityState,
    DecisionConfidence,
    RecommendationStatus,
)


class ConfidenceScorer:
    """Evaluates measurable empirical conditions to rate recommendation confidence."""

    @staticmethod
    def evaluate_confidence(
        data_quality: str = DataQualityState.READY.value,
        has_sufficient_source_inventory: bool = True,
        is_route_open: bool = True,
        is_vehicle_available: bool = True,
        optimization_feasible: bool = True,
        counterfactual_verified: bool = False,
    ) -> Tuple[DecisionConfidence, Optional[str]]:
        """Calculates evidence-grounded confidence without heuristic fabrication."""
        factors: List[str] = []
        score = 0.0

        # 1. Telemetry Data Quality Gate
        dq_upper = data_quality.upper()
        if dq_upper == DataQualityState.READY.value:
            score += 0.25
            factors.append("Sensor and supply telemetry confirmed READY.")
        elif dq_upper == DataQualityState.DEGRADED.value:
            score += 0.10
            factors.append("Telemetry operates in DEGRADED mode; confidence capped at MEDIUM.")
        else:
            factors.append("Data quality INSUFFICIENT; telemetry integrity compromised.")

        # 2. Source Inventory Freshness and Sufficiency
        if has_sufficient_source_inventory:
            score += 0.20
            factors.append("Depot source inventory verified sufficient for planned volume.")
        else:
            factors.append("Depot inventory balance insufficient or unverified.")

        # 3. Route Status Viability
        if is_route_open:
            score += 0.20
            factors.append("Transportation corridor confirmed open and traversable.")
        else:
            factors.append("Assigned route blocked or subjected to active hazard.")

        # 4. Fleet Asset Availability & Capacity
        if is_vehicle_available:
            score += 0.15
            factors.append("Assigned transport asset verified AVAILABLE within payload rating.")
        else:
            factors.append("Vehicle asset unavailable or payload rating exceeded.")

        # 5. Optimization & Counterfactual Simulation Verification
        if optimization_feasible:
            score += 0.05
            factors.append("Mathematical allocation satisfied all linear constraints.")

        if counterfactual_verified:
            score += 0.15
            factors.append("Closed-loop counterfactual simulation verified positive operational effect.")

        # Enforce Hard Data-Quality Constraints
        score = round(min(1.0, score), 2)
        forced_status_override: Optional[str] = None

        if dq_upper == DataQualityState.INSUFFICIENT.value:
            level = ConfidenceLevel.LOW.value
            forced_status_override = RecommendationStatus.INCONCLUSIVE.value
        elif dq_upper == DataQualityState.DEGRADED.value:
            level = ConfidenceLevel.MEDIUM.value if score >= 0.50 else ConfidenceLevel.LOW.value
        else:
            if score >= 0.80 and counterfactual_verified:
                level = ConfidenceLevel.HIGH.value
            elif score >= 0.50:
                level = ConfidenceLevel.MEDIUM.value
            else:
                level = ConfidenceLevel.LOW.value

        confidence = DecisionConfidence(
            level=level,
            score=score,
            factors=factors,
        )
        return confidence, forced_status_override
