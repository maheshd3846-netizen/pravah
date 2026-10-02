"""Network Generator for PRAVAH Logistics Grid.

Constructs 20-40 realistic military forward routes with terrain classification,
weather sensitivity, multi-path redundancy (primary and alternate bypass routes),
and GeoJSON geometry coordinates.
"""

from __future__ import annotations
import math
from typing import Dict, List, Tuple
from simulation.world_generator import (
    Node,
    Route,
    RouteStatus,
    TerrainType,
)


class NetworkGenerator:
    """Generates the connected route graph with terrain types, redundancy, and geometry."""

    def __init__(self, nodes: Dict[str, Node], seed: int = 42):
        self.nodes = nodes
        self.seed = seed

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculates surface distance in kilometers."""
        r = 6371.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        a = (
            math.sin(delta_phi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return r * c

    def generate_routes(self) -> Dict[str, Route]:
        """Creates 28-32 connected routes with primary and alternate bypass pathways."""

        # Define edge topology between nodes:
        # (source_id, dest_id, code, terrain_type, detour_multiplier, capacity, base_speed_kmh, weather_sens, reliability)
        raw_edges: List[Tuple[str, str, str, TerrainType, float, float, float, float, float]] = [
            # Central Depot -> Regional Hubs & Staging Bases
            ("NODE_CD_01", "NODE_RH_01", "R-01", TerrainType.VALLEY_HIGHWAY, 1.25, 20000.0, 45.0, 0.25, 0.95),
            ("NODE_CD_01", "NODE_SB_01", "R-02", TerrainType.VALLEY_HIGHWAY, 1.20, 25000.0, 50.0, 0.20, 0.96),
            ("NODE_SB_01", "NODE_RH_01", "R-03", TerrainType.MOUNTAIN_ROAD, 1.35, 15000.0, 32.0, 0.50, 0.88),  # Alternate to R-01
            ("NODE_CD_01", "NODE_RH_02", "R-04", TerrainType.MOUNTAIN_ROAD, 1.30, 18000.0, 35.0, 0.45, 0.90),
            ("NODE_CD_01", "NODE_RH_03", "R-05", TerrainType.MOUNTAIN_ROAD, 1.35, 16000.0, 30.0, 0.50, 0.89),

            # Lateral / Cross-Hub Connections (Network Resilience)
            ("NODE_RH_01", "NODE_RH_03", "R-06", TerrainType.HIGH_ALTITUDE_PASS, 1.50, 10000.0, 22.0, 0.80, 0.75),
            ("NODE_RH_01", "NODE_RH_02", "R-07", TerrainType.MOUNTAIN_ROAD, 1.40, 12000.0, 28.0, 0.55, 0.85),

            # Hub to Staging Bases
            ("NODE_RH_01", "NODE_SB_02", "R-08", TerrainType.MOUNTAIN_ROAD, 1.30, 14000.0, 30.0, 0.50, 0.88),
            ("NODE_RH_01", "NODE_SB_03", "R-09", TerrainType.HIGH_ALTITUDE_PASS, 1.45, 10000.0, 20.0, 0.82, 0.72),
            ("NODE_RH_03", "NODE_SB_02", "R-10", TerrainType.HIGH_ALTITUDE_PASS, 1.40, 10000.0, 22.0, 0.78, 0.76),
            ("NODE_RH_03", "NODE_FP_01", "R-11", TerrainType.MOUNTAIN_ROAD, 1.35, 12000.0, 28.0, 0.60, 0.84),
            ("NODE_RH_02", "NODE_SB_03", "R-12", TerrainType.MOUNTAIN_ROAD, 1.35, 12000.0, 30.0, 0.50, 0.86),
            ("NODE_RH_02", "NODE_SB_05", "R-13", TerrainType.MOUNTAIN_ROAD, 1.35, 14000.0, 32.0, 0.45, 0.90),

            # Staging Bases to Staging Bases & Forward Posts
            ("NODE_SB_02", "NODE_FP_01", "R-14", TerrainType.HIGH_ALTITUDE_PASS, 1.40, 8000.0, 20.0, 0.85, 0.70),  # Alternate to R-11
            ("NODE_SB_02", "NODE_SB_04", "R-15", TerrainType.HIGH_ALTITUDE_PASS, 1.50, 9000.0, 18.0, 0.85, 0.70),
            ("NODE_SB_02", "NODE_FP_02", "R-16", TerrainType.MOUNTAIN_ROAD, 1.35, 10000.0, 25.0, 0.65, 0.80),
            ("NODE_SB_04", "NODE_FP_02", "R-17", TerrainType.RUGGED_TRAIL, 1.60, 6000.0, 15.0, 0.88, 0.68),  # Alternate to R-16
            ("NODE_SB_04", "NODE_FP_06", "R-18", TerrainType.HIGH_ALTITUDE_PASS, 1.55, 6000.0, 16.0, 0.90, 0.65),

            ("NODE_SB_03", "NODE_FP_03", "R-19", TerrainType.HIGH_ALTITUDE_PASS, 1.45, 8000.0, 20.0, 0.85, 0.72),
            ("NODE_SB_04", "NODE_FP_03", "R-20", TerrainType.RUGGED_TRAIL, 1.65, 5000.0, 14.0, 0.90, 0.62),  # Alternate to R-19
            ("NODE_SB_03", "NODE_SB_04", "R-21", TerrainType.RUGGED_TRAIL, 1.55, 6000.0, 16.0, 0.85, 0.65),

            ("NODE_SB_05", "NODE_FP_04", "R-22", TerrainType.HIGH_ALTITUDE_PASS, 1.45, 8000.0, 22.0, 0.80, 0.74),
            ("NODE_SB_03", "NODE_FP_04", "R-23", TerrainType.RUGGED_TRAIL, 1.60, 6000.0, 16.0, 0.85, 0.66),  # Alternate to R-22
            ("NODE_SB_05", "NODE_FP_05", "R-24", TerrainType.MOUNTAIN_ROAD, 1.30, 10000.0, 28.0, 0.60, 0.82),
            ("NODE_RH_02", "NODE_FP_05", "R-25", TerrainType.VALLEY_HIGHWAY, 1.25, 14000.0, 38.0, 0.35, 0.92),  # Direct bypass
            ("NODE_FP_02", "NODE_FP_06", "R-26", TerrainType.RUGGED_TRAIL, 1.70, 4000.0, 12.0, 0.95, 0.60),  # Extreme forward ridge
            ("NODE_FP_01", "NODE_FP_02", "R-27", TerrainType.MOUNTAIN_ROAD, 1.40, 7000.0, 24.0, 0.70, 0.78),  # Forward lateral link
            ("NODE_FP_03", "NODE_FP_04", "R-28", TerrainType.HIGH_ALTITUDE_PASS, 1.50, 5000.0, 18.0, 0.85, 0.68),  # Lateral link
        ]

        routes_dict: Dict[str, Route] = {}

        for src_id, dst_id, code, terrain, detour, cap, speed, w_sens, rel in raw_edges:
            src = self.nodes[src_id]
            dst = self.nodes[dst_id]

            straight_dist = self._haversine_distance(
                src.latitude, src.longitude, dst.latitude, dst.longitude
            )
            dist_km = round(straight_dist * detour, 1)
            base_travel_hours = max(1.0, round(dist_km / speed, 2))

            # GeoJSON geometry coordinates [[lon, lat], [lon, lat]]
            # Add an intermediate elevation waypoint for realistic routing polyline
            mid_lon = (src.longitude + dst.longitude) / 2.0
            mid_lat = (src.latitude + dst.latitude) / 2.0 + (0.015 if "PASS" in terrain.value else 0.0)

            geometry = {
                "type": "LineString",
                "coordinates": [
                    [src.longitude, src.latitude],
                    [mid_lon, mid_lat],
                    [dst.longitude, dst.latitude],
                ],
            }

            route_id = f"ROUTE_{code.replace('-', '_')}"
            route = Route(
                id=route_id,
                route_code=code,
                source_node_id=src_id,
                destination_node_id=dst_id,
                distance_km=dist_km,
                base_travel_hours=base_travel_hours,
                max_capacity=cap,
                terrain_type=terrain,
                reliability_score=rel,
                weather_sensitivity=w_sens,
                status=RouteStatus.AVAILABLE,
                geometry=geometry,
            )
            routes_dict[route.id] = route

        return routes_dict
