"""Network Topology API Route."""

from __future__ import annotations
from fastapi import APIRouter
from simulation.world_generator import WorldGenerator
from backend.app.schemas.network import (
    NetworkResponse,
    NodeResponse,
    RouteResponse,
    VehicleResponse,
)

router = APIRouter(prefix="/network", tags=["Network"])


@router.get("", response_model=NetworkResponse)
async def get_network(seed: int = 42) -> NetworkResponse:
    """Returns the complete synthetic military logistics grid: 15 nodes, routes, and vehicle fleet."""
    world_gen = WorldGenerator(seed=seed)
    world = world_gen.generate_world()

    node_responses = [
        NodeResponse(
            id=n.id,
            code=n.code,
            name=n.name,
            type=n.type.value,
            priority=n.priority,
            latitude=n.latitude,
            longitude=n.longitude,
            elevation=n.elevation,
            storage_capacity=n.storage_capacity,
            safety_stock_days=n.safety_stock_days,
            active=n.active,
            initial_inventory=n.initial_inventory,
            reorder_point=n.reorder_point,
            reorder_quantity=n.reorder_quantity,
        )
        for n in world.nodes.values()
    ]

    route_responses = [
        RouteResponse(
            id=r.id,
            route_code=r.route_code,
            source_node_id=r.source_node_id,
            destination_node_id=r.destination_node_id,
            distance_km=r.distance_km,
            base_travel_hours=r.base_travel_hours,
            max_capacity=r.max_capacity,
            terrain_type=r.terrain_type.value,
            reliability_score=r.reliability_score,
            weather_sensitivity=r.weather_sensitivity,
            status=r.status.value,
            geometry=r.geometry,
        )
        for r in world.routes.values()
    ]

    vehicle_responses = [
        VehicleResponse(
            id=v.id,
            vehicle_code=v.vehicle_code,
            vehicle_type=v.vehicle_type.value,
            capacity=v.capacity,
            current_node_id=v.current_node_id,
            availability=v.availability,
            fuel_level=v.fuel_level,
            status=v.status.value,
        )
        for v in world.vehicles.values()
    ]

    return NetworkResponse(
        total_nodes=len(node_responses),
        total_routes=len(route_responses),
        total_vehicles=len(vehicle_responses),
        nodes=node_responses,
        routes=route_responses,
        vehicles=vehicle_responses,
    )
