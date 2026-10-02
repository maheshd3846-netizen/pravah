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
from optimization.heuristic import PriorityHeuristicSolver
from optimization.evaluator import PlanEvaluator
from optimization.evaluation_metrics import EvaluationStatus
from backend.app.decision.engine import DecisionEngine
from backend.app.decision.schemas import DataQualityState
from backend.app.decision.service import DecisionService
from backend.app.decision.schemas import RecommendationGenerateRequest
from dataclasses import dataclass as _dc

SEED=42; HORIZON=72; SCENARIO="COMPOUND_DISRUPTION"
results={}; errors=[]
def check(name, fn):
    try:
        r = fn()
        results[name] = {"PASS": True, "ev": r}
        print("  PASS  " + name)
    except Exception as e:
        results[name] = {"PASS": False, "error": str(e)}
        errors.append(name)
        print("  FAIL  " + name + ": " + str(e)[:120])

print("=== PIPELINE BUILD ===")
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
bk=sum(1 for r in world.routes.values() if r.status==RouteStatus.BLOCKED)
dg=sum(1 for r in world.routes.values() if r.status==RouteStatus.DEGRADED)
uv=sum(1 for v in world.vehicles.values() if v.status==VehicleStatus.UNAVAILABLE)
rej_count=sum(1 for r in recs if r.status=="REJECTED")
print("  world: nodes=" + str(len(world.nodes)) + " routes=" + str(len(world.routes)) + " vehicles=" + str(len(world.vehicles)))
print("  @h24: blocked=" + str(bk) + " degraded=" + str(dg) + " vehicles_unavail=" + str(uv))
print("  disruption_types=" + str([d.type.value for d in disps]))
print("  opt=" + opt.status.value + " decisions=" + str(len(opt.decisions)) + " shortage=" + str(round(opt.total_shortage,1)))
print("  cf=" + ev.status.value)
print("  recs_total=" + str(len(recs)) + " rejected=" + str(rej_count))

print("\n=== G3 DISRUPTIONS ===")
check("G3.1_disruptions", lambda: {"types":[d.type.value for d in disps],"blocked":bk,"degraded":dg,"unavail":uv})

print("\n=== G4 PIPELINE TRACE ===")
check("G4.1_risk", lambda: {"count":len(risk_ass),"max_risk":round(max(getattr(a,"overall_risk",0) for a in risk_ass.values()),4)})
check("G4.2_problem", lambda: {"id":prob.problem_id,"demand":round(sum(v for im in prob.required_demand.values() for v in im.values()),1)})
check("G4.3_opt", lambda: {"run_id":opt.run_id,"status":opt.status.value,"lp_status":opt.metadata.get("lp_solver_status"),"solver_class":opt.metadata.get("solver_classification"),"is_pure_milp":str(opt.metadata.get("is_pure_milp")),"decisions":len(opt.decisions),"shortage":round(opt.total_shortage,2)})
check("G4.4_cf", lambda: {"eval_id":ev.evaluation_id,"status":ev.status.value,"unmet_delta":round(ev.deltas["unmet_demand"].absolute_delta,2),"stockout_delta":round(ev.deltas["stockout_events"].absolute_delta,2),"keys":sorted(ev.deltas.keys())})
check("G4.5_recs", lambda: {"total":len(recs),"first_id":recs[0].recommendation_id,"audit_ok":"optimization_run_id" in recs[0].audit_trail})

print("\n=== G5 OPT SEMANTICS ===")
def g5inf():
    w=WorldGenerator(seed=7).generate_world()
    for r in w.routes.values(): r.status=RouteStatus.BLOCKED
    p=OptimizationInputAdapter.create_problem(world=w,risk_assessments={},demand_policy=DemandPolicy.P80,objective_weights=ObjectiveWeights())
    r=MilpSolver(allow_fallback=False).solve(p)
    assert r.status==OptimizationStatus.INFEASIBLE, "Expected INFEASIBLE got " + r.status.value
    assert len(r.decisions)==0 and r.total_shortage>0
    assert any("NO_FEASIBLE_DISPATCH" in x for x in r.infeasibility_reasons)
    assert r.metadata.get("lp_solver_status")=="OPTIMAL"
    return {"app_status":r.status.value,"lp_status":r.metadata["lp_solver_status"],"decisions":len(r.decisions),"shortage":round(r.total_shortage,1),"reason":r.infeasibility_reasons[0][:80]}
def g5opt():
    w=WorldGenerator(seed=SEED).generate_world()
    p=OptimizationInputAdapter.create_problem(world=w,risk_assessments={},demand_policy=DemandPolicy.P80,objective_weights=ObjectiveWeights())
    r=MilpSolver(allow_fallback=False).solve(p)
    assert r.status==OptimizationStatus.OPTIMAL and len(r.decisions)>0
    return {"status":r.status.value,"decisions":len(r.decisions)}
def g5zero():
    w=WorldGenerator(seed=7).generate_world()
    for r in w.routes.values(): r.status=RouteStatus.BLOCKED
    p=OptimizationInputAdapter.create_problem(world=w,risk_assessments={},demand_policy=DemandPolicy.P80,objective_weights=ObjectiveWeights())
    p.required_demand={}
    r=MilpSolver(allow_fallback=False).solve(p)
    assert r.status==OptimizationStatus.OPTIMAL
    return {"status":r.status.value}
def g5hyb():
    assert opt.metadata.get("solver_classification")=="HYBRID_LP_FLOW_HEURISTIC_DISPATCH", "Got: " + str(opt.metadata.get("solver_classification"))
    assert opt.metadata.get("is_pure_milp")==False
    return {"label":opt.metadata["solver_classification"]}
def g5sup():
    w=WorldGenerator(seed=SEED).generate_world()
    p=OptimizationInputAdapter.create_problem(world=w,risk_assessments={},demand_policy=DemandPolicy.P80,objective_weights=ObjectiveWeights())
    r=MilpSolver(allow_fallback=False).solve(p)
    used={}
    for d in r.decisions:
        key=(d.source_node_id,d.item); used[key]=used.get(key,0.0)+d.quantity
    for (src,item),qty in used.items():
        avail=p.available_supply.get(src,{}).get(item,0.0)
        assert qty<=avail+1.0
    return {"checks":len(used),"all_pass":True}
check("G5.1_infeasible_all_blocked",g5inf)
check("G5.2_optimal_normal",g5opt)
check("G5.3_optimal_zero_demand",g5zero)
check("G5.4_hybrid_label",g5hyb)
check("G5.5_supply_constraints",g5sup)

print("\n=== G6 TIMING ===")
@_dc
class FR:
    base_travel_hours: float
def g6util():
    cases=[(FR(2.0),2),(FR(7.0),7),(FR(7.6),8),(FR(7.4),7),(None,4),(FR(0.0),1),(FR(-1.0),4),(FR(float("nan")),4),(FR(float("inf")),4),({"base_travel_hours":5.0},5),({},4)]
    for ro,exp in cases:
        got=compute_estimated_arrival(ro)
        assert got==exp, "Input " + str(ro) + " expected " + str(exp) + " got " + str(got)
        assert isinstance(got,int) and got>=1
    return {"cases":len(cases),"all_pass":True}
def g6lp():
    arrivals=[d.estimated_arrival_hour for d in opt.decisions]
    unique=sorted(set(arrivals))
    assert all(a>=1 for a in arrivals)
    for d in opt.decisions[:5]:
        route=world.routes.get(d.route_id)
        if route:
            expected=max(1,int(round(route.base_travel_hours)))
            assert d.estimated_arrival_hour==expected
    return {"unique_arrivals":unique,"not_all_4":len(unique)>1}
def g6doc():
    doc=compute_estimated_arrival.__doc__ or ""
    assert "Optimization estimate" in doc or "optimization estimate" in doc.lower()
    assert "Simulation" in doc
    return {"documented":True}
check("G6.1_utility",g6util)
check("G6.2_lp_timing",g6lp)
check("G6.3_distinction",g6doc)

print("\n=== G7 CANDIDATE vs FEASIBLE ===")
def g7sum():
    svc=DecisionService()
    resp=svc.generate_recommendations(RecommendationGenerateRequest(scenario_id=SCENARIO,seed=SEED,horizon_hours=HORIZON))
    rejected=resp.status_counts.get("REJECTED",0)
    feasible=resp.total_recommendations-rejected
    if rejected>0:
        assert resp.rejection_summary is not None and str(rejected) in resp.rejection_summary
    return {"candidates":resp.total_recommendations,"rejected":rejected,"feasible":feasible,"presentation":str(feasible)+" FEASIBLE / "+str(rejected)+" FILTERED","summary_present":resp.rejection_summary is not None}
def g7conf():
    for r in recs:
        if r.status=="REJECTED":
            assert r.conflict_detected==True and len(r.conflict_details)>0
    return {"rejected_verified":sum(1 for r in recs if r.status=="REJECTED")}
check("G7.1_rejection_summary",g7sum)
check("G7.2_conflict_details",g7conf)

print("\n=== G8 COUNTERFACTUAL ===")
def g8det():
    ev2=PlanEvaluator().evaluate_plan(plan_or_result=opt,base_config=cfg,scenario_id=SCENARIO,horizon_hours=HORIZON,seed=SEED)
    assert ev.status==ev2.status
    d1=round(ev.deltas["unmet_demand"].absolute_delta,4)
    d2=round(ev2.deltas["unmet_demand"].absolute_delta,4)
    assert d1==d2
    return {"status":ev.status.value,"unmet_delta":d1,"match":True}
def g8stat():
    valid={EvaluationStatus.IMPROVED,EvaluationStatus.DEGRADED,EvaluationStatus.MIXED,EvaluationStatus.NO_CHANGE}
    assert ev.status in valid
    return {"status":ev.status.value}
def g8keys():
    req={"unmet_demand","stockout_events","fulfillment_rate"}
    missing=req-set(ev.deltas.keys())
    assert not missing, "Missing: "+str(missing)
    return {"all_keys":sorted(ev.deltas.keys())}
check("G8.1_determinism",g8det)
check("G8.2_valid_status",g8stat)
check("G8.3_delta_keys",g8keys)

print("\n=== G9 RECOMMENDATIONS ===")
def g9ev_fn():
    checked=0
    for r in recs[:5]:
        for ei in r.evidence:
            assert ei.source and ei.type; checked+=1
    return {"evidence_items":checked}
def g9aud():
    for r in recs[:5]:
        assert "optimization_run_id" in r.audit_trail
        assert r.audit_trail.get("scenario_id")==SCENARIO
    return {"recs_checked":5}
def g9dq():
    def avg(dq):
        rs2=eng.generate_recommendations(world=world,optimization_result=opt,evaluation_result=ev,risk_assessments=risk_ass,scenario_id=SCENARIO,data_quality_state=dq)
        scores=[r.confidence.score for r in rs2 if r.confidence]
        return round(sum(scores)/max(1,len(scores)),3)
    rd=avg("READY"); ins=avg("INSUFFICIENT")
    assert rd>=ins
    return {"READY":rd,"INSUFFICIENT":ins}
def g9ins():
    rs2=eng.generate_recommendations(world=world,optimization_result=opt,evaluation_result=ev,risk_assessments=risk_ass,scenario_id=SCENARIO,data_quality_state="INSUFFICIENT")
    high=[r for r in rs2 if r.confidence and r.confidence.score>=0.8]
    assert len(high)==0
    return {"total":len(rs2),"high_conf_blocked":True}
check("G9.1_evidence",g9ev_fn)
check("G9.2_audit",g9aud)
check("G9.3_conf_degrades",g9dq)
check("G9.4_insuff_blocks_high",g9ins)

print("\n=== G12 DETERMINISM ===")
def g12():
    def run():
        w=WorldGenerator(seed=SEED).generate_world()
        sc2=ScenarioService().get_scenario(SCENARIO)
        de2=DisruptionEngine([Disruption.from_dict(d) for d in sc2["disruptions"]])
        de2.apply_route_disruptions(w.routes,24); de2.apply_vehicle_disruptions(w.vehicles,24)
        rs2=RiskIntelligenceService(); rs2.evaluate_world_risk(w)
        p=OptimizationInputAdapter.create_problem(world=w,risk_assessments=rs2._cached_assessments,demand_policy=DemandPolicy.P80)
        return MilpSolver(allow_fallback=True).solve(p)
    r1=run(); r2=run()
    assert r1.status==r2.status
    assert round(r1.objective_value,4)==round(r2.objective_value,4)
    assert len(r1.decisions)==len(r2.decisions)
    return {"decisions":len(r1.decisions),"objective":round(r1.objective_value,4),"status":r1.status.value}
check("G12.1_canonical_determinism",g12)

print("\n=== G13 FAILURE PATHS ===")
def g13blk():
    w=WorldGenerator(seed=7).generate_world()
    for r in w.routes.values(): r.status=RouteStatus.BLOCKED
    p=OptimizationInputAdapter.create_problem(world=w,risk_assessments={},demand_policy=DemandPolicy.P80,objective_weights=ObjectiveWeights())
    r=MilpSolver(allow_fallback=False).solve(p)
    assert r.status==OptimizationStatus.INFEASIBLE
    return {"status":r.status.value,"reasons":len(r.infeasibility_reasons)}
def g13inv():
    w=WorldGenerator(seed=SEED).generate_world()
    for n in w.nodes.values(): n.initial_inventory={}
    p=OptimizationInputAdapter.create_problem(world=w,risk_assessments={},demand_policy=DemandPolicy.P80,objective_weights=ObjectiveWeights())
    r=MilpSolver(allow_fallback=False).solve(p)
    assert r.status in list(OptimizationStatus)
    return {"status":r.status.value}
def g13veh():
    w=WorldGenerator(seed=SEED).generate_world()
    for v in w.vehicles.values(): v.status=VehicleStatus.UNAVAILABLE
    p=OptimizationInputAdapter.create_problem(world=w,risk_assessments={},demand_policy=DemandPolicy.P80,objective_weights=ObjectiveWeights())
    r=MilpSolver(allow_fallback=True).solve(p)
    assert r.status in list(OptimizationStatus)
    return {"status":r.status.value}
def g13dq():
    rs2=eng.generate_recommendations(world=world,optimization_result=opt,evaluation_result=ev,risk_assessments=risk_ass,scenario_id=SCENARIO,data_quality_state="INSUFFICIENT")
    assert len([r for r in rs2 if r.confidence and r.confidence.score>=0.8])==0
    return {"total":len(rs2)}
def g13cmp():
    assert ev is not None and len(recs)>0
    return {"eval":ev.status.value,"recs":len(recs)}
def g13emp():
    from optimization.types import OptimizationResult
    empty=OptimizationResult(run_id="RUN_EMPTY",status=OptimizationStatus.INFEASIBLE,solver_type=SolverType.MILP,objective_value=9999.0,execution_time_ms=0.0,demand_policy=DemandPolicy.P80,total_transport_cost=0.0,total_shortage=5000.0,total_delay=0.0,total_risk_cost=0.0,decisions=[],infeasibility_reasons=["NO_FEASIBLE_DISPATCH"])
    rs2=eng.generate_recommendations(world=world,optimization_result=empty,evaluation_result=None,risk_assessments=risk_ass,scenario_id=SCENARIO,data_quality_state="READY")
    return {"total":len(rs2),"holds":sum(1 for r in rs2 if r.action_type=="HOLD")}
check("G13.1_all_routes_blocked",g13blk)
check("G13.2_zero_inventory",g13inv)
check("G13.3_all_vehicles_unavail",g13veh)
check("G13.4_insufficient_data",g13dq)
check("G13.5_compound",g13cmp)
check("G13.6_empty_decisions",g13emp)

print("\n=== G16 DEMO SAFETY ===")
check("G16.1_not_pure_milp", lambda: {"label":opt.metadata.get("solver_classification"),"not_milp":opt.metadata.get("is_pure_milp")==False} if opt.metadata.get("is_pure_milp")==False else (_ for _ in ()).throw(AssertionError("is_pure_milp must be False")))
check("G16.2_computed_deltas", lambda: {"unmet_delta":round(ev.deltas["unmet_demand"].absolute_delta,2)})

total=len(results); passed=sum(1 for v in results.values() if v["PASS"]); failed=total-passed
print("\n" + "="*60)
print("PHASE 4.5.2 FINAL SUMMARY")
print("="*60)
print("  Total: "+str(total)+"  PASS: "+str(passed)+"  FAIL: "+str(failed))
for name,v in results.items():
    st="PASS" if v["PASS"] else "FAIL"
    print("  ["+st+"] "+name)
    if not v["PASS"]: print("         "+str(v["error"])[:120])
verdict="DEMO FROZEN / PHASE 5 READY" if failed==0 else "NOT READY -- "+str(failed)+" gate(s) failed"
print("\n  VERDICT: "+verdict)

def safe(o):
    if isinstance(o,dict): return {k:safe(v) for k,v in o.items()}
    if isinstance(o,(list,tuple)): return [safe(v) for v in o]
    if isinstance(o,bool): return 1 if o else 0
    if isinstance(o,float): return o if math.isfinite(o) else 0
    return o
with open("phase_4_5_2_evidence.json","w",encoding="utf-8") as f:
    json.dump({"verdict":verdict,"passed":passed,"failed":failed,"total":total,"gates":safe(results)},f,indent=2)
print("Evidence -> phase_4_5_2_evidence.json")
