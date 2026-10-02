"""Tests for route blockage disruptions and alternate route routing."""

from simulation.world_generator import RouteStatus, DisruptionType
from simulation.disruption_engine import Disruption
from simulation.simulator import Simulator, SimulationConfig


def test_route_blockage_prevents_direct_dispatch():
    # Define disruption blocking ROUTE_R_01 (CD-01 to RH-01) from hour 0 to 48
    disr = Disruption(
        id="D_BLOCK_01",
        type=DisruptionType.ROUTE_BLOCKED,
        target="ROUTE_R_01",
        severity=1.0,
        start_time=0,
        duration=48,
        impact_factor=1.0,
    )

    config = SimulationConfig(
        seed=42,
        horizon_hours=24,
        scenario_name="ROUTE_TEST",
        disruptions=[disr],
    )
    sim = Simulator(config=config)

    # Initial route status should be AVAILABLE
    assert sim.world.routes["ROUTE_R_01"].status == RouteStatus.AVAILABLE

    # After step at hour 0, disruption applies and ROUTE_R_01 is BLOCKED
    sim.step()
    assert sim.world.routes["ROUTE_R_01"].status == RouteStatus.BLOCKED

    # Finding best route must avoid ROUTE_R_01 and pick alternate or multi-hop path
    best = sim.find_best_route("NODE_CD_01", "NODE_RH_01")
    if best is not None:
        assert best.id != "ROUTE_R_01"
        assert best.status != RouteStatus.BLOCKED
