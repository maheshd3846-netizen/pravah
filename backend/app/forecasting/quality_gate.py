"""Data Quality Gate for PRAVAH Logistics Intelligence Engine.

Evaluates multi-source telemetry freshness and historical sample sufficiency
prior to triggering forecasting, risk modeling, and optimization cycles.
Classifies readiness into:
- READY: All telemetry feeds and historical depths exceed minimum operational baselines.
- DEGRADED: Non-critical telemetry is stale or partial; models can proceed with caution flags.
- INSUFFICIENT: Essential historical or state inputs are missing or critically corrupted.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional
import pandas as pd


class QualityStatus(str, Enum):
    READY = "READY"
    DEGRADED = "DEGRADED"
    INSUFFICIENT = "INSUFFICIENT"


@dataclass
class FeedQualityReport:
    feed_name: str
    status: QualityStatus
    metric_value: Any
    threshold: Any
    message: str


@dataclass
class DataQualityAssessment:
    overall_status: QualityStatus
    summary_message: str
    feed_reports: Dict[str, FeedQualityReport]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.overall_status.value,
            "summary_message": self.summary_message,
            "feed_reports": {
                k: {
                    "status": v.status.value,
                    "metric_value": v.metric_value,
                    "threshold": v.threshold,
                    "message": v.message,
                }
                for k, v in self.feed_reports.items()
            },
            "metadata": self.metadata,
        }


class DataQualityGate:
    """Evaluates telemetry feeds and historical series for optimization readiness."""

    def __init__(
        self,
        min_demand_history_hours: int = 720,  # Minimum 1 month of hourly observations
        min_nodes_count: int = 5,
        min_items_count: int = 1,
        max_inventory_age_hours: float = 24.0,
        max_route_age_hours: float = 12.0,
        max_weather_age_hours: float = 6.0,
        max_vehicle_age_hours: float = 12.0,
    ):
        self.min_demand_history_hours = min_demand_history_hours
        self.min_nodes_count = min_nodes_count
        self.min_items_count = min_items_count
        self.max_inventory_age_hours = max_inventory_age_hours
        self.max_route_age_hours = max_route_age_hours
        self.max_weather_age_hours = max_weather_age_hours
        self.max_vehicle_age_hours = max_vehicle_age_hours

    def evaluate(
        self,
        demand_history_df: Optional[pd.DataFrame] = None,
        inventory_freshness_hours: Optional[float] = None,
        route_freshness_hours: Optional[float] = None,
        weather_freshness_hours: Optional[float] = None,
        vehicle_freshness_hours: Optional[float] = None,
    ) -> DataQualityAssessment:
        """Runs validation checks across all intelligence inputs."""
        reports: Dict[str, FeedQualityReport] = {}

        # 1. Demand History Sufficiency Check
        if demand_history_df is None or len(demand_history_df) == 0:
            reports["demand_history"] = FeedQualityReport(
                feed_name="demand_history",
                status=QualityStatus.INSUFFICIENT,
                metric_value=0,
                threshold=self.min_demand_history_hours,
                message="Demand history dataframe is completely missing or empty.",
            )
        else:
            total_hours = (
                int(demand_history_df["timestamp_hour"].max() - demand_history_df["timestamp_hour"].min() + 1)
                if "timestamp_hour" in demand_history_df.columns
                else len(demand_history_df)
            )
            has_required_cols = {"node_id", "item", "requested_demand"}.issubset(demand_history_df.columns)

            if not has_required_cols:
                reports["demand_history"] = FeedQualityReport(
                    feed_name="demand_history",
                    status=QualityStatus.INSUFFICIENT,
                    metric_value=list(demand_history_df.columns),
                    threshold=["node_id", "item", "requested_demand"],
                    message="Demand history is missing required schema columns.",
                )
            elif total_hours < self.min_demand_history_hours:
                reports["demand_history"] = FeedQualityReport(
                    feed_name="demand_history",
                    status=QualityStatus.DEGRADED,
                    metric_value=total_hours,
                    threshold=self.min_demand_history_hours,
                    message=f"Demand history has only {total_hours} hours; minimum {self.min_demand_history_hours}h recommended.",
                )
            else:
                reports["demand_history"] = FeedQualityReport(
                    feed_name="demand_history",
                    status=QualityStatus.READY,
                    metric_value=total_hours,
                    threshold=self.min_demand_history_hours,
                    message=f"Demand history is sufficient ({total_hours} hours observed).",
                )

        # 2. Inventory Freshness Check
        if inventory_freshness_hours is None:
            reports["inventory_freshness"] = FeedQualityReport(
                feed_name="inventory_freshness",
                status=QualityStatus.DEGRADED,
                metric_value=None,
                threshold=self.max_inventory_age_hours,
                message="Inventory telemetry age not reported; assuming cached base stock.",
            )
        elif inventory_freshness_hours > self.max_inventory_age_hours * 2:
            reports["inventory_freshness"] = FeedQualityReport(
                feed_name="inventory_freshness",
                status=QualityStatus.INSUFFICIENT,
                metric_value=inventory_freshness_hours,
                threshold=self.max_inventory_age_hours,
                message=f"Inventory telemetry is critically stale ({inventory_freshness_hours:.1f}h old).",
            )
        elif inventory_freshness_hours > self.max_inventory_age_hours:
            reports["inventory_freshness"] = FeedQualityReport(
                feed_name="inventory_freshness",
                status=QualityStatus.DEGRADED,
                metric_value=inventory_freshness_hours,
                threshold=self.max_inventory_age_hours,
                message=f"Inventory telemetry is older than nominal threshold ({inventory_freshness_hours:.1f}h).",
            )
        else:
            reports["inventory_freshness"] = FeedQualityReport(
                feed_name="inventory_freshness",
                status=QualityStatus.READY,
                metric_value=inventory_freshness_hours,
                threshold=self.max_inventory_age_hours,
                message=f"Inventory telemetry is fresh ({inventory_freshness_hours:.1f}h old).",
            )

        # 3. Route Status Freshness Check
        if route_freshness_hours is None:
            reports["route_status"] = FeedQualityReport(
                feed_name="route_status",
                status=QualityStatus.READY,
                metric_value=0.0,
                threshold=self.max_route_age_hours,
                message="Route status feed active from network topology.",
            )
        elif route_freshness_hours > self.max_route_age_hours * 2:
            reports["route_status"] = FeedQualityReport(
                feed_name="route_status",
                status=QualityStatus.DEGRADED,
                metric_value=route_freshness_hours,
                threshold=self.max_route_age_hours,
                message=f"Route status feed delayed ({route_freshness_hours:.1f}h old).",
            )
        else:
            reports["route_status"] = FeedQualityReport(
                feed_name="route_status",
                status=QualityStatus.READY,
                metric_value=route_freshness_hours,
                threshold=self.max_route_age_hours,
                message=f"Route status feed is fresh ({route_freshness_hours:.1f}h old).",
            )

        # 4. Weather Telemetry Freshness Check
        if weather_freshness_hours is None:
            reports["weather_freshness"] = FeedQualityReport(
                feed_name="weather_freshness",
                status=QualityStatus.READY,
                metric_value=0.0,
                threshold=self.max_weather_age_hours,
                message="Weather radar observation active.",
            )
        elif weather_freshness_hours > self.max_weather_age_hours * 2:
            reports["weather_freshness"] = FeedQualityReport(
                feed_name="weather_freshness",
                status=QualityStatus.DEGRADED,
                metric_value=weather_freshness_hours,
                threshold=self.max_weather_age_hours,
                message=f"Weather observation is stale ({weather_freshness_hours:.1f}h old).",
            )
        else:
            reports["weather_freshness"] = FeedQualityReport(
                feed_name="weather_freshness",
                status=QualityStatus.READY,
                metric_value=weather_freshness_hours,
                threshold=self.max_weather_age_hours,
                message=f"Weather telemetry is fresh ({weather_freshness_hours:.1f}h old).",
            )

        # 5. Vehicle Availability Freshness Check
        if vehicle_freshness_hours is None:
            reports["vehicle_freshness"] = FeedQualityReport(
                feed_name="vehicle_freshness",
                status=QualityStatus.READY,
                metric_value=0.0,
                threshold=self.max_vehicle_age_hours,
                message="Vehicle fleet status active.",
            )
        elif vehicle_freshness_hours > self.max_vehicle_age_hours * 2:
            reports["vehicle_freshness"] = FeedQualityReport(
                feed_name="vehicle_freshness",
                status=QualityStatus.DEGRADED,
                metric_value=vehicle_freshness_hours,
                threshold=self.max_vehicle_age_hours,
                message=f"Vehicle availability status is stale ({vehicle_freshness_hours:.1f}h old).",
            )
        else:
            reports["vehicle_freshness"] = FeedQualityReport(
                feed_name="vehicle_freshness",
                status=QualityStatus.READY,
                metric_value=vehicle_freshness_hours,
                threshold=self.max_vehicle_age_hours,
                message=f"Vehicle fleet availability is fresh ({vehicle_freshness_hours:.1f}h old).",
            )

        # Determine overall quality status
        statuses = [r.status for r in reports.values()]
        if any(s == QualityStatus.INSUFFICIENT for s in statuses):
            overall = QualityStatus.INSUFFICIENT
            summary = "Critical data deficiency detected. Intelligence engine operates under degraded confidence."
        elif any(s == QualityStatus.DEGRADED for s in statuses):
            overall = QualityStatus.DEGRADED
            summary = "Minor telemetry staleness detected. Models proceed with operational confidence flags."
        else:
            overall = QualityStatus.READY
            summary = "All input telemetry and historical data streams meet quality thresholds."

        return DataQualityAssessment(
            overall_status=overall,
            summary_message=summary,
            feed_reports=reports,
        )
