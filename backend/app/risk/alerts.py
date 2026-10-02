"""Early Warning Engine for PRAVAH Logistics Intelligence.

Evaluates multi-echelon telemetry against deterministic thresholds to trigger
structured, actionable operational alerts with full audit evidence.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from backend.app.risk.explanations import ExplanationEngine


@dataclass
class Alert:
    alert_id: str
    severity: str  # INFO, WARNING, HIGH, CRITICAL
    node_id: str
    node_code: str
    item: str
    alert_type: str
    time_horizon_hours: Optional[int]
    probability: Optional[float]
    causes: List[str]
    evidence: Dict[str, Any]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "severity": self.severity,
            "node_id": self.node_id,
            "node_code": self.node_code,
            "item": self.item,
            "alert_type": self.alert_type,
            "time_horizon_hours": self.time_horizon_hours,
            "probability": round(self.probability, 3) if self.probability is not None else None,
            "causes": self.causes,
            "evidence": self.evidence,
            "explanation": self.explanation,
        }


class EarlyWarningEngine:
    """Detects impending supply chain failures and emits structured alerts."""

    def __init__(self):
        self.explanation_engine = ExplanationEngine()
        self.alert_counter = 0

    def evaluate_inventory_alerts(
        self,
        node_id: str,
        node_code: str,
        item: str,
        current_inventory: float,
        safety_stock: float,
        time_to_ss_hours: Optional[int],
        time_to_zero_hours: Optional[int],
        stockout_prob: float,
        p95_cumulative_demand: float,
        lead_time_hours: float = 24.0,
        route_status: str = "AVAILABLE",
        weather_severity: str = "NORMAL",
        demand_surge_percent: float = 0.0,
    ) -> List[Alert]:
        """Scans inventory projection outputs and triggers threshold-based alerts."""
        alerts = []

        # 1. Critical Stockout Imminent (Time to zero <= lead time OR stockout prob >= 0.50)
        if (time_to_zero_hours is not None and time_to_zero_hours <= lead_time_hours * 1.5) or stockout_prob >= 0.50:
            self.alert_counter += 1
            expl = self.explanation_engine.explain_stockout_risk(
                node_code=node_code,
                item=item,
                current_inventory=current_inventory,
                safety_stock=safety_stock,
                time_to_ss_hours=time_to_ss_hours,
                time_to_zero_hours=time_to_zero_hours,
                stockout_prob=stockout_prob,
                route_status=route_status,
                weather_severity=weather_severity,
                demand_surge_percent=demand_surge_percent,
            )
            alerts.append(
                Alert(
                    alert_id=f"ALT_CRIT_{self.alert_counter:04d}",
                    severity="CRITICAL",
                    node_id=node_id,
                    node_code=node_code,
                    item=item,
                    alert_type="CRITICAL_STOCKOUT_IMMINENT",
                    time_horizon_hours=time_to_zero_hours,
                    probability=stockout_prob,
                    causes=["Zero stock trajectory within operational replenishment lead-time window"],
                    evidence={
                        "current_inventory": current_inventory,
                        "dynamic_safety_stock": safety_stock,
                        "time_to_zero_hours": time_to_zero_hours,
                        "lead_time_hours": lead_time_hours,
                        "stockout_probability": stockout_prob,
                    },
                    explanation=expl,
                )
            )

        # 2. Safety Stock Breach (time_to_ss <= lead_time)
        elif (time_to_ss_hours is not None and time_to_ss_hours <= lead_time_hours * 1.25) or (current_inventory < safety_stock):
            self.alert_counter += 1
            expl = self.explanation_engine.explain_stockout_risk(
                node_code=node_code,
                item=item,
                current_inventory=current_inventory,
                safety_stock=safety_stock,
                time_to_ss_hours=time_to_ss_hours,
                time_to_zero_hours=time_to_zero_hours,
                stockout_prob=stockout_prob,
                route_status=route_status,
                weather_severity=weather_severity,
                demand_surge_percent=demand_surge_percent,
            )
            alerts.append(
                Alert(
                    alert_id=f"ALT_WARN_{self.alert_counter:04d}",
                    severity="HIGH",
                    node_id=node_id,
                    node_code=node_code,
                    item=item,
                    alert_type="SAFETY_STOCK_BREACH",
                    time_horizon_hours=time_to_ss_hours,
                    probability=stockout_prob,
                    causes=["Stock level projected to breach required dynamic safety buffer"],
                    evidence={
                        "current_inventory": current_inventory,
                        "safety_stock": safety_stock,
                        "time_to_safety_stock_hours": time_to_ss_hours,
                    },
                    explanation=expl,
                )
            )

        # 3. P95 Stress Deficit (available inventory cannot cover P95 high-demand scenario)
        if current_inventory < p95_cumulative_demand and stockout_prob > 0.15:
            self.alert_counter += 1
            alerts.append(
                Alert(
                    alert_id=f"ALT_STRESS_{self.alert_counter:04d}",
                    severity="WARNING",
                    node_id=node_id,
                    node_code=node_code,
                    item=item,
                    alert_type="P95_SURGE_DEFICIT",
                    time_horizon_hours=int(lead_time_hours),
                    probability=stockout_prob,
                    causes=["High-percentile (P95) surge demand exceeds on-hand reserves"],
                    evidence={
                        "on_hand": current_inventory,
                        "p95_cumulative_demand": round(p95_cumulative_demand, 1),
                        "shortfall": round(p95_cumulative_demand - current_inventory, 1),
                    },
                    explanation=(
                        f"Under a P95 surge demand scenario, {node_code} faces a deficit of "
                        f"{p95_cumulative_demand - current_inventory:,.0f} units of {item} unless reinforced."
                    ),
                )
            )

        return alerts

    def evaluate_route_alerts(
        self,
        route_id: str,
        route_code: str,
        source_code: str,
        dest_code: str,
        status: str,
        weather_severity: str,
        dependency_factor: float,
    ) -> List[Alert]:
        """Emits route impediment alerts based on route status and supply dependency."""
        alerts = []
        if status == "BLOCKED" and dependency_factor > 0.25:
            self.alert_counter += 1
            alerts.append(
                Alert(
                    alert_id=f"ALT_ROUTE_{self.alert_counter:04d}",
                    severity="CRITICAL" if dependency_factor > 0.50 else "HIGH",
                    node_id=dest_code,
                    node_code=dest_code,
                    item="ALL_SUPPLIES",
                    alert_type="SUPPLY_CORRIDOR_BLOCKED",
                    time_horizon_hours=0,
                    probability=1.0,
                    causes=[f"Route {route_code} blocked; supplies {dependency_factor*100:.0f}% of inbound throughput"],
                    evidence={
                        "route_id": route_id,
                        "route_code": route_code,
                        "source": source_code,
                        "destination": dest_code,
                        "dependency": dependency_factor,
                    },
                    explanation=(
                        f"Supply corridor {route_code} from {source_code} to {dest_code} is BLOCKED. "
                        f"This route provides {dependency_factor*100:.0f}% of inbound supply to {dest_code}."
                    ),
                )
            )
        elif weather_severity == "SEVERE":
            self.alert_counter += 1
            alerts.append(
                Alert(
                    alert_id=f"ALT_WX_{self.alert_counter:04d}",
                    severity="WARNING",
                    node_id=dest_code,
                    node_code=dest_code,
                    item="TRANSPORT",
                    alert_type="SEVERE_WEATHER_ALERT",
                    time_horizon_hours=12,
                    probability=0.85,
                    causes=["Severe blizzard conditions degrading transit pass speed"],
                    evidence={"route_code": route_code, "weather_severity": weather_severity},
                    explanation=f"Severe blizzard over corridor {route_code} will significantly slow convoy movements to {dest_code}.",
                )
            )

        return alerts
