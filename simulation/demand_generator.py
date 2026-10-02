"""Synthetic Demand Generator for PRAVAH Logistics Engine.

Generates multi-attribute hourly synthetic demand based on:
Demand = baseline * seasonality * trend * environmental_factor * operational_factor + noise.
Maintains requested, fulfilled, and unmet demand to decouple supply constraints from true demand.
"""

from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from simulation.world_generator import (
    Node,
    NodeType,
    SupplyCategory,
    WeatherState,
)


@dataclass
class HourlyDemand:
    node_id: str
    item: str
    timestamp_hour: int
    requested_demand: float
    fulfilled_demand: float = 0.0
    unmet_demand: float = 0.0

    def to_dict(self) -> Dict[str, any]:
        return {
            "node_id": self.node_id,
            "item": self.item,
            "timestamp_hour": self.timestamp_hour,
            "requested_demand": self.requested_demand,
            "fulfilled_demand": self.fulfilled_demand,
            "unmet_demand": self.unmet_demand,
        }


class DemandGenerator:
    """Generates realistic operational demand series across nodes, supply categories, and time."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = np.random.RandomState(seed)

    def _hourly_seasonality(self, item: str, hour_of_day: int) -> float:
        """Item-specific diurnal demand profile."""
        if item == SupplyCategory.FOOD.value:
            # Meal peaks at 07:00 (breakfast), 12:00 (lunch), 19:00 (dinner)
            if hour_of_day in [7, 8]:
                return 1.6
            elif hour_of_day in [12, 13]:
                return 1.8
            elif hour_of_day in [19, 20]:
                return 1.7
            elif 23 <= hour_of_day or hour_of_day <= 5:
                return 0.3
            return 0.8
        elif item == SupplyCategory.FUEL.value:
            # Heating fuel peaks in coldest night/early morning hours (21:00 - 06:00)
            if hour_of_day <= 6 or hour_of_day >= 20:
                return 1.45
            elif 11 <= hour_of_day <= 15:
                return 0.70
            return 1.05
        elif item == SupplyCategory.WATER.value:
            # Daytime activities
            if 7 <= hour_of_day <= 20:
                return 1.35
            return 0.40
        elif item == SupplyCategory.MEDICAL.value:
            # Relatively flat with daytime clinical hours
            if 9 <= hour_of_day <= 17:
                return 1.25
            return 0.75
        else:  # GENERAL_CRITICAL
            if 8 <= hour_of_day <= 18:
                return 1.30
            return 0.60

    def _weekly_seasonality(self, day_of_week: int) -> float:
        """Weekly rotation and operational cycle."""
        # Days 0-4 regular drills; day 5 equipment inspection/maintenance; day 6 replenishment prep
        weekday_weights = [1.0, 1.05, 1.0, 1.08, 1.15, 0.95, 0.90]
        return weekday_weights[day_of_week % 7]

    def _trend_factor(self, timestamp_hour: int, total_hours: int) -> float:
        """Gradual operational escalation or seasonal buildup."""
        progress = timestamp_hour / max(1.0, float(total_hours))
        # Mild 8% expansion over the period
        return 1.0 + 0.08 * progress

    def _environmental_factor(self, item: str, weather: Optional[WeatherState]) -> float:
        """Environmental drivers (e.g. extreme sub-zero cold spikes fuel consumption)."""
        if weather is None:
            return 1.0

        if item == SupplyCategory.FUEL.value:
            if weather.temperature < 0.0:
                # 3% extra fuel per degree below freezing
                return min(2.5, 1.0 + abs(weather.temperature) * 0.035)
            return 1.0
        elif item == SupplyCategory.WATER.value:
            # Freezing requires fuel to melt ice, slightly reduces direct water draw but increases heating need
            if weather.temperature < -10.0:
                return 0.85
            return 1.0
        elif item == SupplyCategory.MEDICAL.value:
            # Severe weather / blizzards increase frostbite / altitude sickness incidents
            if weather.severity.value in ["MODERATE", "SEVERE"]:
                return 1.50
            return 1.0
        return 1.0

    def calculate_hourly_demand(
        self,
        node: Node,
        item: str,
        timestamp_hour: int,
        weather: Optional[WeatherState] = None,
        operational_factor: float = 1.0,
        surge_multiplier: float = 1.0,
        total_hours: int = 8760,
    ) -> HourlyDemand:
        """Calculates exact requested demand for a node-item pair at a given hour."""
        hour_of_day = timestamp_hour % 24
        day_of_week = (timestamp_hour // 24) % 7

        # Base hourly burn rate
        # Node reorder points provide baseline daily consumption
        daily_baseline = node.reorder_point.get(item, 100.0) / max(1, node.safety_stock_days)
        base_hourly = daily_baseline / 24.0

        # Component multipliers
        s_hourly = self._hourly_seasonality(item, hour_of_day)
        s_weekly = self._weekly_seasonality(day_of_week)
        trend = self._trend_factor(timestamp_hour, total_hours)
        env = self._environmental_factor(item, weather)

        # Deterministic noise per node, item, timestamp
        uid_str = f"{node.id}_{item}_{timestamp_hour}"
        deterministic_hash = (self.seed + hash(uid_str)) % (2**31 - 1)
        step_rng = np.random.RandomState(deterministic_hash)

        # Controlled noise (~10% CV)
        noise = float(step_rng.normal(0.0, 0.08 * base_hourly))

        # Occasional operational anomaly surge (1% chance if not already surging)
        stochastic_surge = 1.35 if step_rng.rand() < 0.015 else 1.0

        total_demand = (
            base_hourly
            * s_hourly
            * s_weekly
            * trend
            * env
            * operational_factor
            * surge_multiplier
            * stochastic_surge
            + noise
        )

        requested = max(0.5, round(float(total_demand), 2))
        return HourlyDemand(
            node_id=node.id,
            item=item,
            timestamp_hour=timestamp_hour,
            requested_demand=requested,
            fulfilled_demand=0.0,
            unmet_demand=0.0,
        )

    def generate_annual_history(
        self,
        nodes: Dict[str, Node],
        months: int = 12,
    ) -> pd.DataFrame:
        """Generates full synthetic demand dataset for ML training and evaluation."""
        total_hours = months * 30 * 24  # 8640 hours
        records = []

        from simulation.weather_generator import WeatherGenerator
        weather_gen = WeatherGenerator(seed=self.seed)

        for hour in range(total_hours):
            # Sample subset of hours or compute per node to keep fast and comprehensive
            # Sample every 4 hours for long training dataset or all hours for forward posts
            if hour % 3 != 0:
                continue

            for node in nodes.values():
                weather = weather_gen.generate_weather(node, hour)
                for item in SupplyCategory:
                    demand_obj = self.calculate_hourly_demand(
                        node=node,
                        item=item.value,
                        timestamp_hour=hour,
                        weather=weather,
                        total_hours=total_hours,
                    )
                    records.append({
                        "node_id": node.id,
                        "node_code": node.code,
                        "node_type": node.type.value,
                        "item": item.value,
                        "timestamp_hour": hour,
                        "hour_of_day": hour % 24,
                        "day_of_week": (hour // 24) % 7,
                        "elevation": node.elevation,
                        "temperature": weather.temperature,
                        "rainfall": weather.rainfall,
                        "wind_speed": weather.wind_speed,
                        "visibility": weather.visibility,
                        "weather_severity": weather.severity.value,
                        "requested_demand": demand_obj.requested_demand,
                    })

        return pd.DataFrame(records)
