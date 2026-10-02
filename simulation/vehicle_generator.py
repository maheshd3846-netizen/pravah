"""Vehicle Fleet Generator for PRAVAH Logistics Grid.

Generates 10-12 tactical transport vehicles with realistic capacities,
fuel state, initial operational staging nodes, and availability tracking.
"""

from __future__ import annotations
from typing import Dict, List
from simulation.world_generator import (
    Node,
    Vehicle,
    VehicleStatus,
    VehicleType,
)


class VehicleGenerator:
    """Generates the tactical transport fleet stationed across depot and regional hubs."""

    def __init__(self, nodes: Dict[str, Node], seed: int = 42):
        self.nodes = nodes
        self.seed = seed

    def generate_fleet(self) -> Dict[str, Vehicle]:
        """Creates 12 tactical vehicles stationed across depot and regional hubs."""
        fleet_specs = [
            # 4x Heavy Logistics Trucks (Based at Depot and Major Hubs)
            ("VEH_HT_01", "ALS-101", VehicleType.HEAVY_TRUCK, 12000.0, "NODE_CD_01", 1.0),
            ("VEH_HT_02", "ALS-102", VehicleType.HEAVY_TRUCK, 12000.0, "NODE_CD_01", 0.95),
            ("VEH_HT_03", "ALS-103", VehicleType.HEAVY_TRUCK, 10000.0, "NODE_RH_01", 0.90),
            ("VEH_HT_04", "ALS-104", VehicleType.HEAVY_TRUCK, 10000.0, "NODE_RH_02", 0.85),

            # 4x Medium Tactical Vehicles (Flexible regional distribution)
            ("VEH_MT_01", "MATV-201", VehicleType.MEDIUM_TACTICAL, 6000.0, "NODE_CD_01", 0.95),
            ("VEH_MT_02", "MATV-202", VehicleType.MEDIUM_TACTICAL, 6000.0, "NODE_RH_01", 0.90),
            ("VEH_MT_03", "MATV-203", VehicleType.MEDIUM_TACTICAL, 5500.0, "NODE_RH_02", 0.85),
            ("VEH_MT_04", "MATV-204", VehicleType.MEDIUM_TACTICAL, 5500.0, "NODE_RH_03", 0.90),

            # 2x All-Terrain High-Mobility Convoys (For extreme passes and rugged trails)
            ("VEH_ATC_01", "ATC-301", VehicleType.ALL_TERRAIN_CONVOY, 4000.0, "NODE_SB_02", 0.92),
            ("VEH_ATC_02", "ATC-302", VehicleType.ALL_TERRAIN_CONVOY, 4000.0, "NODE_SB_03", 0.88),

            # 2x Light 4x4 Fast Tactical Couriers (Medical & emergency supplies)
            ("VEH_L4X_01", "LTAC-401", VehicleType.LIGHT_4X4, 2000.0, "NODE_RH_01", 1.0),
            ("VEH_L4X_02", "LTAC-402", VehicleType.LIGHT_4X4, 2000.0, "NODE_RH_03", 0.95),
        ]

        vehicles_dict: Dict[str, Vehicle] = {}
        for vid, code, vtype, cap, node_id, fuel in fleet_specs:
            v = Vehicle(
                id=vid,
                vehicle_code=code,
                vehicle_type=vtype,
                capacity=cap,
                current_node_id=node_id,
                availability=True,
                fuel_level=fuel,
                status=VehicleStatus.AVAILABLE,
            )
            vehicles_dict[v.id] = v

        return vehicles_dict
