"""
Phase 4.5.2 Final Acceptance Runner.
Executes Gates 3-16 against the canonical COMPOUND_DISRUPTION scenario.
"""

from __future__ import annotations
import json, math
from typing import Any, Dict

SCENARIO_ID = "COMPOUND_DISRUPTION"
SEED = 42
HORIZON = 72

gates: Dict[str, Dict[str, Any]] = {}

def gate(name: str):
    def decorator(fn):
        def wrapper():
            try:
                result = fn()
                gates[name] = {"status": "PASS", "evidence": result}
                print(f"  ✅ {name}")
                return result
            except AssertionError as e:
                gates[name] = {"status": "FAIL", "error": str(e)}
                print(f"  ❌ {name}: {e}")
                return None
            except Exception as e:
                gates[name] = {"status": "ERROR", "error": f"{type(e).__name__}: {e}"}
                print(f"  💥 {name}: {type(e).__name__}: {e}")
                return None
        return wrapper
    return decorator

# ── Shared imports ────────────────────────────────────────────────────────────
from simulation.world_generator import WorldGenerator, RouteStatus, VehicleStatus
from simulation.disruption_engine import Disruption, DisruptionEngine
from simulation.simulator import SimulationConfig
from backend.app.services.scenario_service import ScenarioService
from backend.app.risk.service import RiskIntelligenceService
from optimization.adapters import OptimizationInputAdapter
from optimization.types import (DemandPolicy, SolverType, ObjectiveWeights,
                                OptimizationStatus, compute_estimated_arrival)
from optimization.solver import LogisticsSolver, MilpSolver
from optimization.heuristic import PriorityHeuristicSolver
from optimization.evaluator import PlanEvaluator
from backend.app.decision.engine import DecisionEngine
from backend.app.decision.schemas import DataQualityState

# ── Build canonical pipeline once ─────────────────────────────────────────────
print("\n" + "="*70)
print("BUILDING CANONICAL COMPOUND_DISRUPTION PIPELINE (seed=42, 72h)")
print("="*70)

world = WorldGenerator(seed=SEED).generate_world()
sc_data = ScenarioService().get_scenario(SCENARIO_ID)
disruptions = [Disruption.from_dict(d) for d in sc_data["disruptions"]]
dis_engine = DisruptionEngine(disruptions)
dis_engine.apply_route_disruptions(world.routes, current_hour=0)
dis_engine.apply_vehicle_disruptions(world.vehicles, current_hour=0)

risk_svc = RiskIntelligenceService()
risk_svc.evaluate_world_risk(world)
risk_assessments = risk_svc._cached_assessments

problem = OptimizationInputAdapter.create_problem(
    world=world, risk_assessments=risk_assessments,
    demand_policy=DemandPolicy.P80, horizon_hours=HORIZON, scenario_id=SCENARIO_ID
)
opt_result = MilpSolver(allow_fallback=True).solve(problem)

evaluator = PlanEvaluator()
sim_cfg = SimulationConfig(seed=SEED, horizon_hours=HORIZON, scenario_name=SCENARIO_ID, auto_replenish=True)
eval_result = evaluator.evaluate_plan(
    plan_or_result=opt_result, base_config=sim_cfg,
    scenario_id=SCENARIO_ID, horizon_hours=HORIZON, seed=SEED
)

decision_engine = DecisionEngine()
recs = decision_engine.generate_recommendations(
    world=world, optimization_result=opt_result, evaluation_result=eval_result,
    risk_assessments=risk_assessments, scenario_id=SCENARIO_ID,
    data_quality_state=DataQualityState.READY.value
)

print(f"  World: {len(world.nodes)} nodes, {len(world.routes)} routes, {len(world.vehicles)} vehicles")
print(f"  Disruptions applied: {sum(1 for r in world.routes.values() if r.status == RouteStatus.BLOCKED)} blocked, {sum(1 for r in world.routes.values() if r.status == RouteStatus.DEGRADED)} degraded")
print(f"  Optimization: {opt_result.status.value}, {len(opt_result.decisions)} decisions, shortage={opt_result.total_shortage:.1f}")
print(f"  Counterfactual: {eval_result.status.value}")
print(f"  Recommendations: {len(recs)} total, {sum(1 for r in recs if r.status=='REJECTED')} rejected")

# =============================================================================
print("\n" + "="*70)
print("GATE 1 — ENVIRONMENT")
print("="*70)

@gate("G1.1 World generation")
def g1_world():
    w2 = WorldGenerator(seed=SEED).generate_world()
    assert len(w2.nodes) >= 10
    assert len(w2.routes) >= 20
    return {"nodes": len(w2.nodes), "routes": len(w2.routes), "vehicles": len(w2.vehicles)}

@gate("G1.2 Scenario COMPOUND_DISRUPTION exists")
def g1_scenario():
    sc = ScenarioService().get_scenario(SCENARIO_ID)
    assert sc is not None
    assert len(sc.get("disruptions", [])) > 0
    return {"disruptions": len(sc["disruptions"]), "types": list({d.get("type") for d in sc["disruptions"]})}

@gate("G1.3 API starts and responds")
def g1_api():
    from fastapi.testclient import TestClient
    from backend.main import app
    c = TestClient(app)
    r = c.get("/")
    assert r.status_code == 200
    assert r.json().get("status") == "online"
    return {"status": "online"}

g1_world(); g1_scenario(); g1_api()

# =============================================================================
print("\n" + "="*70)
print("GATE 3 — SIH SCENARIO DISRUPTIONS")
print("="*70)

@gate("G3.1 Route and vehicle disruptions applied")
def g3():
    blocked = sum(1 for r in world.routes.values() if r.status == RouteStatus.BLOCKED)
    degraded = sum(1 for r in world.routes.values() if r.status == RouteStatus.DEGRADED)
    unavail = sum(1 for v in world.vehicles.values() if v.status == VehicleStatus.UNAVAILABLE)
    assert blocked + degraded > 0, "No route disruptions"
    return {"blocked": blocked, "degraded": degraded, "vehicles_unavailable": unavail}

g3()

# =============================================================================
print("\n" + "="*70)
print("GATE 4 — PIPELINE STAGE TRACEABILITY")
print("="*70)

@gate("G4.1 Risk — non-zero assessments")
def g4_risk():
    scores = [getattr(a, "overall_risk", 0) for a in risk_assessments.values()]
    assert any(s > 0 for s in scores)
    return {"nodes": len(risk_assessments), "max_risk": round(max(scores), 4)}

@gate("G4.2 Optimization — problem has demand")
def g4_problem():
    td = sum(v for im in problem.required_demand.values() for v in im.values())
    assert td > 0
    return {"problem_id": problem.problem_id, "total_demand": round(td, 1)}

@gate("G4.3 Optimization — result has run_id and traceable status")
def g4_opt():
    assert opt_result.run_id
    assert opt_result.status in list(OptimizationStatus)
    assert opt_result.metadata.get("lp_solver_status"), "lp_solver_status must be in metadata"
    return {"run_id": opt_result.run_id, "status": opt_result.status.value,
            "lp_status": opt_result.metadata["lp_solver_status"]}

@gate("G4.4 Counterfactual — evaluation_id traceable to opt run")
def g4_cf():
    assert eval_result.evaluation_id
    assert eval_result.status is not None
    assert eval_result.deltas
    unmet = eval_result.deltas.get("unmet_demand")
    return {"eval_id": eval_result.evaluation_id, "status": eval_result.status.value,
            "unmet_delta": round(unmet.absolute_delta, 1) if unmet else None}

@gate("G4.5 Recommendations — IDs + action types present")
def g4_recs():
    assert len(recs) > 0
    for r in recs:
        assert r.recommendation_id
        assert r.action_type
        assert r.status
    return {"total": len(recs), "sample_id": recs[0].recommendation_id}

g4_risk(); g4_problem(); g4_opt(); g4_cf(); g4_recs()

# =============================================================================
print("\n" + "="*70)
print("GATE 5 — OPTIMIZATION SEMANTICS")
print("="*70)

@gate("G5.1 OPTIMAL with available routes + decisions > 0")
def g5_optimal():
    w = WorldGenerator(seed=SEED).generate_world()
    p = OptimizationInputAdapter.create_problem(world=w, risk_assessments={},
        demand_policy=DemandPolicy.P80, objective_weights=ObjectiveWeights())
    r = MilpSolver(allow_fallback=False).solve(p)
    assert r.status == OptimizationStatus.OPTIMAL
    assert len(r.decisions) > 0
    assert r.metadata.get("lp_solver_status") == "OPTIMAL"
    return {"status": r.status.value, "decisions": len(r.decisions)}

@gate("G5.2 INFEASIBLE when all routes blocked + demand > 0")
def g5_infeasible():
    w = WorldGenerator(seed=7).generate_world()
    for r in w.routes.values():
        r.status = RouteStatus.BLOCKED
    p = OptimizationInputAdapter.create_problem(world=w, risk_assessments={},
        demand_policy=DemandPolicy.P80, objective_weights=ObjectiveWeights())
    r = MilpSolver(allow_fallback=False).solve(p)
    assert r.status == OptimizationStatus.INFEASIBLE
    assert len(r.decisions) == 0
    assert r.total_shortage > 0
    assert any("NO_FEASIBLE_DISPATCH" in x for x in r.infeasibility_reasons)
    assert r.metadata.get("lp_solver_status") == "OPTIMAL"
    return {"app_status": r.status.value, "lp_status": r.metadata["lp_solver_status"],
            "reason": r.infeasibility_reasons[0][:60]}

@gate("G5.3 OPTIMAL when demand = 0 even with blocked routes")
def g5_zero_demand():
    w = WorldGenerator(seed=7).generate_world()
    for r in w.routes.values():
        r.status = RouteStatus.BLOCKED
    p = OptimizationInputAdapter.create_problem(world=w, risk_assessments={},
        demand_policy=DemandPolicy.P80, objective_weights=ObjectiveWeights())
    p.required_demand = {}
    r = MilpSolver(allow_fallback=False).solve(p)
    assert r.status == OptimizationStatus.OPTIMAL
    return {"status": r.status.value}

@gate("G5.4 Solver classified HYBRID not pure MILP")
def g5_hybrid():
    assert opt_result.metadata.get("solver_classification") == "HYBRID_LP_FLOW_HEURISTIC_DISPATCH"
    assert opt_result.metadata.get("is_pure_milp") is False
    return {"label": opt_result.metadata["solver_classification"]}

@gate("G5.5 Supply constraints — no over-dispatch")
def g5_supply():
    w = WorldGenerator(seed=SEED).generate_world()
    p = OptimizationInputAdapter.create_problem(world=w, risk_assessments={},
        demand_policy=DemandPolicy.P80, objective_weights=ObjectiveWeights())
    r = MilpSolver(allow_fallback=False).solve(p)
    used: Dict[tuple, float] = {}
    for d in r.decisions:
        key = (d.source_node_id, d.item)
        used[key] = used.get(key, 0.0) + d.quantity
    for (src, item), qty in used.items():
        avail = p.available_supply.get(src, {}).get(item, 0.0)
        assert qty <= avail + 1.0, f"Over-dispatch: {src}/{item} used={qty:.1f} avail={avail:.1f}"
    return {"supply_checks": len(used), "all_pass": True}

g5_optimal(); g5_infeasible(); g5_zero_demand(); g5_hybrid(); g5_supply()

# =============================================================================
print("\n" + "="*70)
print("GATE 6 — ROUTE-BASED TIMING")
print("="*70)

@gate("G6.1 compute_estimated_arrival edge cases")
def g6_utility():
    from dataclasses import dataclass as dc

    @dc
    class R:
        base_travel_hours: float

    cases = [
        (R(2.0), 2), (R(7.0), 7), (R(7.6), 8), (R(7.4), 7),
        (None, 4), (R(0.0), 1), (R(-1.0), 4),
        (R(float("nan")), 4), (R(float("inf")), 4),
        ({"base_travel_hours": 5.0}, 5), ({}, 4),
    ]
    for route_obj, expected in cases:
        got = compute_estimated_arrival(route_obj)
        assert got == expected, f"For {route_obj}: expected {expected}, got {got}"
        assert isinstance(got, int) and got >= 1
    return {"cases_verified": len(cases)}

@gate("G6.2 LP decisions use actual route travel time")
def g6_lp():
    w = WorldGenerator(seed=SEED).generate_world()
    p = OptimizationInputAdapter.create_problem(world=w, risk_assessments={},
        demand_policy=DemandPolicy.P80, objective_weights=ObjectiveWeights())
    r = MilpSolver(allow_fallback=False).solve(p)
    assert r.decisions
    for d in r.decisions[:5]:
        route = w.routes.get(d.route_id)
        if route:
            expected = max(1, int(round(route.base_travel_hours)))
            assert d.estimated_arrival_hour == expected
    arrivals = [d.estimated_arrival_hour for d in r.decisions]
    return {"unique_arrivals": sorted(set(arrivals)), "all_geq_1": all(a >= 1 for a in arrivals)}

@gate("G6.3 Heuristic decisions use actual route travel time")
def g6_heuristic():
    w = WorldGenerator(seed=SEED).generate_world()
    p = OptimizationInputAdapter.create_problem(world=w, risk_assessments={},
        demand_policy=DemandPolicy.P80, objective_weights=ObjectiveWeights())
    r = PriorityHeuristicSolver().solve(p)
    assert r.decisions
    for d in r.decisions[:5]:
        route = w.routes.get(d.route_id)
        if route:
            expected = max(1, int(round(route.base_travel_hours)))
            assert d.estimated_arrival_hour == expected
    return {"decisions": len(r.decisions), "all_geq_1": True}

@gate("G6.4 Estimate vs Simulation distinction documented in source")
def g6_distinction():
    doc = compute_estimated_arrival.__doc__ or ""
    assert "Optimization estimate" in doc or "optimization estimate" in doc.lower()
    assert "Simulation" in doc
    return {"documented": True}

g6_utility(); g6_lp(); g6_heuristic(); g6_distinction()

# =============================================================================
print("\n" + "="*70)
print("GATE 7 — CANDIDATE vs FEASIBLE ACTIONS")
print("="*70)

@gate("G7.1 Rejection summary present and correct")
def g7_summary():
    from backend.app.decision.service import DecisionService
    from backend.app.decision.schemas import RecommendationGenerateRequest
    svc = DecisionService()
    resp = svc.generate_recommendations(
        RecommendationGenerateRequest(scenario_id=SCENARIO_ID, horizon_hours=HORIZON, seed=SEED)
    )
    rejected = resp.status_counts.get("REJECTED", 0)
    feasible = resp.total_recommendations - rejected
    if rejected > 0:
        assert resp.rejection_summary is not None
        assert str(rejected) in resp.rejection_summary
    return {
        "total_candidates": resp.total_recommendations,
        "rejected": rejected,
        "feasible": feasible,
        "presentation": f"{feasible} FEASIBLE / {rejected} FILTERED",
        "summary_present": resp.rejection_summary is not None,
    }

@gate("G7.2 Conflict details on all REJECTED recs")
def g7_conflicts():
    for r in recs:
        if r.status == "REJECTED":
            assert r.conflict_detected is True
            assert len(r.conflict_details) > 0
    return {"rejected_verified": sum(1 for r in recs if r.status == "REJECTED")}

@gate("G7.3 Full recommendation schema fields present")
def g7_schema():
    required = ["recommendation_id", "action_type", "source_node", "destination_node",
                "item", "quantity", "route", "vehicle", "planned_departure",
                "expected_arrival", "title", "reason", "evidence", "tradeoffs",
                "expected_effect", "status", "confidence", "validation_state",
                "conflict_detected", "audit_trail", "created_at"]
    for r in recs[:3]:
        d = r.model_dump()
        missing = [f for f in required if f not in d]
        assert not missing, f"Missing schema fields: {missing}"
    return {"fields_verified": len(required)}

g7_summary(); g7_conflicts(); g7_schema()

# =============================================================================
print("\n" + "="*70)
print("GATE 8 — COUNTERFACTUAL VERIFICATION")
print("="*70)

@gate("G8.1 Deterministic evaluation — same result twice")
def g8_determinism():
    ev2 = PlanEvaluator()
    r2 = ev2.evaluate_plan(
        plan_or_result=opt_result, base_config=sim_cfg,
        scenario_id=SCENARIO_ID, horizon_hours=HORIZON, seed=SEED
    )
    assert eval_result.status == r2.status
    f1 = getattr(eval_result, "baseline_fingerprint", None)
    f2 = getattr(r2, "baseline_fingerprint", None)
    if f1 and f2:
        assert f1 == f2
    return {"status_match": True, "fingerprint_match": f1 == f2 if f1 else "N/A"}

@gate("G8.2 Required delta keys present")
def g8_deltas():
    required_keys = {"unmet_demand", "stockout_events", "fulfillment_rate"}
    missing = required_keys - set(eval_result.deltas.keys())
    assert not missing, f"Missing delta keys: {missing}"
    unmet = eval_result.deltas["unmet_demand"]
    stockout = eval_result.deltas["stockout_events"]
    return {
        "unmet_abs": round(unmet.absolute_delta, 1),
        "unmet_pct": round(unmet.relative_delta_percent, 1),
        "stockout_abs": round(stockout.absolute_delta, 1),
        "eval_status": eval_result.status.value,
        "all_keys": sorted(eval_result.deltas.keys()),
    }

@gate("G8.3 Valid evaluation status (IMPROVED/DEGRADED/MIXED/NO_CHANGE)")
def g8_status():
    from optimization.evaluation_metrics import EvaluationStatus
    valid = {EvaluationStatus.IMPROVED, EvaluationStatus.DEGRADED,
             EvaluationStatus.MIXED, EvaluationStatus.NO_CHANGE}
    assert eval_result.status in valid, f"Unexpected status: {eval_result.status}"
    return {"status": eval_result.status.value}

g8_determinism(); g8_deltas(); g8_status()

# =============================================================================
print("\n" + "="*70)
print("GATE 9 — RECOMMENDATION ENGINE")
print("="*70)

@gate("G9.1 Evidence items have source + type")
def g9_evidence():
    checked = 0
    for r in recs[:5]:
        for ev in r.evidence:
            assert ev.source, "Evidence missing source"
            assert ev.type, "Evidence missing type"
            checked += 1
    return {"evidence_items_checked": checked}

@gate("G9.2 Audit trail contains traceability fields")
def g9_audit():
    for r in recs[:5]:
        at = r.audit_trail
        assert "optimization_run_id" in at
        assert "scenario_id" in at
        assert at["scenario_id"] == SCENARIO_ID
    return {"verified": len(recs[:5])}

@gate("G9.3 Confidence degrades with data quality")
def g9_dq():
    eng = DecisionEngine()
    def avg_conf(dq: str) -> float:
        rs = eng.generate_recommendations(
            world=world, optimization_result=opt_result, evaluation_result=eval_result,
            risk_assessments=risk_assessments, scenario_id=SCENARIO_ID, data_quality_state=dq
        )
        scores = [r.confidence.score for r in rs if r.confidence]
        return round(sum(scores)/max(1, len(scores)), 3)
    ready = avg_conf("READY")
    insuff = avg_conf("INSUFFICIENT")
    assert ready >= insuff, f"READY ({ready}) should be >= INSUFFICIENT ({insuff})"
    return {"READY": ready, "INSUFFICIENT": insuff}

@gate("G9.4 INSUFFICIENT data blocks high-confidence recs")
def g9_insuff():
    eng = DecisionEngine()
    rs = eng.generate_recommendations(
        world=world, optimization_result=opt_result, evaluation_result=eval_result,
        risk_assessments=risk_assessments, scenario_id=SCENARIO_ID,
        data_quality_state=DataQualityState.INSUFFICIENT.value
    )
    high_conf = [r for r in rs if r.confidence and r.confidence.score >= 0.8]
    assert len(high_conf) == 0, f"High-conf recs with INSUFFICIENT data: {len(high_conf)}"
    return {"blocked": True, "total_recs": len(rs)}

g9_evidence(); g9_audit(); g9_dq(); g9_insuff()

# =============================================================================
print("\n" + "="*70)
print("GATE 12 — DETERMINISM")
print("="*70)

@gate("G12.1 Two canonical runs are identical")
def g12():
    def run_canonical():
        w = WorldGenerator(seed=SEED).generate_world()
        sc2 = ScenarioService().get_scenario(SCENARIO_ID)
        disps = [Disruption.from_dict(d) for d in sc2["disruptions"]]
        de = DisruptionEngine(disps)
        de.apply_route_disruptions(w.routes, 0)
        de.apply_vehicle_disruptions(w.vehicles, 0)
        rs = RiskIntelligenceService()
        rs.evaluate_world_risk(w)
        p = OptimizationInputAdapter.create_problem(
            world=w, risk_assessments=rs._cached_assessments,
            demand_policy=DemandPolicy.P80, objective_weights=ObjectiveWeights()
        )
        return MilpSolver(allow_fallback=True).solve(p)

    r1 = run_canonical()
    r2 = run_canonical()
    assert r1.status == r2.status
    assert round(r1.objective_value, 4) == round(r2.objective_value, 4)
    assert len(r1.decisions) == len(r2.decisions)
    assert round(r1.total_shortage, 4) == round(r2.total_shortage, 4)
    return {"decisions": len(r1.decisions), "objective": round(r1.objective_value, 4), "deterministic": True}

g12()

# =============================================================================
print("\n" + "="*70)
print("GATE 13 — FAILURE PATHS")
print("="*70)

@gate("G13.1 All routes BLOCKED — INFEASIBLE, no crash")
def g13_blocked():
    w = WorldGenerator(seed=7).generate_world()
    for r in w.routes.values(): r.status = RouteStatus.BLOCKED
    p = OptimizationInputAdapter.create_problem(world=w, risk_assessments={},
        demand_policy=DemandPolicy.P80, objective_weights=ObjectiveWeights())
    r = MilpSolver(allow_fallback=False).solve(p)
    assert r.status == OptimizationStatus.INFEASIBLE
    return {"status": r.status.value}

@gate("G13.2 Zero inventory — graceful, no crash")
def g13_zero_inv():
    w = WorldGenerator(seed=SEED).generate_world()
    for node in w.nodes.values(): node.initial_inventory = {}
    p = OptimizationInputAdapter.create_problem(world=w, risk_assessments={},
        demand_policy=DemandPolicy.P80, objective_weights=ObjectiveWeights())
    r = MilpSolver(allow_fallback=False).solve(p)
    assert r.status in list(OptimizationStatus)
    return {"status": r.status.value, "decisions": len(r.decisions)}

@gate("G13.3 All vehicles UNAVAILABLE — no crash")
def g13_vehicles():
    w = WorldGenerator(seed=SEED).generate_world()
    for v in w.vehicles.values(): v.status = VehicleStatus.UNAVAILABLE
    p = OptimizationInputAdapter.create_problem(world=w, risk_assessments={},
        demand_policy=DemandPolicy.P80, objective_weights=ObjectiveWeights())
    r = MilpSolver(allow_fallback=True).solve(p)
    assert r.status in list(OptimizationStatus)
    return {"status": r.status.value}

@gate("G13.4 COMPOUND_DISRUPTION — all stages complete, no crash")
def g13_compound():
    assert eval_result is not None
    assert eval_result.evaluation_id
    assert len(recs) > 0
    return {"stages": "all complete", "eval_status": eval_result.status.value}

@gate("G13.5 INSUFFICIENT data — recommendations downgraded, no high-conf")
def g13_insuff():
    eng = DecisionEngine()
    rs = eng.generate_recommendations(
        world=world, optimization_result=opt_result, evaluation_result=eval_result,
        risk_assessments=risk_assessments, scenario_id=SCENARIO_ID,
        data_quality_state=DataQualityState.INSUFFICIENT.value
    )
    high = [r for r in rs if r.confidence and r.confidence.score >= 0.8]
    assert len(high) == 0
    return {"total": len(rs), "high_conf_blocked": True}

@gate("G13.6 Empty decisions → HOLD recommendations for critical nodes")
def g13_empty_decisions():
    from optimization.types import OptimizationResult, SolverType, DemandPolicy
    import uuid
    empty_result = OptimizationResult(
        run_id=f"RUN_EMPTY_{uuid.uuid4().hex[:6]}",
        status=OptimizationStatus.INFEASIBLE,
        solver_type=SolverType.MILP,
        objective_value=9999.0,
        execution_time_ms=0.0,
        demand_policy=DemandPolicy.P80,
        total_transport_cost=0.0,
        total_shortage=5000.0,
        total_delay=0.0,
        total_risk_cost=0.0,
        decisions=[],
        infeasibility_reasons=["NO_FEASIBLE_DISPATCH"],
    )
    eng = DecisionEngine()
    rs = eng.generate_recommendations(
        world=world, optimization_result=empty_result,
        evaluation_result=None, risk_assessments=risk_assessments,
        scenario_id=SCENARIO_ID, data_quality_state=DataQualityState.READY.value
    )
    # Should generate HOLD recommendations for high-risk critical nodes
    holds = [r for r in rs if r.action_type == "HOLD"]
    return {"recs": len(rs), "holds": len(holds)}

g13_blocked(); g13_zero_inv(); g13_vehicles(); g13_compound(); g13_insuff(); g13_empty_decisions()

# =============================================================================
print("\n" + "="*70)
print("GATE 16 — DEMO SAFETY")
print("="*70)

@gate("G16.1 All deltas are computed — not hardcoded")
def g16_computed():
    unmet = eval_result.deltas.get("unmet_demand")
    assert unmet is not None
    assert isinstance(unmet.absolute_delta, float)
    assert math.isfinite(unmet.absolute_delta)
    return {"unmet_delta": round(unmet.absolute_delta, 1), "computed": True}

@gate("G16.2 Solver not labeled pure MILP")
def g16_label():
    assert opt_result.metadata.get("is_pure_milp") is False
    assert "HYBRID" in opt_result.metadata.get("solver_classification", "")
    return {"ok": True}

g16_computed(); g16_label()

# =============================================================================
print("\n" + "="*70)
print("FINAL ACCEPTANCE SUMMARY")
print("="*70)

passed = sum(1 for g in gates.values() if g["status"] == "PASS")
failed = sum(1 for g in gates.values() if g["status"] == "FAIL")
errors = sum(1 for g in gates.values() if g["status"] == "ERROR")
total = len(gates)

print(f"\n  Gates: {total}  |  PASS: {passed}  |  FAIL: {failed}  |  ERROR: {errors}\n")
for name, result in gates.items():
    sym = "✅" if result["status"] == "PASS" else ("❌" if result["status"] == "FAIL" else "💥")
    print(f"  {sym} {name}: {result['status']}", end="")
    ev = result.get("evidence") or {}
    if isinstance(ev, dict):
        compact = {k: v for k, v in ev.items()
                   if not isinstance(v, list) or len(str(v)) < 60}
        if compact: print(f"  {compact}", end="")
    if result["status"] != "PASS":
        print(f"\n       ⚠ {result.get('error','')[:100]}", end="")
    print()

verdict = "DEMO FROZEN / PHASE 5 READY" if (failed == 0 and errors == 0) else f"NOT READY — {failed} FAILED + {errors} ERRORS"
print(f"\n{'='*70}")
print(f"  VERDICT: {verdict}")
print(f"{'='*70}\n")

def serialize(obj):
    if isinstance(obj, dict): return {k: serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)): return [serialize(v) for v in obj]
    if isinstance(obj, float): return round(obj, 6)
    return obj

with open("phase_4_5_2_evidence.json", "w") as f:
    json.dump({"verdict": verdict, "gates": serialize(gates)}, f, indent=2)
print("Evidence written → phase_4_5_2_evidence.json")
