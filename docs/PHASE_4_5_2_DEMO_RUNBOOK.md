# PRAVAH Demo Runbook

**SIH PS 26251 -- Indian Army Predictive Logistics & Forward Supply Chain**
**Phase 4.5.2 -- Demo Freeze Version**
**Date**: 2026-10-02
**Target**: SIH Technical Evaluation Panel

---

## CRITICAL RULES

1. DO NOT manipulate backend data during the presentation.
2. DO NOT modify any source files during the demo.
3. The backend is deterministic: identical inputs always produce identical outputs.
4. If a judge asks "is this real data?" -- answer:
   "Synthetic/public/anonymized data and fictional coordinates are used for demonstration."
5. CANONICAL SCENARIO: COMPOUND_DISRUPTION | seed=42 | 72-hour horizon

---

## Pre-Demo Checklist (30 minutes before)

- [ ] git checkout phase-4-5-2-final-acceptance
- [ ] git status (verify clean working tree)
- [ ] Run: python -m pytest tests/ -q (expect 150 passed)
- [ ] Start backend: uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
- [ ] Verify: curl http://localhost:8000/ -> {"status":"online"}
- [ ] Start frontend: npm run dev (in /frontend directory)
- [ ] Open: http://localhost:5173 -- verify Command Center loads
- [ ] Select scenario: COMPOUND_DISRUPTION
- [ ] Verify all 5 panels load with data (no blank panels, no error toasts)
- [ ] Screenshot/note the canonical values for reference (see below)

---

## Canonical Demo Values (seed=42, COMPOUND_DISRUPTION, 72h)

These values are deterministically produced every run:

| Metric | Value |
|---|---|
| World: nodes/routes/vehicles | 15 / 28 / 12 |
| Disruptions activated | 4 (at h24-h36) |
| LP decisions generated | 55 |
| LP status | OPTIMAL |
| Total shortage (LP) | 0.0 |
| Counterfactual status | DEGRADED |
| Total candidates | 55 |
| FEASIBLE actions | 12 |
| FILTERED actions | 43 |
| Solver label | HYBRID_LP_FLOW_HEURISTIC_DISPATCH |

If your values differ: verify seed=42 is set. Do NOT change these values.

---

## Presentation Flow (2-3 minutes per panel)

### Panel 1: Intelligence Overview (2 min)

SPEAK: "This is the PRAVAH Command Center. It exposes a 7-stage intelligence pipeline:
PREDICT -> RISK -> OPTIMIZE -> SIMULATE -> VERIFY -> EXPLAIN -> RECOMMEND"

SHOW: Top-right pipeline status indicator. It shows all 7 stages lit.

SPEAK: "The system has generated 15 risk assessments across all supply chain nodes.
You can see the KPI cards: overall risk level, nodes at risk, active alerts, and
the optimization status."

POINT TO: Red/amber nodes in the risk overview table.

---

### Panel 2: Predictive Analytics (2 min)

SPEAK: "The forecasting engine runs XGBoost demand prediction. For each forward post,
it generates P50, P80, and P95 demand quantiles. We dispatch to P80 -- the 80th
percentile demand -- to balance overstocking against stockout risk."

SHOW: Demand chart for any forward post node.

SPEAK: "The system also detects whether demand is trending up due to the active
demand surge disruption. Time-to-stockout and stockout probability are computed
dynamically from current inventory and projected demand."

---

### Panel 3: Optimization & Routing (2 min)

SPEAK: "The optimizer solves a Continuous Multi-Commodity Linear Flow LP using
SciPy HiGHS. For the COMPOUND_DISRUPTION scenario, it generates 55 candidate
dispatch decisions covering all items across all supply lanes."

SHOW: Optimization panel, decisions table.

SPEAK: "The solver is labeled HYBRID -- it combines a continuous LP flow allocation
with a deterministic heuristic fleet dispatch. We do NOT claim it is a pure MILP
or integer program."

SPEAK: "In this scenario, the LP achieves zero shortage at hour 0 -- meaning if
dispatched immediately before disruptions materialize, demand would be met.
The counterfactual then tests whether this actually holds when disruptions activate."

---

### Panel 4: Counterfactual Simulation (2 min)

SPEAK: "This is the unique validation stage. We inject the optimizer's plan into
the same disrupted simulation environment and compare outcomes."

SHOW: Counterfactual panel. Point to status: DEGRADED.

SPEAK: "The result is DEGRADED. This means: when the h0-optimized plan runs against
disruptions that materialize at h24, unmet demand increases. This is the system
being honest -- the static plan does not adapt to temporal disruptions."

IF JUDGE ASKS: "Is this a problem?"
ANSWER: "No -- it correctly motivates Phase 5: a rolling-horizon reactive planner
that would recompute as disruptions materialize. The system is designed to expose
exactly this limitation."

SHOW: Delta table. Point to unmet_demand positive delta, fulfillment_rate_percent drop.

---

### Panel 5: Recommendations (2 min)

SPEAK: "The decision engine filters 55 LP candidates through a conflict detector
and counterfactual evaluator, producing 12 physically feasible, conflict-free,
counterfactually-verified actions."

SHOW: Recommendation list. Filter by status.

SPEAK: "43 are FILTERED -- rejected because the LP assigns all vehicles at hour 0,
but the fleet conflict detector enforces one vehicle per time slot. This is correct
physics enforcement."

SPEAK: "Each recommendation includes: action type, item, quantity, source/destination,
expected arrival hour, confidence score, and a full audit trail linking back to
the optimization run ID, evaluation ID, and scenario ID."

SHOW: Click one recommendation -> full detail view -> audit trail.

SPEAK: "Every decision is traceable end-to-end. A judge can verify the exact inputs
that produced each recommendation."

---

### Panel 6: Audit Trail (1 min)

SPEAK: "For regulatory and operational accountability, every recommendation carries:
forecast_version, risk_version, optimization_run_id, evaluation_id, scenario_id,
and a timestamp. No decision can be made without a traceable lineage."

IF TIME ALLOWS: Show an INFEASIBLE scenario (all routes blocked variant)
SPEAK: "If all routes are blocked, the system returns INFEASIBLE with reason
NO_FEASIBLE_DISPATCH -- not a crash, not a fake success. The judge can verify
this by changing the scenario."

---

## Common Judge Questions & Answers

Q: "Is this real Army data?"
A: "Synthetic/public/anonymized data and fictional coordinates are used for
   demonstration. The architecture is designed for real operational data integration."

Q: "Why is the counterfactual DEGRADED? Doesn't that mean your system failed?"
A: "No -- it means the system is honest. A static plan optimized before disruptions
   cannot be expected to be optimal after they materialize. The system correctly
   identifies degradation and rejects those recommendations, which is exactly the
   behavior you want from a decision-support system."

Q: "What is the solver? Is it MILP?"
A: "It is a Continuous Multi-Commodity Linear Flow LP solved by SciPy HiGHS,
   combined with a deterministic heuristic fleet dispatch. We explicitly label it
   HYBRID -- not MILP -- to be accurate about the approach."

Q: "Why are only 12/55 recommendations not rejected?"
A: "The LP allocates all vehicles at dispatch hour 0. The conflict detector
   enforces physical constraints -- one vehicle per time slot. 43 dispatches
   share vehicle assignments, so they are filtered. A time-expanded LP formulation
   would reduce this in Phase 5."

Q: "Is the system deterministic?"
A: "Yes. Same seed, same scenario, same horizon always produces identical outputs.
   We verified this by running the canonical pipeline twice in automated tests."

Q: "What happens if all routes are blocked?"
A: "The system returns application status INFEASIBLE with reason NO_FEASIBLE_DISPATCH.
   The LP internally reports OPTIMAL (because mathematically, zero flow with shortage
   variables solves the formulation), but we classify it as INFEASIBLE at the
   application layer to be honest with the operator."

---

## Fallback Procedures

### If backend crashes:
1. Ctrl+C the uvicorn process
2. cd Pravah && python -m pytest tests/ -q (verify 150 pass)
3. Restart: uvicorn backend.app.main:app --host 0.0.0.0 --port 8000

### If frontend shows blank panels:
1. Hard refresh browser (Ctrl+Shift+R)
2. Verify backend is responding: curl http://localhost:8000/
3. Check COMPOUND_DISRUPTION is selected in scenario dropdown

### If judge asks to change the scenario:
- DEMAND_SURGE: safe, no route changes, optimizer stays OPTIMAL
- ROUTE_BLOCKAGE: demonstrates INFEASIBLE path
- WEATHER_DEGRADATION: demonstrates risk escalation
- COMPOUND_DISRUPTION: canonical demo (recommended)

### If judge asks to run with different seed:
- Change seed parameter in the API call
- Results will differ (deterministic but not fixed to seed=42)
- Canonical presentation values will differ; explain it is a different random world

---

## Architecture Summary Card (for poster/handout)

```
PRAVAH -- Predictive Logistics Intelligence & Resilience Engine

PIPELINE:
  Synthetic Simulation     (Phase 1)
  -> XGBoost Forecasting   (Phase 2)
  -> Composite Risk Engine (Phase 2)
  -> LP Flow Optimization  (Phase 3A)
  -> Counterfactual Eval   (Phase 3B)
  -> Decision Engine       (Phase 3C)
  -> Command Center UI     (Phase 4)

SOLVER:
  Continuous Multi-Commodity Linear Flow LP via SciPy HiGHS
  + Deterministic heuristic fleet dispatch
  Label: HYBRID_LP_FLOW_HEURISTIC_DISPATCH

CANONICAL SCENARIO:
  COMPOUND_DISRUPTION | seed=42 | 72h
  (4 simultaneous disruptions: demand surge + route block + weather + vehicle loss)

DATA:
  Synthetic/public/anonymized data and fictional coordinates.
  Architecture designed for real operational data integration.

VALIDATION:
  150/150 backend tests | 13/13 frontend tests
  Deterministic | Failure-resilient | Fully auditable
```

---

## Git State at Demo Freeze

Branch: phase-4-5-2-final-acceptance
Backend tests: 150/150 PASS
Frontend tests: 13/13 PASS
Production build: PASS

DO NOT merge to main or create new branches during the demo period.
