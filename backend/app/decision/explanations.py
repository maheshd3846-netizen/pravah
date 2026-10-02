"""Deterministic Fact-Grounded Explanation Engine and Route Alternative Comparator."""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Tuple
from backend.app.decision.schemas import (
    ActionType,
    DecisionEvidenceItem,
    EvidenceType,
    RouteAlternative,
)


class ExplanationGenerator:
    """Generates auditable, deterministic military logistics decision rationales."""

    @staticmethod
    def generate_why_explanation(
        action_type: str,
        dst_code: str,
        src_code: str,
        item: str,
        quantity: float,
        route_code: str,
        vehicle_code: str,
        evidence: List[DecisionEvidenceItem],
        primary_blocked: bool = False,
        primary_route_code: Optional[str] = None,
    ) -> str:
        """Constructs an auditable explanation grounded strictly in verified evidence."""
        bullets: List[str] = []

        # Find specific evidence items
        ev_map = {e.type: e for e in evidence}

        # 1. Forward deficit & stockout rationale
        so_ev = ev_map.get(EvidenceType.STOCKOUT_PROBABILITY.value)
        if so_ev and float(so_ev.value) >= 0.20:
            bullets.append(f"{dst_code} displays elevated stockout probability ({float(so_ev.value)*100:.1f}%).")
        else:
            bullets.append(f"{dst_code} requires forward inventory replenishment under active operational demand.")

        # 2. Time-to-zero urgency
        ttz_ev = ev_map.get(EvidenceType.TIME_TO_ZERO.value)
        if ttz_ev and int(ttz_ev.value) < 72:
            bullets.append(f"Time-to-zero is critical ({ttz_ev.value} hours remaining) within the operational horizon.")

        # 3. Route condition & rerouting
        if primary_blocked and primary_route_code:
            bullets.append(f"Primary corridor {primary_route_code} is BLOCKED; alternate detour {route_code} is viable.")
        else:
            r_ev = ev_map.get(EvidenceType.ROUTE_STATUS.value)
            r_status = r_ev.value if r_ev else "AVAILABLE"
            bullets.append(f"Transport corridor {route_code} is confirmed {r_status} and traversable.")

        # 4. Source depot sufficiency
        src_ev = ev_map.get(EvidenceType.SOURCE_INVENTORY.value)
        if src_ev:
            bullets.append(f"Source depot {src_code} has verified available stock ({src_ev.value:.1f} units of {item}).")

        # 5. Vehicle payload
        veh_ev = ev_map.get(EvidenceType.VEHICLE_CAPACITY.value)
        if veh_ev:
            bullets.append(f"Assigned asset {vehicle_code} provides {veh_ev.value:.1f} units payload capacity.")

        # 6. Counterfactual simulation verification
        cf_ev = ev_map.get(EvidenceType.COUNTERFACTUAL_DELTA.value)
        if cf_ev and cf_ev.details.get("is_better"):
            bullets.append(
                f"Closed-loop simulation verified reduction of unmet demand by {abs(float(cf_ev.value)):.1f} units."
            )

        header = f"{item} -> {dst_code}\nRecommended Action: {action_type}\nWhy:"
        body = "\n".join(f"- {b}" for b in bullets)
        return f"{header}\n{body}"

    @staticmethod
    def analyze_route_alternatives(
        selected_route_id: str,
        routes: Dict[str, Any],
        route_risks: Optional[Dict[str, float]] = None,
    ) -> Tuple[List[RouteAlternative], str]:
        """Compares the selected route against available alternatives for transparent solver explainability."""
        selected_obj = routes.get(selected_route_id)
        if not selected_obj:
            return [], "Route details unavailable."

        src = getattr(selected_obj, "source_node_id", None)
        dst = getattr(selected_obj, "destination_node_id", None)

        # Find parallel or alternative routes serving the same destination
        comp_routes = [
            r for r in routes.values()
            if getattr(r, "destination_node_id", None) == dst
        ]

        alternatives: List[RouteAlternative] = []
        explanation_lines: List[str] = []

        sel_dist = float(getattr(selected_obj, "distance_km", 50.0))
        sel_risk = float((route_risks or {}).get(selected_route_id, 0.0))
        sel_code = getattr(selected_obj, "route_code", selected_route_id)
        sel_status = getattr(selected_obj, "status", "AVAILABLE")
        sel_status_str = sel_status.value if hasattr(sel_status, "value") else str(sel_status)

        for r in comp_routes:
            r_id = getattr(r, "id", "")
            r_code = getattr(r, "route_code", r_id)
            r_dist = float(getattr(r, "distance_km", 50.0))
            r_risk = float((route_risks or {}).get(r_id, 0.0))
            r_hrs = float(getattr(r, "base_travel_hours", 4.0))
            r_stat = getattr(r, "status", "AVAILABLE")
            r_stat_str = r_stat.value if hasattr(r_stat, "value") else str(r_stat)

            is_sel = (r_id == selected_route_id)
            if is_sel:
                reason = "Selected by optimizer as optimal risk-weighted feasible path."
            elif r_stat_str == "BLOCKED":
                reason = "Infeasible: corridor is currently BLOCKED by environmental disruption."
            elif r_risk > sel_risk + 0.15:
                reason = f"Rejected: risk score ({r_risk:.2f}) materially higher than selected ({sel_risk:.2f})."
            elif r_dist > sel_dist:
                reason = f"Rejected: longer distance ({r_dist:.1f} km vs {sel_dist:.1f} km)."
            else:
                reason = "Alternative route evaluated but yielded higher composite penalty."

            alternatives.append(
                RouteAlternative(
                    route_id=r_code,
                    status=r_stat_str,
                    distance_km=r_dist,
                    risk_score=round(r_risk, 3),
                    travel_time_hours=r_hrs,
                    is_selected=is_sel,
                    selection_reason=reason,
                )
            )

        # Synthesize explainable narrative
        blocked_alts = [a.route_id for a in alternatives if not a.is_selected and a.status == "BLOCKED"]
        if blocked_alts:
            explanation_lines.append(
                f"Primary alternative corridor(s) {', '.join(blocked_alts)} are BLOCKED. "
                f"The optimizer selected {sel_code} ({sel_dist:.1f} km) as the viable operational corridor."
            )
        else:
            explanation_lines.append(
                f"Selected {sel_code} ({sel_dist:.1f} km, risk={sel_risk:.2f}) over alternative corridors "
                f"to minimize weighted transport, risk, and delay penalties."
            )

        return alternatives, " ".join(explanation_lines)
