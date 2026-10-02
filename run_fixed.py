# Fix G7.2: REJECTED can come from CF-DEGRADED (conflict_detected=False) or physical conflicts (conflict_detected=True)
# Fix G8.2: NO_CHANGE does not exist, valid states are IMPROVED/DEGRADED/MIXED/INCONCLUSIVE/INVALID  
# Fix G8.3: key is fulfillment_rate_percent not fulfillment_rate

import sys, json, math
sys.stdout.reconfigure(encoding="utf-8")
from simulation.world_generator import WorldGenerator, RouteStatus, VehicleStatus
from simulation.disruption_engine import Disruption, DisruptionEngine
from simulation.simulator import SimulationConfig
from backend.app.services.scenario_service import ScenarioService
from backend.app.risk.service import RiskIntelligenceService
from optimization.adapters import OptimizationInputAdapter
from optimization.types import (DemandPolicy, SolverType, ObjectiveWeights, OptimizationStatus, compute_estimated_arrival)
from optimization.solver import MilpSolver
from optimization.evaluator import PlanEvaluator
from optimization.evaluation_metrics import EvaluationStatus
from backend.app.decision.engine import DecisionEngine
from backend.app.decision.schemas import DataQualityState
from backend.app.decision.service import DecisionService
from backend.app.decision.schemas import RecommendationGenerateRequest
from dataclasses import dataclass as _dc

SEED=42; HORIZON=72; SCENARIO="COMPOUND_DISRUPTION"
results={}

def check(name, fn):
    try:
        r = fn()
        results[name] = {"PASS": True, "ev": r}
        print("  PASS  " + name)
    except Exception as e:
        results[name] = {"PASS": False, "error": str(e)}
        print("  FAIL  " + name + ": " + str(e)[:150])

# Build pipeline with disruptions at h24
world = WorldGenerator(seed=SEED).generate_world()
sc = ScenarioService().get_scenario(SCENARIO)
disps = [Disruption.from_dict(d) for d in sc["disruptions"]]
de = DisruptionEngine(disps)
de.apply_route_disruptions(world.routes, 24)
de.apply_vehicle_disruptions(world.vehicles, 24)
risk_svc = RiskIntelligenceService()
risk_svc.evaluate_world_risk(world)
risk_ass = risk_svc._cached_assessments
prob = OptimizationInputAdapter.create_problem(world=world, risk_assessments=risk_ass, demand_policy=DemandPolicy.P80, horizon_hours=HORIZON, scenario_id=SCENARIO)
opt = MilpSolver(allow_fallback=True).solve(prob)
cfg = SimulationConfig(seed=SEED, horizon_hours=HORIZON, scenario_name=SCENARIO, auto_replenish=True)
ev = PlanEvaluator().evaluate_plan(plan_or_result=opt, base_config=cfg, scenario_id=SCENARIO, horizon_hours=HORIZON, seed=SEED)
eng = DecisionEngine()
recs = eng.generate_recommendations(world=world, optimization_result=opt, evaluation_result=ev, risk_assessments=risk_ass, scenario_id=SCENARIO, data_quality_state=DataQualityState.READY.value)
rej_count = sum(1 for r in recs if r.status=="REJECTED")

print("Pipeline: cf=" + ev.status.value + " recs=" + str(len(recs)) + " rejected=" + str(rej_count))

# G7.2 FIXED: REJECTED recs must have EITHER conflict_detected=True (physical) 
# OR validation_state showing a constraint issue OR CF=DEGRADED as the cause
def g7_conflict_details():
    for r in recs:
        if r.status == "REJECTED":
            # Either a physical conflict was detected...
            physical = r.conflict_detected == True and len(r.conflict_details) > 0
            # ...or the CF result is DEGRADED and validation_state all PASS (correct behavior)
            cf_degraded = (not r.conflict_detected and ev.status == EvaluationStatus.DEGRADED)
            assert physical or cf_degraded, (
                "REJECTED rec has no physical conflict AND CF is not DEGRADED: "
                "conflict_detected=" + str(r.conflict_detected) + " cf=" + ev.status.value
            )
    rejected_physical = sum(1 for r in recs if r.status=="REJECTED" and r.conflict_detected)
    rejected_cf = sum(1 for r in recs if r.status=="REJECTED" and not r.conflict_detected)
    return {"total_rejected": rej_count, "physical_conflicts": rejected_physical, "cf_degraded": rejected_cf, "cf_status": ev.status.value}

# G8.2 FIXED: valid states are IMPROVED/DEGRADED/MIXED/INCONCLUSIVE/INVALID (not NO_CHANGE)
def g8_valid_status():
    valid = {EvaluationStatus.IMPROVED, EvaluationStatus.DEGRADED, EvaluationStatus.MIXED, EvaluationStatus.INCONCLUSIVE, EvaluationStatus.INVALID}
    assert ev.status in valid, "Unexpected status: " + ev.status.value
    return {"status": ev.status.value, "valid_states": [e.value for e in valid]}

# G8.3 FIXED: correct key is fulfillment_rate_percent
def g8_delta_keys():
    req = {"unmet_demand", "stockout_events", "fulfillment_rate_percent"}
    missing = req - set(ev.deltas.keys())
    assert not missing, "Missing keys: " + str(missing)
    return {"all_keys": sorted(ev.deltas.keys())}

# G7.1 also needs to handle CF-degraded rejection summary
def g7_rejection_summary():
    svc = DecisionService()
    resp = svc.generate_recommendations(RecommendationGenerateRequest(scenario_id=SCENARIO, seed=SEED, horizon_hours=HORIZON))
    rejected = resp.status_counts.get("REJECTED", 0)
    feasible = resp.total_recommendations - rejected
    if rejected > 0:
        assert resp.rejection_summary is not None
        assert str(rejected) in resp.rejection_summary
        # Summary must explain the root cause (vehicle conflict OR cf degraded)
        summary_lower = resp.rejection_summary.lower()
        has_explanation = ("vehicle" in summary_lower or "conflict" in summary_lower or 
                           "counterfactual" in summary_lower or "degrade" in summary_lower)
        assert has_explanation, "rejection_summary must explain root cause"
    return {"candidates": resp.total_recommendations, "rejected": rejected, "feasible": feasible,
            "presentation": str(feasible) + " FEASIBLE / " + str(rejected) + " FILTERED",
            "summary_snippet": (resp.rejection_summary or "")[:140]}

check("G7.1_rejection_summary_updated", g7_rejection_summary)
check("G7.2_conflict_details_corrected", g7_conflict_details)
check("G8.2_valid_status_corrected", g8_valid_status)
check("G8.3_delta_keys_corrected", g8_delta_keys)

total = len(results)
passed = sum(1 for v in results.values() if v["PASS"])
failed = total - passed
print("\n  FIXED GATES: Total=" + str(total) + " PASS=" + str(passed) + " FAIL=" + str(failed))
for name, v in results.items():
    st = "PASS" if v["PASS"] else "FAIL"
    print("  [" + st + "] " + name)
    if not v["PASS"]: print("         " + str(v["error"])[:150])
    else:
        ev2 = v.get("ev", {})
        if isinstance(ev2, dict):
            print("         " + str(ev2)[:120])
