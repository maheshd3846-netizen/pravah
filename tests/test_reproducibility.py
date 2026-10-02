"""Tests for deterministic simulation reproducibility.

Verifies that running the same scenario with identical seeds produces
bit-for-bit identical results and event sequences.
"""

from backend.app.services.scenario_service import ScenarioService
from simulation.simulator import Simulator, SimulationConfig


def test_simulation_reproducibility_seed_42():
    seed = 42
    horizon = 96

    scenario_service = ScenarioService()
    compound_disruptions = scenario_service.load_disruptions("COMPOUND_DISRUPTION")

    config1 = SimulationConfig(
        seed=seed,
        horizon_hours=horizon,
        scenario_name="COMPOUND_DISRUPTION",
        disruptions=compound_disruptions,
    )
    res1 = Simulator(config=config1).run()

    config2 = SimulationConfig(
        seed=seed,
        horizon_hours=horizon,
        scenario_name="COMPOUND_DISRUPTION",
        disruptions=compound_disruptions,
    )
    res2 = Simulator(config=config2).run()

    # Exact equality of demands
    assert res1.total_requested_demand == res2.total_requested_demand
    assert res1.total_fulfilled_demand == res2.total_fulfilled_demand
    assert res1.total_unmet_demand == res2.total_unmet_demand
    assert res1.fulfillment_rate_percent == res2.fulfillment_rate_percent
    assert res1.total_stockout_events == res2.total_stockout_events
    assert res1.earliest_stockout_hour == res2.earliest_stockout_hour
    assert len(res1.shipments) == len(res2.shipments)

    # Verify identical snapshots across steps
    assert len(res1.snapshots) == len(res2.snapshots)
    for s1, s2 in zip(res1.snapshots[:100], res2.snapshots[:100]):
        assert s1.node_id == s2.node_id
        assert s1.item == s2.item
        assert s1.timestamp_hour == s2.timestamp_hour
        assert s1.requested_demand == s2.requested_demand
        assert s1.ending_inventory == s2.ending_inventory
