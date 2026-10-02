"""Tests for vehicle unavailability shocks."""

from simulation.world_generator import VehicleStatus, DisruptionType
from simulation.disruption_engine import Disruption
from simulation.simulator import Simulator, SimulationConfig


def test_vehicle_unavailability_shock():
    # Disruption disabling 50% of the fleet
    disr = Disruption(
        id="D_VEH_01",
        type=DisruptionType.VEHICLE_UNAVAILABLE,
        target="FLEET_PERCENTAGE",
        severity=0.8,
        start_time=0,
        duration=24,
        impact_factor=0.50,
    )

    config = SimulationConfig(seed=42, horizon_hours=12, disruptions=[disr])
    sim = Simulator(config=config)

    sim.step()

    unavailable = [v for v in sim.world.vehicles.values() if v.status == VehicleStatus.UNAVAILABLE]
    assert len(unavailable) >= 4
    for v in unavailable:
        assert v.availability is False
