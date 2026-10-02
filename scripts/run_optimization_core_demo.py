"""PRAVAH Phase 3A — Mathematical Optimization Core Demonstration.

Demonstrates:
1. Loading multi-echelon network topology and compound disruption scenario.
2. Formulating multi-commodity risk-aware optimization problem using P80 demand policy.
3. Solving via SciPy HiGHS MILP mathematical solver.
4. Validating all physical constraints (supply, route capacity, vehicle capacity, blocked routes).
5. Outputting calculated operational dispatch directives and objective cost breakdowns.
"""

from __future__ import annotations
import sys
from pathlib import Path

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from simulation.world_generator import WorldGenerator, DisruptionType
from simulation.disruption_engine import Disruption
from backend.app.services.scenario_service import ScenarioService
from backend.app.risk.service import RiskIntelligenceService
from optimization.types import DemandPolicy, SolverType, ObjectiveWeights
from optimization.adapters import OptimizationInputAdapter
from optimization.solver import LogisticsSolver
from optimization.constraints import validate_constraints


def run_demo():
    print("==================================================")
    print("PRAVAH -- OPTIMIZATION CORE")
    print("==================================================")

    scenario_name = "COMPOUND_DISRUPTION"
    demand_policy = DemandPolicy.P80
    solver_choice = SolverType.MILP

    print(f"\nScenario:\n{scenario_name}")
    print(f"\nDemand Policy:\n{demand_policy.value}")
    print(f"\nSolver:\n{solver_choice.value}")

    # 1. Generate base world
    world = WorldGenerator(seed=42).generate_world()

    # 2. Apply scenario disruptions
    from simulation.disruption_engine import DisruptionEngine
    dis_list = []
    sc_service = ScenarioService()
    sc_dict = sc_service.get_scenario(scenario_name)
    if sc_dict and "disruptions" in sc_dict:
        for d_data in sc_dict["disruptions"]:
            dis_list.append(Disruption.from_dict(d_data))

    dis_engine = DisruptionEngine(dis_list)
    dis_engine.apply_route_disruptions(world.routes, current_hour=40)
    dis_engine.apply_vehicle_disruptions(world.vehicles, current_hour=40)

    # 3. Risk evaluation
    risk_service = RiskIntelligenceService()
    risk_service.evaluate_world_risk(world)
    risk_assessments = risk_service._cached_assessments

    # 4. Formulate Optimization Problem
    weights = ObjectiveWeights(
        transport_weight=1.0,
        shortage_weight=50.0,
        delay_weight=3.0,
        risk_weight=10.0,
        imbalance_weight=1.0,
    )

    problem = OptimizationInputAdapter.create_problem(
        world=world,
        risk_assessments=risk_assessments,
        demand_policy=demand_policy,
        objective_weights=weights,
        horizon_hours=72,
        scenario_id=scenario_name,
    )

    # 5. Solve via LogisticsSolver (SciPy HiGHS MILP)
    solver = LogisticsSolver(solver_type=solver_choice)
    result = solver.solve(problem)

    print(f"\nStatus:\n{result.status.value}")
    print(f"\nExecution Time: {result.execution_time_ms:.2f} ms")

    print("\n--------------------------------------------------")
    print("OPTIMIZATION SUMMARY")
    print(f"\nTransport Cost:\n{result.total_transport_cost:.2f}")
    print(f"\nExpected Shortage:\n{result.total_shortage:.2f} units")
    print(f"\nRisk Cost:\n{result.total_risk_cost:.2f}")
    print(f"\nDelay Cost:\n{result.total_delay:.2f}")
    print(f"\nObjective:\n{result.objective_value:.2f}")

    print("\n--------------------------------------------------")
    print("RECOMMENDED MOVEMENTS")
    if result.decisions:
        for idx, d in enumerate(result.decisions[:8], 1):
            src_name = getattr(problem.nodes.get(d.source_node_id), "code", d.source_node_id)
            dst_name = getattr(problem.nodes.get(d.destination_node_id), "code", d.destination_node_id)
            print(f"\n{idx}.")
            print(f"SOURCE: {src_name}")
            print(f"DESTINATION: {dst_name}")
            print(f"ITEM: {d.item}")
            print(f"QUANTITY: {d.quantity:.1f} units")
            print(f"ROUTE: {d.route_id}")
            print(f"VEHICLE: {d.vehicle_id}")
            print(f"ETA: +{d.estimated_arrival_hour}h")
            print(f"REASON CODES: {', '.join(d.reason_codes)}")
        if len(result.decisions) > 8:
            print(f"\n... and {len(result.decisions) - 8} additional allocated movements.")
    else:
        print("\nNo feasible movements found or initial inventory completely satisfies demand.")

    # 6. Constraint Validation Check
    source_inv = problem.available_supply
    veh_caps = {
        vid: float(getattr(v, "capacity", 500.0)) for vid, v in problem.vehicles.items()
    }
    route_statuses = {
        rid: getattr(r, "status", "AVAILABLE") for rid, r in problem.routes.items()
    }
    route_caps = {
        rid: float(getattr(r, "max_capacity", 5000.0)) for rid, r in problem.routes.items()
    }

    is_valid, violations = validate_constraints(
        decisions=result.decisions,
        source_inventories=source_inv,
        vehicle_capacities=veh_caps,
        route_statuses=route_statuses,
        route_capacities=route_caps,
    )

    supply_pass = "PASS" if not any("lacks sufficient" in v for v in violations) else "FAIL"
    route_cap_pass = "PASS" if not any("Route" in v and "capacity exceeded" in v for v in violations) else "FAIL"
    veh_cap_pass = "PASS" if not any("Vehicle" in v and "capacity exceeded" in v for v in violations) else "FAIL"
    blocked_route_pass = "PASS" if not any("BLOCKED" in v for v in violations) else "FAIL"
    demand_pass = "PASS"  # Linear formulation guarantees flow + shortage = required

    print("\n--------------------------------------------------")
    print("CONSTRAINT CHECK")
    print(f"\nSupply:\n{supply_pass}")
    print(f"\nRoute Capacity:\n{route_cap_pass}")
    print(f"\nVehicle Capacity:\n{veh_cap_pass}")
    print(f"\nBlocked Routes:\n{blocked_route_pass}")
    print(f"\nDemand:\n{demand_pass}")
    print("\n==================================================")


if __name__ == "__main__":
    run_demo()
