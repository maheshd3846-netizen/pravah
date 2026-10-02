"""Tests for inventory conservation, non-negativity, and stockout tracking."""

from simulation.world_generator import WorldGenerator, Shipment
from simulation.inventory_engine import InventoryEngine
from simulation.demand_generator import HourlyDemand


def test_inventory_non_negativity():
    world = WorldGenerator(seed=42).generate_world()
    engine = InventoryEngine(world.nodes)

    # Force an extreme demand that exceeds available stock
    target_node = list(world.nodes.keys())[0]
    initial_food = engine.get_stock(target_node, "FOOD")

    excessive_demand = [
        HourlyDemand(
            node_id=target_node,
            item="FOOD",
            timestamp_hour=1,
            requested_demand=initial_food + 50000.0,
        )
    ]

    processed, snapshots = engine.process_step(
        timestamp_hour=1,
        demands=excessive_demand,
        arrived_shipments=[],
        dispatched_shipments=[],
    )

    # Stock must be exactly 0, never negative
    ending_stock = engine.get_stock(target_node, "FOOD")
    assert ending_stock == 0.0

    # Demand fulfilled equals available stock, unmet equals remainder
    d_res = processed[0]
    assert d_res.fulfilled_demand == initial_food
    assert d_res.unmet_demand == 50000.0

    # Stockout event must be recorded
    assert len(engine.stockout_events) >= 1
    event = engine.stockout_events[-1]
    assert event.node_id == target_node
    assert event.item == "FOOD"
    assert event.shortage_amount == 50000.0


def test_inventory_conservation_with_receipts():
    world = WorldGenerator(seed=42).generate_world()
    engine = InventoryEngine(world.nodes)

    target_node = list(world.nodes.keys())[0]
    initial_water = engine.get_stock(target_node, "WATER")

    # Inflow shipment
    shipment = Shipment(
        shipment_id="TEST_S1",
        source_node_id="NODE_CD_01",
        destination_node_id=target_node,
        item="WATER",
        quantity=500.0,
        route_id="R-01",
        vehicle_id="VEH-01",
        departure_time=0,
        expected_arrival=1,
        actual_arrival=1,
    )

    # Moderate demand
    demand = [
        HourlyDemand(
            node_id=target_node,
            item="WATER",
            timestamp_hour=1,
            requested_demand=200.0,
        )
    ]

    engine.process_step(
        timestamp_hour=1,
        demands=demand,
        arrived_shipments=[shipment],
        dispatched_shipments=[],
    )

    ending_water = engine.get_stock(target_node, "WATER")
    # Balance: I[t+1] = I[t] + receipts - demand
    expected_end = initial_water + 500.0 - 200.0
    assert abs(ending_water - expected_end) < 0.01
