"""Tests for demand surge disruptions and unmet demand tracking."""

from simulation.world_generator import DisruptionType
from simulation.disruption_engine import Disruption
from simulation.simulator import Simulator, SimulationConfig


def test_demand_surge_impact():
    # Run baseline normal
    normal_config = SimulationConfig(seed=42, horizon_hours=48, disruptions=[])
    normal_sim = Simulator(config=normal_config)
    normal_res = normal_sim.run()

    # Run demand surge scenario: +50% on all forward posts
    surge_disr = Disruption(
        id="D_SURGE_01",
        type=DisruptionType.DEMAND_SURGE,
        target="ALL_FORWARD_POSTS",
        severity=0.5,
        start_time=0,
        duration=48,
        impact_factor=0.50,
    )
    surge_config = SimulationConfig(seed=42, horizon_hours=48, disruptions=[surge_disr])
    surge_sim = Simulator(config=surge_config)
    surge_res = surge_sim.run()

    # Requested demand must be noticeably higher under surge
    assert surge_res.total_requested_demand > normal_res.total_requested_demand

    # Difference in demand should roughly match the +50% forward post demand
    delta_demand = surge_res.total_requested_demand - normal_res.total_requested_demand
    assert delta_demand > 5000.0
