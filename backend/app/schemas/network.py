"""Pydantic Schemas for Network Topology and Assets."""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class NodeResponse(BaseModel):
    id: str
    code: str
    name: str
    type: str
    priority: int
    latitude: float
    longitude: float
    elevation: float
    storage_capacity: float
    safety_stock_days: int
    active: bool
    initial_inventory: Dict[str, float] = Field(default_factory=dict)
    reorder_point: Dict[str, float] = Field(default_factory=dict)
    reorder_quantity: Dict[str, float] = Field(default_factory=dict)


class RouteResponse(BaseModel):
    id: str
    route_code: str
    source_node_id: str
    destination_node_id: str
    distance_km: float
    base_travel_hours: float
    max_capacity: float
    terrain_type: str
    reliability_score: float
    weather_sensitivity: float
    status: str
    geometry: Dict[str, Any] = Field(default_factory=dict)


class VehicleResponse(BaseModel):
    id: str
    vehicle_code: str
    vehicle_type: str
    capacity: float
    current_node_id: str
    availability: bool
    fuel_level: float
    status: str


class NetworkResponse(BaseModel):
    total_nodes: int
    total_routes: int
    total_vehicles: int
    nodes: List[NodeResponse]
    routes: List[RouteResponse]
    vehicles: List[VehicleResponse]
