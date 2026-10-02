"""PRAVAH Simulation Engine — First Demo Script.

Demonstrates synthetic world generation, baseline normal operations,
and dynamic compound disruption execution with actual calculated values.
"""

from __future__ import annotations
import sys
from pathlib import Path

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from simulation.world_generator import WorldGenerator
from simulation.simulator import Simulator, SimulationConfig
from backend.app.services.scenario_service import ScenarioService


def run_demo():
    seed = 42
    horizon_hours = 336  # 14 days

    # 1. Generate the synthetic world
    world_gen = WorldGenerator(seed=seed)
    world = world_gen.generate_world()

    node_count = len(world.nodes)
    route_count = len(world.routes)
    vehicle_count = len(world.vehicles)

    # 2. Run normal simulation
    normal_config = SimulationConfig(
        seed=seed,
        horizon_hours=horizon_hours,
        scenario_name="NORMAL",
        disruptions=[],
    )
    normal_sim = Simulator(config=normal_config)
    normal_result = normal_sim.run()

    # 3. Run compound disruption
    scenario_service = ScenarioService()
    compound_disruptions = scenario_service.load_disruptions("COMPOUND_DISRUPTION")

    compound_config = SimulationConfig(
        seed=seed,
        horizon_hours=horizon_hours,
        scenario_name="COMPOUND_DISRUPTION",
        disruptions=compound_disruptions,
    )
    compound_sim = Simulator(config=compound_config)
    compound_result = compound_sim.run()

    # Format critical nodes string
    if compound_result.critical_nodes:
        crit_str = ", ".join(
            f"{cn['node_code']} ({cn['unmet_demand']} units)"
            for cn in compound_result.critical_nodes[:3]
        )
    else:
        crit_str = "None (100% Fulfilled)"

    earliest_stockout_str = (
        f"Hour {compound_result.earliest_stockout_hour} (Day {compound_result.earliest_stockout_hour // 24}, +{compound_result.earliest_stockout_hour % 24}h)"
        if compound_result.earliest_stockout_hour is not None
        else "None"
    )

    print("==================================================")
    print("PRAVAH -- SIMULATION ENGINE")
    print(f"Nodes: {node_count} (1 Central Depot, 3 Regional Hubs, 5 Transit Points, 6 Forward Posts)")
    print(f"Routes: {route_count} (Primary highways, high-altitude passes, bypass trails)")
    print(f"Vehicles: {vehicle_count} (Heavy trucks, medium tacticals, all-terrain convoys, light 4x4)")
    print(f"Simulation horizon: {horizon_hours} hours ({horizon_hours // 24} days)")
    print("--------------------------------------------------")
    print("BASELINE RUN (NORMAL):")
    print(f"Requested demand: {normal_result.total_requested_demand:,.1f} units")
    print(f"Fulfilled demand: {normal_result.total_fulfilled_demand:,.1f} units")
    print(f"Unmet demand: {normal_result.total_unmet_demand:,.1f} units")
    print(f"Fulfillment rate: {normal_result.fulfillment_rate_percent:.2f}%")
    print(f"Stockout events: {normal_result.total_stockout_events}")
    print("--------------------------------------------------")
    print("Scenario:")
    print("COMPOUND_DISRUPTION")
    print("Demand impact: +30% across forward defense posts (t=24 to t=192)")
    print("Route impact: Primary corridor ROUTE_R_01 BLOCKED (t=24 to t=144)")
    print("Weather severity: SEVERE blizzard in Northern Sector passes (t=36 to t=132)")
    print("Vehicle availability: -20% fleet reduction (sub-zero maintenance hold)")
    print("Results:")
    print(f"Requested demand: {compound_result.total_requested_demand:,.1f} units")
    print(f"Fulfilled demand: {compound_result.total_fulfilled_demand:,.1f} units")
    print(f"Unmet demand: {compound_result.total_unmet_demand:,.1f} units")
    print(f"Fulfillment rate: {compound_result.fulfillment_rate_percent:.2f}%")
    print(f"Stockout events: {compound_result.total_stockout_events}")
    print(f"Critical nodes: {crit_str}")
    print(f"Earliest stockout: {earliest_stockout_str}")
    print("==================================================")


if __name__ == "__main__":
    run_demo()
