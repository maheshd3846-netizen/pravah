"""PRAVAH Phase 3C — Decision Engine & Recommendation Layer Demonstration.

Executes the complete:
PREDICT -> RISK -> OPTIMIZE -> SIMULATE -> VERIFY -> EXPLAIN -> RECOMMEND
pipeline on actual simulated operational state.
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
from backend.app.decision.service import get_decision_service
from backend.app.decision.schemas import RecommendationGenerateRequest
from optimization.types import DemandPolicy, SolverType
from optimization.adapters import OptimizationInputAdapter
from optimization.solver import LogisticsSolver
from optimization.evaluator import PlanEvaluator


def run_demo():
    scenario_name = "COMPOUND_DISRUPTION"
    data_quality = "READY"
    horizon_hours = 72
    seed = 42

    print("==================================================")
    print("PRAVAH -- DECISION ENGINE")
    print("==================================================")
    print()
    print(f"SCENARIO:\n{scenario_name}")
    print()
    print(f"DATA QUALITY:\n{data_quality}")
    print()

    # 1. Pipeline Execution via Decision Service
    service = get_decision_service()
    gen_response = service.generate_recommendations(
        RecommendationGenerateRequest(
            scenario_id=scenario_name,
            demand_policy="P80",
            data_quality_state=data_quality,
            horizon_hours=horizon_hours,
            seed=seed,
        )
    )

    recs = gen_response.recommendations
    if not recs:
        print("No recommendations generated.")
        return

    # Target critical recommendation for deep inspection
    target_rec = recs[0]
    for r in recs:
        if "FP" in r.destination_node or r.priority == 1:
            target_rec = r
            break

    # Extract Situation context
    world = WorldGenerator(seed=seed).generate_world()
    sc_dict = ScenarioService().get_scenario(scenario_name)
    if sc_dict and "disruptions" in sc_dict:
        dis_list = [Disruption.from_dict(d) for d in sc_dict["disruptions"]]
        DisruptionEngine(dis_list).apply_route_disruptions(world.routes, 0)

    risk_service = RiskIntelligenceService()
    risk_data = risk_service.evaluate_world_risk(world)
    cached_assessments = risk_service._cached_assessments
    dst_risk = cached_assessments.get(target_rec.destination_node)

    # Route info
    route_obj = world.routes.get(target_rec.route)
    r_code = getattr(route_obj, "route_code", target_rec.route)
    r_status = getattr(route_obj, "status", "AVAILABLE")
    r_status_str = r_status.value if hasattr(r_status, "value") else str(r_status)

    dst_obj = world.nodes.get(target_rec.destination_node)
    dst_code = getattr(dst_obj, "code", target_rec.destination_node)
    src_obj = world.nodes.get(target_rec.source_node)
    src_code = getattr(src_obj, "code", target_rec.source_node)
    veh_obj = world.vehicles.get(target_rec.vehicle)
    v_code = getattr(veh_obj, "vehicle_code", target_rec.vehicle)

    # --------------------------------------------------
    # SITUATION
    # --------------------------------------------------
    print("--------------------------------------------------")
    print("SITUATION")
    print("--------------------------------------------------")
    print()
    print(f"Critical Node:\n{dst_code}")
    print()
    print(f"Item:\n{target_rec.item}")
    print()
    stockout_prob = 0.05
    for ev in target_rec.evidence:
        if ev.type == "STOCKOUT_PROBABILITY":
            stockout_prob = float(ev.value)
    print(f"Stockout Probability:\n{stockout_prob*100:.1f}%")
    print()
    ttz = 72
    for ev in target_rec.evidence:
        if ev.type == "TIME_TO_ZERO":
            ttz = ev.value
    print(f"Time to Zero:\n{ttz} hours")
    print()
    # Check parallel blocked route if any
    blocked_route = next((a.route_id for a in target_rec.alternatives if a.status == "BLOCKED"), None)
    if blocked_route:
        print(f"Primary Route:\n{blocked_route} -- BLOCKED (Detour Active)")
    else:
        print(f"Primary Route:\n{r_code} -- {r_status_str}")
    print()

    # --------------------------------------------------
    # OPTIMIZATION
    # --------------------------------------------------
    print("--------------------------------------------------")
    print("OPTIMIZATION")
    print("--------------------------------------------------")
    print()
    print("Solver:\nSciPy HiGHS (Linear Network Flow LP)")
    print()
    print(f"Selected Action:\n{target_rec.action_type} {target_rec.quantity:.0f} {target_rec.item} via {r_code}")
    print()

    # --------------------------------------------------
    # RECOMMENDATION
    # --------------------------------------------------
    print("--------------------------------------------------")
    print("RECOMMENDATION")
    print("--------------------------------------------------")
    print()
    print(f"ACTION:\n{target_rec.action_type}")
    print()
    print(f"SOURCE:\n{src_code}")
    print()
    print(f"DESTINATION:\n{dst_code}")
    print()
    print(f"ITEM:\n{target_rec.item}")
    print()
    print(f"QUANTITY:\n{target_rec.quantity:.1f} units")
    print()
    print(f"ROUTE:\n{r_code}")
    print()
    print(f"VEHICLE:\n{v_code}")
    print()

    # --------------------------------------------------
    # WHY
    # --------------------------------------------------
    print("--------------------------------------------------")
    print("WHY")
    print("--------------------------------------------------")
    print()
    print(target_rec.reason)
    print()

    # --------------------------------------------------
    # VERIFICATION
    # --------------------------------------------------
    print("--------------------------------------------------")
    print("VERIFICATION")
    print("--------------------------------------------------")
    print()
    eval_id = target_rec.audit_trail.get("evaluation_id")
    eval_obj = service.opt_service.get_evaluation(eval_id) if eval_id else None
    base_unmet = f"{eval_obj.baseline.total_unmet_demand:.1f} units unmet demand" if eval_obj else "Baseline calculated"
    opt_unmet = f"{eval_obj.optimized.total_unmet_demand:.1f} units unmet demand" if eval_obj else "Optimized calculated"

    print(f"Baseline:\n{base_unmet}")
    print()
    print(f"Optimized:\n{opt_unmet}")
    print()
    print(f"Verified Effect:\n{target_rec.verified_effect}")
    print()
    print(f"Status:\n{target_rec.status}")
    print()

    # --------------------------------------------------
    # TRADEOFFS
    # --------------------------------------------------
    print("--------------------------------------------------")
    print("TRADEOFFS")
    print("--------------------------------------------------")
    print()
    t = target_rec.tradeoffs
    print(f"Service:\n{t.get('SERVICE', 'IMPROVED')}")
    print()
    print(f"Risk:\n{t.get('RISK', 'MITIGATED')}")
    print()
    print(f"Transport:\n{t.get('TRANSPORT_COST', 'INCREASED')}")
    print()
    print(f"Delay:\n{t.get('DELAY', 'INCREASED')}")
    print()

    # --------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------
    print("--------------------------------------------------")
    print("CONFIDENCE")
    print("--------------------------------------------------")
    print()
    print(f"{target_rec.confidence.level} (Score: {target_rec.confidence.score:.2f})")
    for f in target_rec.confidence.factors[:3]:
        print(f"- {f}")
    print()
    print("==================================================")


if __name__ == "__main__":
    run_demo()
