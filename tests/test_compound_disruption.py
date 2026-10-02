"""Tests for multi-factor compound disruption scenario execution."""

from backend.app.services.scenario_service import ScenarioService
from simulation.simulator import Simulator, SimulationConfig


def test_compound_disruption_impact():
    seed = 42
    horizon = 168  # 7 days

    scenario_service = ScenarioService()

    # Normal Run
    normal_config = SimulationConfig(seed=seed, horizon_hours=horizon, scenario_name="NORMAL")
    normal_res = Simulator(config=normal_config).run()

    # Compound Run
    compound_disruptions = scenario_service.load_disruptions("COMPOUND_DISRUPTION")
    compound_config = SimulationConfig(
        seed=seed,
        horizon_hours=horizon,
        scenario_name="COMPOUND_DISRUPTION",
        disruptions=compound_disruptions,
    )
    compound_res = Simulator(config=compound_config).run()

    # Compound disruption should cause higher demand, lower fulfillment rate, and more stockouts
    assert compound_res.total_requested_demand > normal_res.total_requested_demand
    assert compound_res.total_unmet_demand > normal_res.total_unmet_demand
    assert compound_res.fulfillment_rate_percent <= normal_res.fulfillment_rate_percent
    assert compound_res.total_stockout_events >= normal_res.total_stockout_events
    assert len(compound_res.critical_nodes) > 0
