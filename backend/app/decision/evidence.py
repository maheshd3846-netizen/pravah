"""Evidence Extraction and Traceability Engine for Operational Recommendations."""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from backend.app.decision.schemas import DecisionEvidenceItem, EvidenceType


class EvidenceBuilder:
    """Extracts, formats, and validates atomic operational facts from PRAVAH pipeline layers."""

    @staticmethod
    def build_decision_evidence(
        dst_node: Any,
        src_node: Any,
        route: Any,
        vehicle: Any,
        item: str,
        quantity: float,
        risk_assessment: Optional[Any] = None,
        inventory_projection: Optional[Dict[str, Any]] = None,
        counterfactual_eval: Optional[Any] = None,
        weather: Optional[Any] = None,
    ) -> List[DecisionEvidenceItem]:
        """Constructs auditable evidence items linked directly to system states."""
        evidence: List[DecisionEvidenceItem] = []

        # 1. Stockout Probability Evidence
        stockout_prob = 0.05
        if inventory_projection and "stockout_probability" in inventory_projection:
            stockout_prob = float(inventory_projection["stockout_probability"])
        elif risk_assessment and hasattr(risk_assessment, "raw_indicators"):
            stockout_prob = float(risk_assessment.raw_indicators.get("stockout_probability", 0.05))
        elif risk_assessment and isinstance(risk_assessment, dict):
            stockout_prob = float(risk_assessment.get("raw_indicators", {}).get("stockout_probability", 0.05))

        evidence.append(
            DecisionEvidenceItem(
                type=EvidenceType.STOCKOUT_PROBABILITY.value,
                value=round(stockout_prob, 3),
                source="Phase 2 Monte Carlo Engine",
                description=f"Predicted forward stockout probability is {stockout_prob*100:.1f}%.",
                details={"threshold": 0.35, "is_critical": stockout_prob >= 0.50},
            )
        )

        # 2. Time-to-Zero Evidence
        ttz = None
        if inventory_projection and "time_to_zero_hours" in inventory_projection:
            ttz = inventory_projection["time_to_zero_hours"]
        elif risk_assessment and hasattr(risk_assessment, "raw_indicators"):
            ttz = risk_assessment.raw_indicators.get("time_to_zero_hours")
        elif risk_assessment and isinstance(risk_assessment, dict):
            ttz = risk_assessment.get("raw_indicators", {}).get("time_to_zero_hours")

        ttz_val = ttz if ttz is not None else 72
        evidence.append(
            DecisionEvidenceItem(
                type=EvidenceType.TIME_TO_ZERO.value,
                value=ttz_val,
                source="Inventory Projection Model",
                description=f"Forward stock will exhaust completely in {ttz_val} hours without replenishment.",
                details={"unit": "hours", "planning_horizon": 72},
            )
        )

        # 3. Route Status & Operational Viability
        r_status = getattr(route, "status", route.get("status", "AVAILABLE") if isinstance(route, dict) else "AVAILABLE")
        r_id = getattr(route, "route_code", getattr(route, "id", "ROUTE"))
        r_dist = float(getattr(route, "distance_km", route.get("distance_km", 50.0) if isinstance(route, dict) else 50.0))
        r_status_str = r_status.value if hasattr(r_status, "value") else str(r_status)

        evidence.append(
            DecisionEvidenceItem(
                type=EvidenceType.ROUTE_STATUS.value,
                value=r_status_str,
                source="Network State Registry",
                description=f"Selected route {r_id} ({r_dist:.1f} km) status is {r_status_str}.",
                details={"route_id": r_id, "distance_km": r_dist, "is_open": r_status_str != "BLOCKED"},
            )
        )

        # 4. Source Depot Stock Availability
        init_inv = getattr(src_node, "initial_inventory", src_node.get("initial_inventory", {}) if isinstance(src_node, dict) else {})
        src_stock = float(init_inv.get(item, 5000.0))
        evidence.append(
            DecisionEvidenceItem(
                type=EvidenceType.SOURCE_INVENTORY.value,
                value=round(src_stock, 1),
                source="Supply Depot Inventory Balance",
                description=f"Source depot has {src_stock:.1f} units of {item} available (planned: {quantity:.1f}).",
                details={"item": item, "requested_quantity": quantity, "sufficient": src_stock >= quantity},
            )
        )

        # 5. Vehicle Payload Feasibility
        v_cap = float(getattr(vehicle, "capacity", vehicle.get("capacity", 5000.0) if isinstance(vehicle, dict) else 5000.0))
        v_code = getattr(vehicle, "vehicle_code", getattr(vehicle, "id", "VEHICLE"))
        evidence.append(
            DecisionEvidenceItem(
                type=EvidenceType.VEHICLE_CAPACITY.value,
                value=round(v_cap, 1),
                source="Fleet Asset Registry",
                description=f"Assigned vehicle {v_code} has payload capacity of {v_cap:.1f} units (dispatch: {quantity:.1f}).",
                details={"vehicle_id": v_code, "capacity_sufficient": v_cap >= quantity},
            )
        )

        # 6. Counterfactual Verification Evidence (if evaluation available)
        if counterfactual_eval and hasattr(counterfactual_eval, "deltas"):
            deltas = counterfactual_eval.deltas
            unmet_d = deltas.get("unmet_demand")
            if unmet_d:
                evidence.append(
                    DecisionEvidenceItem(
                        type=EvidenceType.COUNTERFACTUAL_DELTA.value,
                        value=round(unmet_d.absolute_delta, 1),
                        source="Phase 3B Closed-Loop Simulation",
                        description=f"Simulation verifies unmet demand changed by {unmet_d.absolute_delta:+.1f} units ({unmet_d.direction.value}).",
                        details={
                            "relative_percent": round(unmet_d.relative_delta_percent, 2),
                            "direction": unmet_d.direction.value,
                            "is_better": unmet_d.is_better,
                        },
                    )
                )

        return evidence
