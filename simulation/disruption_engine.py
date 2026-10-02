"""Disruption Engine for PRAVAH Tactical Supply Shock Simulation.

Applies modular disruptions (route blockages, demand surges, weather degradation,
vehicle fleet shocks, depot supply delays, and inventory destruction) dynamically.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from simulation.world_generator import (
    DisruptionType,
    Route,
    RouteStatus,
    Vehicle,
    VehicleStatus,
    WeatherSeverity,
)


@dataclass
class Disruption:
    id: str
    type: DisruptionType
    target: str  # specific node_id, route_id, vehicle_id, or "ALL_FORWARD_POSTS", "NORTHERN_SECTOR"
    severity: float  # 0.0 to 1.0 (or categorical scale)
    start_time: int  # hour
    duration: int  # hours
    impact_factor: float  # multiplier e.g. 0.30 for +30% demand
    description: str = ""

    @property
    def end_time(self) -> int:
        return self.start_time + self.duration

    def is_active(self, current_hour: int) -> bool:
        return self.start_time <= current_hour < self.end_time

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "target": self.target,
            "severity": self.severity,
            "start_time": self.start_time,
            "duration": self.duration,
            "end_time": self.end_time,
            "impact_factor": self.impact_factor,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Disruption:
        return cls(
            id=data["id"],
            type=DisruptionType(data["type"]),
            target=data["target"],
            severity=float(data["severity"]),
            start_time=int(data["start_time"]),
            duration=int(data["duration"]),
            impact_factor=float(data["impact_factor"]),
            description=data.get("description", ""),
        )


class DisruptionEngine:
    """Manages scheduled and active disruptions affecting routes, fleet, demand, and weather."""

    def __init__(self, disruptions: Optional[List[Disruption]] = None):
        self.disruptions: List[Disruption] = disruptions or []

    def add_disruption(self, disruption: Disruption) -> None:
        self.disruptions.append(disruption)

    def get_active_disruptions(self, current_hour: int) -> List[Disruption]:
        return [d for d in self.disruptions if d.is_active(current_hour)]

    def get_demand_surge_multiplier(self, node_id: str, node_type: str, current_hour: int) -> float:
        """Computes aggregate demand surge multiplier for a node at current hour."""
        multiplier = 1.0
        for d in self.get_active_disruptions(current_hour):
            if d.type == DisruptionType.DEMAND_SURGE:
                matches = False
                if d.target == node_id:
                    matches = True
                elif d.target in ["ALL_FORWARD_POSTS", "FORWARD_POST"] and node_type == "FORWARD_POST":
                    matches = True
                elif d.target == "ALL":
                    matches = True

                if matches:
                    multiplier += d.impact_factor
        return multiplier

    def apply_route_disruptions(self, routes: Dict[str, Route], current_hour: int) -> None:
        """Modifies route status based on active disruptions."""
        # First reset routes that were previously modified unless blocked by inherent terrain
        for r in routes.values():
            r.status = RouteStatus.AVAILABLE

        active_disruptions = self.get_active_disruptions(current_hour)
        for d in active_disruptions:
            if d.type == DisruptionType.ROUTE_BLOCKED:
                if d.target in routes:
                    routes[d.target].status = RouteStatus.BLOCKED
                elif d.target == "PRIMARY_CORRIDOR":
                    # Block key central supply line R-01
                    if "ROUTE_R_01" in routes:
                        routes["ROUTE_R_01"].status = RouteStatus.BLOCKED
            elif d.type == DisruptionType.ROUTE_DEGRADED:
                if d.target in routes:
                    routes[d.target].status = RouteStatus.DEGRADED

    def apply_vehicle_disruptions(self, vehicles: Dict[str, Vehicle], current_hour: int) -> None:
        """Disables vehicles based on fleet disruption shocks."""
        active_disruptions = self.get_active_disruptions(current_hour)
        for d in active_disruptions:
            if d.type == DisruptionType.VEHICLE_UNAVAILABLE:
                if d.target in vehicles:
                    vehicles[d.target].status = VehicleStatus.UNAVAILABLE
                    vehicles[d.target].availability = False
                elif d.target == "FLEET_PERCENTAGE":
                    # Disable fraction of available vehicles
                    num_to_disable = max(1, int(len(vehicles) * d.impact_factor))
                    count = 0
                    for v in vehicles.values():
                        if count < num_to_disable and v.status != VehicleStatus.IN_TRANSIT:
                            v.status = VehicleStatus.UNAVAILABLE
                            v.availability = False
                            count += 1

    def get_weather_override(self, node_id: str, current_hour: int) -> Optional[WeatherSeverity]:
        """Checks if a weather degradation disruption forces severe weather."""
        for d in self.get_active_disruptions(current_hour):
            if d.type == DisruptionType.WEATHER_DEGRADATION:
                return WeatherSeverity.SEVERE
        return None
