"""World Generator for PRAVAH Synthetic Logistics Network.

Generates a fully reproducible, fictional military logistics operational environment
for Smart India Hackathon PS 26251. Coordinates and node names are fictional
and do not depict classified or actual operational troop positions.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import random


class NodeType(str, Enum):
    CENTRAL_DEPOT = "CENTRAL_DEPOT"
    REGIONAL_HUB = "REGIONAL_HUB"
    FORWARD_POST = "FORWARD_POST"
    TRANSIT_POINT = "TRANSIT_POINT"


class SupplyCategory(str, Enum):
    FOOD = "FOOD"
    WATER = "WATER"
    FUEL = "FUEL"
    MEDICAL = "MEDICAL"
    GENERAL_CRITICAL = "GENERAL_CRITICAL"


class RouteStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    DEGRADED = "DEGRADED"
    BLOCKED = "BLOCKED"


class TerrainType(str, Enum):
    VALLEY_HIGHWAY = "VALLEY_HIGHWAY"
    MOUNTAIN_ROAD = "MOUNTAIN_ROAD"
    HIGH_ALTITUDE_PASS = "HIGH_ALTITUDE_PASS"
    RUGGED_TRAIL = "RUGGED_TRAIL"


class VehicleStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    IN_TRANSIT = "IN_TRANSIT"
    MAINTENANCE = "MAINTENANCE"
    UNAVAILABLE = "UNAVAILABLE"


class VehicleType(str, Enum):
    HEAVY_TRUCK = "HEAVY_TRUCK"
    MEDIUM_TACTICAL = "MEDIUM_TACTICAL"
    ALL_TERRAIN_CONVOY = "ALL_TERRAIN_CONVOY"
    LIGHT_4X4 = "LIGHT_4X4"


class WeatherSeverity(str, Enum):
    NORMAL = "NORMAL"
    LIGHT = "LIGHT"
    MODERATE = "MODERATE"
    SEVERE = "SEVERE"


class DisruptionType(str, Enum):
    DEMAND_SURGE = "DEMAND_SURGE"
    ROUTE_BLOCKED = "ROUTE_BLOCKED"
    ROUTE_DEGRADED = "ROUTE_DEGRADED"
    WEATHER_DEGRADATION = "WEATHER_DEGRADATION"
    VEHICLE_UNAVAILABLE = "VEHICLE_UNAVAILABLE"
    SUPPLY_DELAY = "SUPPLY_DELAY"
    INVENTORY_REDUCTION = "INVENTORY_REDUCTION"


@dataclass
class Node:
    id: str
    code: str
    name: str
    type: NodeType
    priority: int  # 1 (Highest) to 5 (Critical Forward)
    latitude: float
    longitude: float
    elevation: float  # meters above sea level
    storage_capacity: float  # total storage units
    safety_stock_days: int
    active: bool = True
    initial_inventory: Dict[str, float] = field(default_factory=dict)
    reorder_point: Dict[str, float] = field(default_factory=dict)
    reorder_quantity: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "type": self.type.value,
            "priority": self.priority,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "elevation": self.elevation,
            "storage_capacity": self.storage_capacity,
            "safety_stock_days": self.safety_stock_days,
            "active": self.active,
            "initial_inventory": self.initial_inventory,
            "reorder_point": self.reorder_point,
            "reorder_quantity": self.reorder_quantity,
        }


@dataclass
class Route:
    id: str
    route_code: str
    source_node_id: str
    destination_node_id: str
    distance_km: float
    base_travel_hours: float
    max_capacity: float  # Max convoy volume/units per transit
    terrain_type: TerrainType
    reliability_score: float  # 0.0 - 1.0
    weather_sensitivity: float  # 0.0 - 1.0
    status: RouteStatus = RouteStatus.AVAILABLE
    geometry: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "route_code": self.route_code,
            "source_node_id": self.source_node_id,
            "destination_node_id": self.destination_node_id,
            "distance_km": self.distance_km,
            "base_travel_hours": self.base_travel_hours,
            "max_capacity": self.max_capacity,
            "terrain_type": self.terrain_type.value,
            "reliability_score": self.reliability_score,
            "weather_sensitivity": self.weather_sensitivity,
            "status": self.status.value,
            "geometry": self.geometry,
        }


@dataclass
class Vehicle:
    id: str
    vehicle_code: str
    vehicle_type: VehicleType
    capacity: float
    current_node_id: str
    availability: bool = True
    fuel_level: float = 1.0  # 0.0 to 1.0
    status: VehicleStatus = VehicleStatus.AVAILABLE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "vehicle_code": self.vehicle_code,
            "vehicle_type": self.vehicle_type.value,
            "capacity": self.capacity,
            "current_node_id": self.current_node_id,
            "availability": self.availability,
            "fuel_level": self.fuel_level,
            "status": self.status.value,
        }


@dataclass
class WeatherState:
    region: str
    timestamp_hour: int
    temperature: float  # Celsius
    rainfall: float  # mm/hour
    wind_speed: float  # km/hour
    visibility: float  # km
    severity: WeatherSeverity = WeatherSeverity.NORMAL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "region": self.region,
            "timestamp_hour": self.timestamp_hour,
            "temperature": self.temperature,
            "rainfall": self.rainfall,
            "wind_speed": self.wind_speed,
            "visibility": self.visibility,
            "severity": self.severity.value,
        }


@dataclass
class Shipment:
    shipment_id: str
    source_node_id: str
    destination_node_id: str
    item: str
    quantity: float
    route_id: str
    vehicle_id: str
    departure_time: int  # hour
    expected_arrival: int  # hour
    actual_arrival: int  # hour
    status: str = "IN_TRANSIT"  # SCHEDULED, IN_TRANSIT, DELIVERED, DELAYED, CANCELLED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "shipment_id": self.shipment_id,
            "source_node_id": self.source_node_id,
            "destination_node_id": self.destination_node_id,
            "item": self.item,
            "quantity": self.quantity,
            "route_id": self.route_id,
            "vehicle_id": self.vehicle_id,
            "departure_time": self.departure_time,
            "expected_arrival": self.expected_arrival,
            "actual_arrival": self.actual_arrival,
            "status": self.status,
        }


@dataclass
class WorldState:
    nodes: Dict[str, Node]
    routes: Dict[str, Route]
    vehicles: Dict[str, Vehicle]
    weather_by_node: Dict[str, WeatherState] = field(default_factory=dict)
    active_shipments: List[Shipment] = field(default_factory=list)
    completed_shipments: List[Shipment] = field(default_factory=list)
    current_hour: int = 0
    seed: int = 42

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_hour": self.current_hour,
            "seed": self.seed,
            "node_count": len(self.nodes),
            "route_count": len(self.routes),
            "vehicle_count": len(self.vehicles),
            "nodes": {nid: node.to_dict() for nid, node in self.nodes.items()},
            "routes": {rid: route.to_dict() for rid, route in self.routes.items()},
            "vehicles": {vid: veh.to_dict() for vid, veh in self.vehicles.items()},
            "active_shipments": [s.to_dict() for s in self.active_shipments],
            "completed_shipments": [s.to_dict() for s in self.completed_shipments],
        }


class WorldGenerator:
    """Generates the synthetic logistics world: 15 nodes, routes, vehicles, inventory."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)

    def generate_nodes(self) -> Dict[str, Node]:
        """Creates the 15 synthetic nodes with military hierarchy and realistic parameters."""
        raw_nodes = [
            # 1 Central Logistics Depot
            Node(
                id="NODE_CD_01",
                code="CD-01",
                name="Central Base Depot Alpha",
                type=NodeType.CENTRAL_DEPOT,
                priority=1,
                latitude=34.1200,
                longitude=76.2100,
                elevation=1850.0,
                storage_capacity=500000.0,
                safety_stock_days=21,
                active=True,
            ),
            # 3 Regional Supply Hubs
            Node(
                id="NODE_RH_01",
                code="RH-01",
                name="Northern Sector Hub Trishul",
                type=NodeType.REGIONAL_HUB,
                priority=2,
                latitude=34.4500,
                longitude=76.8200,
                elevation=2900.0,
                storage_capacity=150000.0,
                safety_stock_days=14,
                active=True,
            ),
            Node(
                id="NODE_RH_02",
                code="RH-02",
                name="Eastern Valley Hub Garuda",
                type=NodeType.REGIONAL_HUB,
                priority=2,
                latitude=34.2800,
                longitude=77.4200,
                elevation=3200.0,
                storage_capacity=150000.0,
                safety_stock_days=14,
                active=True,
            ),
            Node(
                id="NODE_RH_03",
                code="RH-03",
                name="Western Ridge Hub Vajra",
                type=NodeType.REGIONAL_HUB,
                priority=2,
                latitude=34.7800,
                longitude=76.3500,
                elevation=3450.0,
                storage_capacity=150000.0,
                safety_stock_days=14,
                active=True,
            ),
            # 5 Intermediate Staging Bases / Transit Points
            Node(
                id="NODE_SB_01",
                code="SB-01",
                name="Transit Staging Base Pass-Alpha",
                type=NodeType.TRANSIT_POINT,
                priority=3,
                latitude=34.3100,
                longitude=76.5400,
                elevation=2400.0,
                storage_capacity=60000.0,
                safety_stock_days=10,
                active=True,
            ),
            Node(
                id="NODE_SB_02",
                code="SB-02",
                name="Transit Staging Base Pass-Beta",
                type=NodeType.TRANSIT_POINT,
                priority=3,
                latitude=34.6200,
                longitude=76.6200,
                elevation=3600.0,
                storage_capacity=60000.0,
                safety_stock_days=10,
                active=True,
            ),
            Node(
                id="NODE_SB_03",
                code="SB-03",
                name="Transit Staging Base Pass-Gamma",
                type=NodeType.TRANSIT_POINT,
                priority=3,
                latitude=34.5000,
                longitude=77.1000,
                elevation=3800.0,
                storage_capacity=60000.0,
                safety_stock_days=10,
                active=True,
            ),
            Node(
                id="NODE_SB_04",
                code="SB-04",
                name="Transit Staging Base Pass-Delta",
                type=NodeType.TRANSIT_POINT,
                priority=3,
                latitude=34.9000,
                longitude=76.9000,
                elevation=4100.0,
                storage_capacity=50000.0,
                safety_stock_days=10,
                active=True,
            ),
            Node(
                id="NODE_SB_05",
                code="SB-05",
                name="Transit Staging Base Pass-Epsilon",
                type=NodeType.TRANSIT_POINT,
                priority=3,
                latitude=34.6500,
                longitude=77.7500,
                elevation=3900.0,
                storage_capacity=50000.0,
                safety_stock_days=10,
                active=True,
            ),
            # 6 Forward Defense Posts
            Node(
                id="NODE_FP_01",
                code="FP-01",
                name="Forward Defense Post Zojila-West",
                type=NodeType.FORWARD_POST,
                priority=5,
                latitude=34.8500,
                longitude=76.4500,
                elevation=4350.0,
                storage_capacity=25000.0,
                safety_stock_days=7,
                active=True,
            ),
            Node(
                id="NODE_FP_02",
                code="FP-02",
                name="Forward Defense Post Kargil-Highland",
                type=NodeType.FORWARD_POST,
                priority=5,
                latitude=35.0500,
                longitude=76.7200,
                elevation=4600.0,
                storage_capacity=20000.0,
                safety_stock_days=7,
                active=True,
            ),
            Node(
                id="NODE_FP_03",
                code="FP-03",
                name="Forward Defense Post Shyok-Glacier",
                type=NodeType.FORWARD_POST,
                priority=5,
                latitude=35.1800,
                longitude=77.2500,
                elevation=4850.0,
                storage_capacity=18000.0,
                safety_stock_days=7,
                active=True,
            ),
            Node(
                id="NODE_FP_04",
                code="FP-04",
                name="Forward Defense Post Changla-Frontier",
                type=NodeType.FORWARD_POST,
                priority=5,
                latitude=34.8200,
                longitude=77.9200,
                elevation=4750.0,
                storage_capacity=22000.0,
                safety_stock_days=7,
                active=True,
            ),
            Node(
                id="NODE_FP_05",
                code="FP-05",
                name="Forward Defense Post Pangong-North",
                type=NodeType.FORWARD_POST,
                priority=5,
                latitude=34.4200,
                longitude=78.1500,
                elevation=4300.0,
                storage_capacity=25000.0,
                safety_stock_days=7,
                active=True,
            ),
            Node(
                id="NODE_FP_06",
                code="FP-06",
                name="Forward Defense Post Siachen-Lookout",
                type=NodeType.FORWARD_POST,
                priority=5,
                latitude=35.2500,
                longitude=76.9500,
                elevation=4980.0,
                storage_capacity=15000.0,
                safety_stock_days=7,
                active=True,
            ),
        ]

        # Baseline daily consumption rates per node type
        baseline_rates = {
            NodeType.CENTRAL_DEPOT: {
                SupplyCategory.FOOD.value: 2000.0,
                SupplyCategory.WATER.value: 2500.0,
                SupplyCategory.FUEL.value: 3000.0,
                SupplyCategory.MEDICAL.value: 400.0,
                SupplyCategory.GENERAL_CRITICAL.value: 600.0,
            },
            NodeType.REGIONAL_HUB: {
                SupplyCategory.FOOD.value: 800.0,
                SupplyCategory.WATER.value: 1000.0,
                SupplyCategory.FUEL.value: 1200.0,
                SupplyCategory.MEDICAL.value: 200.0,
                SupplyCategory.GENERAL_CRITICAL.value: 300.0,
            },
            NodeType.TRANSIT_POINT: {
                SupplyCategory.FOOD.value: 300.0,
                SupplyCategory.WATER.value: 400.0,
                SupplyCategory.FUEL.value: 500.0,
                SupplyCategory.MEDICAL.value: 80.0,
                SupplyCategory.GENERAL_CRITICAL.value: 120.0,
            },
            NodeType.FORWARD_POST: {
                SupplyCategory.FOOD.value: 150.0,
                SupplyCategory.WATER.value: 200.0,
                SupplyCategory.FUEL.value: 350.0,  # High heating fuel need
                SupplyCategory.MEDICAL.value: 50.0,
                SupplyCategory.GENERAL_CRITICAL.value: 80.0,
            },
        }

        # Calculate initial stock based on safety stock days + buffer
        nodes_dict: Dict[str, Node] = {}
        for node in raw_nodes:
            daily_rates = baseline_rates[node.type]
            node.initial_inventory = {}
            node.reorder_point = {}
            node.reorder_quantity = {}

            # Storage capacity allocation multiplier
            storage_alloc = {
                SupplyCategory.FOOD.value: 0.25,
                SupplyCategory.WATER.value: 0.25,
                SupplyCategory.FUEL.value: 0.35,
                SupplyCategory.MEDICAL.value: 0.05,
                SupplyCategory.GENERAL_CRITICAL.value: 0.10,
            }

            for item_cat in SupplyCategory:
                item = item_cat.value
                daily_burn = daily_rates[item]
                # High altitude fuel factor
                if item == SupplyCategory.FUEL.value and node.elevation > 3500:
                    daily_burn *= 1.35

                # Central Depot starts well-stocked (30 days)
                if node.type == NodeType.CENTRAL_DEPOT:
                    stock_days = 30.0
                elif node.type == NodeType.REGIONAL_HUB:
                    stock_days = 16.0
                elif node.type == NodeType.TRANSIT_POINT:
                    stock_days = 12.0
                else:  # FORWARD_POST
                    stock_days = 8.0

                cap_limit = node.storage_capacity * storage_alloc[item]
                initial_stock = min(daily_burn * stock_days, cap_limit * 0.90)

                node.initial_inventory[item] = round(initial_stock, 1)
                node.reorder_point[item] = round(daily_burn * node.safety_stock_days, 1)
                node.reorder_quantity[item] = round(daily_burn * (node.safety_stock_days * 1.5), 1)

            nodes_dict[node.id] = node

        return nodes_dict

    def generate_world(self) -> WorldState:
        """Constructs complete initial world state with nodes, routes, and vehicles."""
        from simulation.network_generator import NetworkGenerator
        from simulation.vehicle_generator import VehicleGenerator

        nodes = self.generate_nodes()
        net_gen = NetworkGenerator(nodes, seed=self.seed)
        routes = net_gen.generate_routes()

        veh_gen = VehicleGenerator(nodes, seed=self.seed)
        vehicles = veh_gen.generate_fleet()

        return WorldState(
            nodes=nodes,
            routes=routes,
            vehicles=vehicles,
            active_shipments=[],
            completed_shipments=[],
            current_hour=0,
            seed=self.seed,
        )
