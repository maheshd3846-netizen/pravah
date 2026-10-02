"""PRAVAH Phase 3B — Closed-Loop Counterfactual Plan Validation Demonstration.

Validates whether an optimizer plan improves simulated operational outcomes
by conducting paired simulations starting from identical state snapshots.
"""

from __future__ import annotations
import sys
from pathlib import Path

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from simulation.world_generator import WorldGenerator
from simulation.disruption_engine import Disruption, DisruptionEngine
from simulation.simulator import SimulationConfig
from backend.app.services.scenario_service import ScenarioService
from backend.app.risk.service import RiskIntelligenceService
from optimization.types import DemandPolicy, SolverType, ObjectiveWeights
from optimization.adapters import OptimizationInputAdapter
from optimization.solver import LogisticsSolver
from optimization.evaluator import PlanEvaluator


def run_demo():
    scenario_name = "COMPOUND_DISRUPTION"
    horizon_hours = 72
    demand_policy = DemandPolicy.P80
    seed = 42

    print("==================================================")
    print("PRAVAH -- CLOSED LOOP VALIDATION")
    print("==================================================")
    print()
    print(f"SCENARIO:\n{scenario_name}")
    print()
    print(f"HORIZON:\n{horizon_hours} HOURS")
    print()
    print(f"DEMAND POLICY:\n{demand_policy.value}")
    print()

    # --------------------------------------------------
    # STEP 1 -- PREDICT
    # --------------------------------------------------
    print("--------------------------------------------------")
    print("STEP 1 -- PREDICT")
    print("--------------------------------------------------")

    world = WorldGenerator(seed=seed).generate_world()
    sc_service = ScenarioService()
    sc_dict = sc_service.get_scenario(scenario_name)
    dis_list = []
    if sc_dict and "disruptions" in sc_dict:
        for d_data in sc_dict["disruptions"]:
            dis_list.append(Disruption.from_dict(d_data))

    dis_engine = DisruptionEngine(dis_list)
    dis_engine.apply_route_disruptions(world.routes, current_hour=0)
    dis_engine.apply_vehicle_disruptions(world.vehicles, current_hour=0)

    risk_service = RiskIntelligenceService()
    risk_service.evaluate_world_risk(world)
    risk_assessments = risk_service._cached_assessments
    critical_risks = [
        f"{a.node_code} (Risk={a.overall_risk:.2f}, Level={a.level})"
        for a in risk_assessments.values()
        if a.overall_risk >= 0.35 or a.level in ["CRITICAL", "HIGH"]
    ]
    avg_network_risk = (
        sum(a.overall_risk for a in risk_assessments.values()) / max(1, len(risk_assessments))
        if risk_assessments else 0.0
    )

    print()
    print("Stockout Risk:")
    print(f"  Network-Wide Composite Risk: {avg_network_risk:.3f}")
    print(f"  Critical Nodes at Risk: {len(critical_risks)}")
    for rk in critical_risks[:3]:
        print(f"    - {rk}")
    print()

    # --------------------------------------------------
    # STEP 2 -- OPTIMIZE
    # --------------------------------------------------
    print("--------------------------------------------------")
    print("STEP 2 -- OPTIMIZE")
    print("--------------------------------------------------")

    problem = OptimizationInputAdapter.create_problem(
        world=world,
        risk_assessments=risk_assessments,
        demand_policy=demand_policy,
        objective_weights=ObjectiveWeights(),
        horizon_hours=horizon_hours,
        scenario_id=scenario_name,
    )

    solver = LogisticsSolver(solver_type=SolverType.MILP)
    opt_result = solver.solve(problem)

    print()
    print("Solver:")
    solver_name = getattr(opt_result.solver_type, "value", str(opt_result.solver_type))
    status_str = getattr(opt_result.status, "value", str(opt_result.status))
    solve_sec = opt_result.execution_time_ms / 1000.0
    print(f"  {solver_name} (Status: {status_str}, Solve Time: {solve_sec:.4f}s)")
    print()
    print("Plan:")
    tot_vol = sum(d.quantity for d in opt_result.decisions)
    print(f"  Plan ID: {opt_result.run_id}")
    print(f"  Dispatched Decisions: {len(opt_result.decisions)}")
    print(f"  Total Volume Allocated: {tot_vol:.1f} units")
    print(f"  Objective Cost: {opt_result.objective_value:.2f}")
    print()

    # --------------------------------------------------
    # STEP 3 & 4 — COUNTERFACTUAL EVALUATION
    # --------------------------------------------------
    evaluator = PlanEvaluator()
    sim_cfg = SimulationConfig(
        seed=seed,
        horizon_hours=horizon_hours,
        scenario_name=scenario_name,
        auto_replenish=True,
    )

    evaluation = evaluator.evaluate_plan(
        plan_or_result=opt_result,
        base_config=sim_cfg,
        scenario_id=scenario_name,
        horizon_hours=horizon_hours,
        seed=seed,
    )

    base = evaluation.baseline
    opt = evaluation.optimized
    deltas = evaluation.deltas

    # --------------------------------------------------
    # STEP 3 -- BASELINE SIMULATION
    # --------------------------------------------------
    print("--------------------------------------------------")
    print("STEP 3 -- BASELINE SIMULATION")
    print("--------------------------------------------------")
    print()
    print("Unmet Demand:")
    print(f"  {base.total_unmet_demand:.1f} units (of {base.total_requested_demand:.1f} requested)")
    print()
    print("Stockout Events:")
    print(f"  {base.total_stockout_events} events ({base.stockout_duration_hours} hours total)")
    print()
    print("Fulfillment Rate:")
    print(f"  {base.fulfillment_rate_percent:.2f}%")
    print()

    # --------------------------------------------------
    # STEP 4 -- OPTIMIZED SIMULATION
    # --------------------------------------------------
    print("--------------------------------------------------")
    print("STEP 4 -- OPTIMIZED SIMULATION")
    print("--------------------------------------------------")
    print()
    print("Unmet Demand:")
    print(f"  {opt.total_unmet_demand:.1f} units")
    print()
    print("Stockout Events:")
    print(f"  {opt.total_stockout_events} events ({opt.stockout_duration_hours} hours total)")
    print()
    print("Fulfillment Rate:")
    print(f"  {opt.fulfillment_rate_percent:.2f}%")
    print()

    # --------------------------------------------------
    # STEP 5 -- COUNTERFACTUAL DELTA
    # --------------------------------------------------
    print("--------------------------------------------------")
    print("STEP 5 -- COUNTERFACTUAL DELTA")
    print("--------------------------------------------------")
    print()

    unmet_d = deltas.get("unmet_demand")
    if unmet_d:
        print("Unmet Demand:")
        print(f"  {unmet_d.absolute_delta:+.1f} units ({unmet_d.relative_delta_percent:+.2f}%) [{unmet_d.direction.value}]")
    print()

    so_d = deltas.get("stockout_events")
    if so_d:
        print("Stockout Events:")
        print(f"  {so_d.absolute_delta:+.0f} events ({so_d.relative_delta_percent:+.2f}%) [{so_d.direction.value}]")
    print()

    ful_d = deltas.get("fulfillment_rate_percent")
    if ful_d:
        print("Fulfillment:")
        print(f"  {ful_d.absolute_delta:+.2f}% points [{ful_d.direction.value}]")
    print()

    print("Risk:")
    print(f"  {evaluation.tradeoffs.get('RISK', 'N/A')}")
    print()

    del_d = deltas.get("average_delay_hours")
    if del_d:
        print("Delay:")
        print(f"  {del_d.absolute_delta:+.2f} hrs avg [{del_d.direction.value}]")
    print()

    # --------------------------------------------------
    # STEP 6 -- TRADEOFF
    # --------------------------------------------------
    print("--------------------------------------------------")
    print("STEP 6 -- TRADEOFF")
    print("--------------------------------------------------")
    print()
    dist_d = deltas.get("transport_distance_km")
    dist_val = f"{dist_d.absolute_delta:+.1f} km ({dist_d.relative_delta_percent:+.1f}%)" if dist_d else "0 km"
    print("Transport Distance:")
    print(f"  {dist_val} [{evaluation.tradeoffs.get('TRANSPORT_COST', 'N/A')}]")
    print()
    print("Risk:")
    print(f"  {evaluation.tradeoffs.get('RISK', 'N/A')}")
    print()
    print("Service:")
    print(f"  {evaluation.tradeoffs.get('SERVICE', 'N/A')}")
    print()

    # --------------------------------------------------
    # VERDICT
    # --------------------------------------------------
    print("--------------------------------------------------")
    print("VERDICT")
    print("--------------------------------------------------")
    print()
    print(evaluation.status.value)
    print()
    print("==================================================")


if __name__ == "__main__":
    run_demo()
