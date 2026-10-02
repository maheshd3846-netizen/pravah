"""Risk Engine for PRAVAH Tactical Logistics.

Calculates normalized risk components [0, 1] across Inventory, Demand, Route,
Transport, and Environment. Combines them using configurable weights into an
overall risk score and categorical threat level.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import numpy as np


@dataclass
class RiskWeightsConfig:
    """Configurable risk weights summing to exactly 1.0."""
    inventory_weight: float = 0.35
    demand_weight: float = 0.20
    route_weight: float = 0.20
    transport_weight: float = 0.15
    environment_weight: float = 0.10

    def __post_init__(self):
        total = (
            self.inventory_weight
            + self.demand_weight
            + self.route_weight
            + self.transport_weight
            + self.environment_weight
        )
        if abs(total - 1.0) > 1e-4:
            raise ValueError(f"Risk weights must sum to 1.0, got {total}")

    def to_dict(self) -> Dict[str, float]:
        return {
            "inventory": self.inventory_weight,
            "demand": self.demand_weight,
            "route": self.route_weight,
            "transport": self.transport_weight,
            "environment": self.environment_weight,
        }


@dataclass
class RiskThresholdsConfig:
    """Configurable categorical risk thresholds."""
    low_cutoff: float = 0.35
    moderate_cutoff: float = 0.60
    high_cutoff: float = 0.75


@dataclass
class NodeRiskAssessment:
    node_id: str
    node_code: str
    overall_risk: float
    level: str  # LOW, MODERATE, HIGH, CRITICAL
    components: Dict[str, float]
    raw_indicators: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_code": self.node_code,
            "overall_risk": round(self.overall_risk, 3),
            "level": self.level,
            "components": {k: round(v, 3) for k, v in self.components.items()},
            "raw_indicators": self.raw_indicators,
        }


class RiskEvaluator:
    """Computes multidimensional operational risks for supply nodes and routes."""

    def __init__(
        self,
        weights: Optional[RiskWeightsConfig] = None,
        thresholds: Optional[RiskThresholdsConfig] = None,
    ):
        self.weights = weights or RiskWeightsConfig()
        self.thresholds = thresholds or RiskThresholdsConfig()

    def evaluate_inventory_risk(
        self,
        stockout_probability: float,
        time_to_zero_hours: Optional[int],
        time_to_safety_stock_hours: Optional[int],
        current_inventory: float,
        safety_stock: float,
        horizon_hours: int = 168,
    ) -> float:
        """Normalized inventory risk in [0, 1]."""
        # 1. Stockout probability contribution
        prob_score = np.clip(stockout_probability, 0.0, 1.0)

        # 2. Time-to-zero score (earlier zero = higher risk)
        if time_to_zero_hours is not None:
            zero_score = np.clip(1.0 - (time_to_zero_hours / float(horizon_hours)), 0.0, 1.0)
        else:
            zero_score = 0.0

        # 3. Buffer ratio: inventory / safety_stock
        ratio = current_inventory / max(1.0, safety_stock)
        if ratio < 1.0:
            buffer_score = np.clip(1.0 - ratio, 0.0, 1.0)
        else:
            buffer_score = 0.0

        # Weighted composite inventory risk
        inv_risk = 0.45 * prob_score + 0.35 * zero_score + 0.20 * buffer_score
        return float(np.clip(inv_risk, 0.0, 1.0))

    def evaluate_demand_risk(
        self,
        demand_growth_ratio: float,  # current vs baseline (e.g. 1.30 for +30%)
        demand_volatility_cv: float,  # std / mean
        forecast_spread_ratio: float,  # (p95 - p50) / p50
    ) -> float:
        """Normalized demand risk in [0, 1]."""
        growth_score = np.clip((demand_growth_ratio - 1.0) / 0.8, 0.0, 1.0)
        vol_score = np.clip(demand_volatility_cv / 0.5, 0.0, 1.0)
        spread_score = np.clip(forecast_spread_ratio / 0.6, 0.0, 1.0)

        dem_risk = 0.40 * growth_score + 0.30 * vol_score + 0.30 * spread_score
        return float(np.clip(dem_risk, 0.0, 1.0))

    def evaluate_route_risk(
        self,
        inflow_routes_status: List[str],  # AVAILABLE, DEGRADED, BLOCKED
        alternate_routes_count: int,
        mean_route_reliability: float,
    ) -> float:
        """Normalized route vulnerability in [0, 1]."""
        if not inflow_routes_status:
            return 1.0

        blocked_count = sum(1 for s in inflow_routes_status if s == "BLOCKED")
        degraded_count = sum(1 for s in inflow_routes_status if s == "DEGRADED")
        total = len(inflow_routes_status)

        status_penalty = (blocked_count * 1.0 + degraded_count * 0.5) / float(total)

        # Alternate route scarcity score
        alt_score = 1.0 if alternate_routes_count == 0 else (0.4 if alternate_routes_count == 1 else 0.1)

        # Unreliability score
        unrel_score = 1.0 - np.clip(mean_route_reliability, 0.0, 1.0)

        route_risk = 0.50 * status_penalty + 0.30 * alt_score + 0.20 * unrel_score
        return float(np.clip(route_risk, 0.0, 1.0))

    def evaluate_transport_risk(
        self,
        vehicle_availability_ratio: float,  # 0.0 to 1.0
        active_delays_count: int,
    ) -> float:
        """Normalized transport fleet risk in [0, 1]."""
        fleet_shortage = 1.0 - np.clip(vehicle_availability_ratio, 0.0, 1.0)
        delay_score = np.clip(active_delays_count / 3.0, 0.0, 1.0)

        trans_risk = 0.65 * fleet_shortage + 0.35 * delay_score
        return float(np.clip(trans_risk, 0.0, 1.0))

    def evaluate_environment_risk(
        self,
        weather_severity: str,
        wind_speed: float,
        visibility: float,
        temperature: float,
    ) -> float:
        """Normalized environmental risk in [0, 1]."""
        severity_scores = {"NORMAL": 0.0, "LIGHT": 0.25, "MODERATE": 0.65, "SEVERE": 1.0}
        sev_score = severity_scores.get(weather_severity, 0.0)

        wind_score = np.clip((wind_speed - 25.0) / 60.0, 0.0, 1.0)
        vis_score = np.clip(1.0 - (visibility / 10.0), 0.0, 1.0)
        temp_score = np.clip(max(0.0, -10.0 - temperature) / 20.0, 0.0, 1.0)

        env_risk = 0.40 * sev_score + 0.25 * wind_score + 0.20 * vis_score + 0.15 * temp_score
        return float(np.clip(env_risk, 0.0, 1.0))

    def calculate_overall_risk(
        self,
        node_id: str,
        node_code: str,
        inventory_risk: float,
        demand_risk: float,
        route_risk: float,
        transport_risk: float,
        environment_risk: float,
        raw_indicators: Optional[Dict[str, Any]] = None,
    ) -> NodeRiskAssessment:
        """Aggregates normalized components into overall weighted score and assigns threat level."""
        overall = (
            self.weights.inventory_weight * inventory_risk
            + self.weights.demand_weight * demand_risk
            + self.weights.route_weight * route_risk
            + self.weights.transport_weight * transport_risk
            + self.weights.environment_weight * environment_risk
        )
        overall = float(np.clip(overall, 0.0, 1.0))

        if overall >= self.thresholds.high_cutoff:
            level = "CRITICAL"
        elif overall >= self.thresholds.moderate_cutoff:
            level = "HIGH"
        elif overall >= self.thresholds.low_cutoff:
            level = "MODERATE"
        else:
            level = "LOW"

        return NodeRiskAssessment(
            node_id=node_id,
            node_code=node_code,
            overall_risk=round(overall, 3),
            level=level,
            components={
                "inventory": round(inventory_risk, 3),
                "demand": round(demand_risk, 3),
                "route": round(route_risk, 3),
                "transport": round(transport_risk, 3),
                "environment": round(environment_risk, 3),
            },
            raw_indicators=raw_indicators or {},
        )
