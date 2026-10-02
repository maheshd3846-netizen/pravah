"""Tests for shipment in-transit state and inventory delivery upon arrival."""

from simulation.world_generator import WorldGenerator, Shipment, VehicleStatus
from simulation.simulator import Simulator, SimulationConfig


def test_shipment_arrival_and_vehicle_release():
    sim = Simulator(config=SimulationConfig(seed=42, auto_replenish=False))

    src_node = "NODE_CD_01"
    dst_node = "NODE_RH_01"
    item = "FUEL"
    qty = 2500.0

    initial_dst_fuel = sim.inventory_engine.get_stock(dst_node, item)

    # Pick an available vehicle
    vehicle = list(sim.world.vehicles.values())[0]
    vehicle.current_node_id = src_node
    vehicle.status = VehicleStatus.IN_TRANSIT
    vehicle.availability = False

    # Dispatch shipment arriving at hour 2
    shipment = Shipment(
        shipment_id="TEST_ARRIVE_01",
        source_node_id=src_node,
        destination_node_id=dst_node,
        item=item,
        quantity=qty,
        route_id="ROUTE_R_01",
        vehicle_id=vehicle.id,
        departure_time=0,
        expected_arrival=1,
        actual_arrival=1,
        status="IN_TRANSIT",
    )
    sim.world.active_shipments.append(shipment)

    # Step to hour 1 -> shipment should still be in-transit
    sim.step()
    assert len(sim.world.active_shipments) == 1
    assert vehicle.status == VehicleStatus.IN_TRANSIT

    # Step to hour 2 -> shipment arrives and is delivered
    sim.step()
    assert len(sim.world.active_shipments) == 0
    assert len(sim.world.completed_shipments) == 1
    assert sim.world.completed_shipments[0].status == "DELIVERED"

    # Vehicle should be freed and stationed at destination
    assert vehicle.status == VehicleStatus.AVAILABLE
    assert vehicle.availability is True
    assert vehicle.current_node_id == dst_node

    # Destination fuel stock must reflect arrival (minus consumption during steps)
    ending_fuel = sim.inventory_engine.get_stock(dst_node, item)
    # The arrival added 2500 units
    assert ending_fuel > (initial_dst_fuel - 500.0)
