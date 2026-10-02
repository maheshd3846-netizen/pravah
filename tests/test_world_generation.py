"""Tests for deterministic world generation and network topology."""

from simulation.world_generator import (
    WorldGenerator,
    NodeType,
    SupplyCategory,
    RouteStatus,
    VehicleType,
)


def test_deterministic_world_generation():
    gen1 = WorldGenerator(seed=42)
    world1 = gen1.generate_world()

    gen2 = WorldGenerator(seed=42)
    world2 = gen2.generate_world()

    # Exact equality of node counts and IDs
    assert len(world1.nodes) == len(world2.nodes)
    assert set(world1.nodes.keys()) == set(world2.nodes.keys())

    # Verify identical node coordinates and initial stocks
    for nid in world1.nodes:
        n1 = world1.nodes[nid]
        n2 = world2.nodes[nid]
        assert n1.latitude == n2.latitude
        assert n1.longitude == n2.longitude
        assert n1.elevation == n2.elevation
        assert n1.storage_capacity == n2.storage_capacity
        assert n1.initial_inventory == n2.initial_inventory

    # Verify identical routes
    assert len(world1.routes) == len(world2.routes)
    for rid in world1.routes:
        assert world1.routes[rid].distance_km == world2.routes[rid].distance_km
        assert world1.routes[rid].base_travel_hours == world2.routes[rid].base_travel_hours


def test_world_node_hierarchy():
    world = WorldGenerator(seed=42).generate_world()

    # Total 15 nodes
    assert len(world.nodes) == 15

    depots = [n for n in world.nodes.values() if n.type == NodeType.CENTRAL_DEPOT]
    hubs = [n for n in world.nodes.values() if n.type == NodeType.REGIONAL_HUB]
    staging = [n for n in world.nodes.values() if n.type == NodeType.TRANSIT_POINT]
    forward = [n for n in world.nodes.values() if n.type == NodeType.FORWARD_POST]

    assert len(depots) == 1
    assert len(hubs) == 3
    assert len(staging) == 5
    assert len(forward) == 6


def test_supply_categories():
    world = WorldGenerator(seed=42).generate_world()
    expected_categories = {"FOOD", "WATER", "FUEL", "MEDICAL", "GENERAL_CRITICAL"}

    for node in world.nodes.values():
        assert set(node.initial_inventory.keys()) == expected_categories
        assert all(qty > 0 for qty in node.initial_inventory.values())


def test_route_network_specifications():
    world = WorldGenerator(seed=42).generate_world()
    # 20 - 40 routes required
    assert 20 <= len(world.routes) <= 40

    for route in world.routes.values():
        assert route.distance_km > 0
        assert route.base_travel_hours > 0
        assert route.max_capacity > 0
        assert 0.0 <= route.reliability_score <= 1.0
        assert 0.0 <= route.weather_sensitivity <= 1.0
        assert route.status in [RouteStatus.AVAILABLE, RouteStatus.DEGRADED, RouteStatus.BLOCKED]
        assert "coordinates" in route.geometry


def test_vehicle_fleet():
    world = WorldGenerator(seed=42).generate_world()
    # 10 - 12 vehicles required
    assert 10 <= len(world.vehicles) <= 12

    types = {v.vehicle_type for v in world.vehicles.values()}
    assert VehicleType.HEAVY_TRUCK in types
    assert VehicleType.MEDIUM_TACTICAL in types
