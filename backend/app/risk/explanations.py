"""Deterministic Fact-Grounded Explanation Engine for Logistics Intelligence.

Synthesizes clear, factual operational explanations strictly from computed metrics
and observed disruptions without hallucination or LLM dependency.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional


class ExplanationEngine:
    """Generates deterministic natural language summaries grounded strictly in calculated values."""

    def explain_stockout_risk(
        self,
        node_code: str,
        item: str,
        current_inventory: float,
        safety_stock: float,
        time_to_ss_hours: Optional[int],
        time_to_zero_hours: Optional[int],
        stockout_prob: float,
        route_status: str = "AVAILABLE",
        weather_severity: str = "NORMAL",
        demand_surge_percent: float = 0.0,
    ) -> str:
        """Constructs an explanatory diagnostic text grounded in real physical states."""
        parts = []

        # 1. Primary finding
        if time_to_zero_hours is not None and time_to_zero_hours <= 48:
            parts.append(
                f"{item} at {node_code} is projected to suffer complete inventory depletion (time-to-zero) in {time_to_zero_hours} hours."
            )
        elif time_to_ss_hours is not None:
            parts.append(
                f"{item} at {node_code} is projected to breach dynamic safety stock ({safety_stock:,.0f} units) within {time_to_ss_hours} hours."
            )
        else:
            parts.append(
                f"{item} at {node_code} maintains stable inventory above safety threshold ({current_inventory:,.0f} units on hand)."
            )

        # 2. Logistics drivers
        driver_clauses = []
        if route_status == "BLOCKED":
            driver_clauses.append("the primary supply corridor is BLOCKED, halting regular dispatches")
        elif route_status == "DEGRADED":
            driver_clauses.append("the primary inbound route is DEGRADED, increasing convoy transit duration by up to 80%")

        if weather_severity in ["MODERATE", "SEVERE"]:
            driver_clauses.append(f"adverse {weather_severity} weather is degrading pass accessibility")

        if demand_surge_percent > 5.0:
            driver_clauses.append(f"forward consumption is surging +{demand_surge_percent:.0f}% above baseline")

        if driver_clauses:
            parts.append("Root causes: " + "; ".join(driver_clauses) + ".")

        # 3. Probability & impact
        if stockout_prob > 0.05:
            parts.append(f"Monte Carlo stress analysis indicates a {stockout_prob * 100:.1f}% risk of stockout over the evaluation horizon.")

        return " ".join(parts)

    def explain_route_risk(
        self,
        route_code: str,
        source_name: str,
        dest_name: str,
        status: str,
        weather_severity: str,
        effective_hours: float,
        base_hours: float,
    ) -> str:
        """Explains route impediment and transit inflation."""
        if status == "BLOCKED":
            return (
                f"Route {route_code} ({source_name} -> {dest_name}) is impassable (BLOCKED). "
                f"Traffic must be rerouted through alternate secondary passes."
            )
        delay_pct = round(((effective_hours - base_hours) / max(0.1, base_hours)) * 100.0, 1)
        if delay_pct > 10.0:
            return (
                f"Route {route_code} transit time has inflated from {base_hours:.1f}h to {effective_hours:.1f}h "
                f"(+{delay_pct}% delay) due to {weather_severity} weather conditions and terrain impedance."
            )
        return f"Route {route_code} is fully operational under normal conditions ({base_hours:.1f}h transit)."
