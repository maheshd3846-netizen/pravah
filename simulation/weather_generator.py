"""Weather Generator for PRAVAH Environmental Modeling.

Generates continuous synthetic weather conditions (temperature, precipitation,
wind speed, visibility, severity) across high-altitude mountain sectors.
Directly dictates route travel time degradation and road conditions.
"""

from __future__ import annotations
import math
from typing import Dict, Optional
import numpy as np
from simulation.world_generator import (
    Node,
    Route,
    WeatherSeverity,
    WeatherState,
)


class WeatherGenerator:
    """Generates deterministic continuous weather states across spatial sectors."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = np.random.RandomState(seed)

    def _determine_severity(
        self, rainfall: float, wind_speed: float, visibility: float, temperature: float
    ) -> WeatherSeverity:
        """Determines categorical severity based on operational military thresholds."""
        # Extreme blizzard / whiteout / severe storm conditions
        if visibility < 2.0 or wind_speed > 65.0 or rainfall > 15.0 or temperature < -25.0:
            return WeatherSeverity.SEVERE
        # High winds or heavy rain/snow
        elif visibility < 5.0 or wind_speed > 45.0 or rainfall > 5.0 or temperature < -15.0:
            return WeatherSeverity.MODERATE
        # Light precipitation or moderate breeze
        elif visibility < 8.0 or wind_speed > 30.0 or rainfall > 1.0:
            return WeatherSeverity.LIGHT
        return WeatherSeverity.NORMAL

    def generate_weather(
        self,
        node: Node,
        timestamp_hour: int,
        forced_severity: Optional[WeatherSeverity] = None,
    ) -> WeatherState:
        """Generates continuous environmental state at a given node and simulation hour."""
        # Deterministic pseudo-random seed per node and timestamp
        node_seed = (self.seed + hash(node.id) + timestamp_hour * 73) % (2**31 - 1)
        local_rng = np.random.RandomState(node_seed)

        # Diurnal temperature cycle: peaks at 14:00 (hour 14), lowest at 04:00 (hour 4)
        hour_of_day = timestamp_hour % 24
        day_of_year = (timestamp_hour // 24) % 365

        # Elevation lapse rate: ~6.5°C per 1000m above base 1500m
        base_temp_sea_level = 10.0 + 12.0 * math.sin(2 * math.pi * (day_of_year - 80) / 365)
        elevation_drop = (node.elevation - 1500.0) * 0.0065
        daily_temp_swing = 7.0 * math.sin(2 * math.pi * (hour_of_day - 8) / 24)
        temperature = round(base_temp_sea_level - elevation_drop + daily_temp_swing + local_rng.normal(0, 1.2), 1)

        if forced_severity == WeatherSeverity.SEVERE:
            rainfall = round(float(local_rng.uniform(16.0, 32.0)), 1)
            wind_speed = round(float(local_rng.uniform(68.0, 95.0)), 1)
            visibility = round(float(local_rng.uniform(0.3, 1.8)), 2)
            temperature = round(min(temperature, -18.0) - float(local_rng.uniform(2.0, 7.0)), 1)
            severity = WeatherSeverity.SEVERE
        elif forced_severity == WeatherSeverity.MODERATE:
            rainfall = round(float(local_rng.uniform(6.0, 14.0)), 1)
            wind_speed = round(float(local_rng.uniform(46.0, 62.0)), 1)
            visibility = round(float(local_rng.uniform(2.2, 4.8)), 2)
            severity = WeatherSeverity.MODERATE
        elif forced_severity == WeatherSeverity.LIGHT:
            rainfall = round(float(local_rng.uniform(1.2, 4.5)), 1)
            wind_speed = round(float(local_rng.uniform(31.0, 44.0)), 1)
            visibility = round(float(local_rng.uniform(5.2, 7.8)), 2)
            severity = WeatherSeverity.LIGHT
        elif forced_severity == WeatherSeverity.NORMAL:
            rainfall = 0.0
            wind_speed = round(float(local_rng.uniform(8.0, 24.0)), 1)
            visibility = round(float(local_rng.uniform(8.5, 15.0)), 1)
            severity = WeatherSeverity.NORMAL
        else:
            # Stochastic baseline with mountain weather patterns (waves of precipitation every 4-7 days)
            wave = math.sin(2 * math.pi * timestamp_hour / 140.0)
            if wave > 0.65:
                # Storm window
                rainfall = round(max(0.0, float(local_rng.exponential(3.0))), 1)
                wind_speed = round(float(local_rng.uniform(35.0, 70.0)), 1)
                visibility = round(float(local_rng.uniform(1.5, 6.0)), 1)
            else:
                rainfall = round(max(0.0, float(local_rng.exponential(0.3))), 1) if local_rng.rand() < 0.2 else 0.0
                wind_speed = round(float(local_rng.uniform(10.0, 32.0)), 1)
                visibility = round(float(local_rng.uniform(7.0, 15.0)), 1)

            severity = self._determine_severity(rainfall, wind_speed, visibility, temperature)

        # Region classification based on longitude
        if node.longitude < 76.6:
            region = "WESTERN_SECTOR"
        elif node.longitude > 77.4:
            region = "EASTERN_SECTOR"
        else:
            region = "NORTHERN_SECTOR"

        return WeatherState(
            region=region,
            timestamp_hour=timestamp_hour,
            temperature=temperature,
            rainfall=rainfall,
            wind_speed=wind_speed,
            visibility=visibility,
            severity=severity,
        )

    def calculate_effective_travel_time(
        self,
        route: Route,
        weather: WeatherState,
    ) -> float:
        """Dynamically computes the actual travel duration based on weather state and route sensitivity."""
        # Severity delay multipliers
        severity_multipliers = {
            WeatherSeverity.NORMAL: 1.0,
            WeatherSeverity.LIGHT: 1.25,
            WeatherSeverity.MODERATE: 1.65,
            WeatherSeverity.SEVERE: 2.50,
        }

        base_multiplier = severity_multipliers[weather.severity]

        # Weight the weather delay by route-specific weather sensitivity
        # effective = base * (1 + sensitivity * (multiplier - 1))
        weather_impact = 1.0 + (route.weather_sensitivity * (base_multiplier - 1.0))

        # Temperature / Freezing icing factor for high passes
        if weather.temperature < -10.0 and "PASS" in route.terrain_type.value:
            weather_impact *= 1.20

        effective_hours = round(route.base_travel_hours * weather_impact, 2)
        return effective_hours
