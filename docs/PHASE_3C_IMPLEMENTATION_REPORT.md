# PRAVAH — Phase 3C Implementation Report

**Smart India Hackathon PS 26251 — Indian Army Predictive Logistics & Forward Supply Chain**  
**Date:** October 2026  
**Branch:** `phase-3c-decision-engine`  
**Status:** COMPLETE & VERIFIED  

---

## 1. Executive Summary

Phase 3C completes the transition of PRAVAH from a predictive and counterfactually validated optimization model into a fully auditable, explainable, and conflict-aware **Decision Engine & Recommendation Layer**.

The complete end-to-end pipeline is now operational:

$$\text{PREDICT} \longrightarrow \text{UNDERSTAND RISK} \longrightarrow \text{OPTIMIZE} \longrightarrow \text{SIMULATE} \longrightarrow \text{VERIFY} \longrightarrow \text{EXPLAIN} \longrightarrow \text{RECOMMEND}$$

Every recommendation output by PRAVAH is directly traceable to empirical simulator states, solver decisions, and Monte Carlo risk assessments. No large language models (LLMs) are used for operational decision-making.

---

## 2. Mandatory Gate: Solver Verification Audit

Before implementing Phase 3C, a comprehensive mathematical and code-level audit was conducted on `optimization/solver.py` (`MilpSolver`).

### Key Audit Findings:
1. **API Called**: `scipy.optimize.linprog(c=c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")`.
2. **Mathematical Formulation**: The mathematical problem solved is a continuous multi-commodity linear network flow LP.
3. **Variable Types & Enforcement**: All decision variables ($x_{r,i,t}, s_{n,i,t}, w_{n,i,t}$) are continuous non-negative real numbers ($x \ge 0$). No integer or binary variable constraints were passed to `linprog`.
4. **Vehicle Assignment**: Vehicle assignment is **not** part of the mathematical solver matrix. Vehicle assets are allocated post-solve via a deterministic round-robin heuristic over continuous flow volumes.
5. **Reported Objective**: The reported objective value reflects the continuous flow cost, penalty, and risk weights, not a mixed-integer objective.
6. **Classification**:
   - **Mislabeled in Phase 3A docstring**: "MILP"
   - **True Classification**: **HYBRID (Continuous Multi-Commodity Linear Flow LP via SciPy HiGHS + Heuristic Fleet Dispatch)**.

### Actions Taken:
- Documented honestly in `docs/PHASE_3C_SOLVER_VERIFICATION.md`.
- Added explicit metadata in `optimization/solver.py`:
  - `solver_classification = "HYBRID_LP_FLOW_HEURISTIC_DISPATCH"`
  - `is_pure_milp = False`
- Updated `DecisionEngine` and explanations to accurately cite the linear network flow solver without making false MILP claims.

---

## 3. Implemented Components

The `backend/app/decision/` package was developed with strict modular separation:

| Module | Core Responsibility |
| :--- | :--- |
| `schemas.py` | Pydantic data schemas: `RecommendationSchema`, `DecisionEvidenceItem`, `DecisionConfidence`, `RouteAlternative`, request/response models. |
| `evidence.py` | `EvidenceBuilder` extracting verifiable operational facts mapped directly to system fields (`STOCKOUT_PROBABILITY`, `TIME_TO_ZERO`, `ROUTE_STATUS`, `SOURCE_INVENTORY`, `VEHICLE_CAPACITY`, `COUNTERFACTUAL_DELTA`). |
| `tradeoffs.py` | `TradeoffAnalyzer` assessing service, risk, transport distance, delay, and fleet utilization between baseline and intervention. |
| `confidence.py` | `ConfidenceScorer` implementing data quality gates (`READY`, `DEGRADED`, `INSUFFICIENT`) and composite confidence scoring. |
| `explanations.py` | `ExplanationGenerator` producing deterministic bulleted rationales and route alternative comparisons. |
| `engine.py` | `DecisionEngine` handling action-type classification, conflict detection (vehicle, route, inventory, time), and recommendation synthesis. |
| `service.py` | `DecisionService` managing end-to-end orchestration, in-memory caching, recommendation filtering, and executive decision summaries. |
| `routes.py` | FastAPI REST endpoints mounted at `/api/recommendations` and `/api/decision`. |

---

## 4. Verification & Testing

### Test Suite Execution
All 94 existing tests from Phases 1, 2, 2.5, 3A, and 3B passed with zero regressions. An additional 25 comprehensive tests were added for Phase 3C:

```bash
pytest -q
# Output:
# 119 passed in 41.73s
```

### Phase 3C Test Coverage:
- `test_recommendation_generation`: End-to-end recommendation generation under compound disruptions.
- `test_action_types`: Deterministic assignment of `MOVE`, `REROUTE`, `REALLOCATE`, `PRIORITIZE`, `HOLD`, and `DEFER`.
- `test_evidence_traceability`: Evidence items map directly to system fields.
- `test_explanation_is_fact_grounded`: Rationales are built strictly from structured facts.
- `test_verified_vs_expected_effect`: Expected analytical improvements are cleanly separated from verified simulation deltas.
- `test_tradeoff_generation`: Tradeoffs in transport cost and transit delay are honestly exposed.
- `test_confidence_data_quality`: `READY`, `DEGRADED`, and `INSUFFICIENT` states appropriately modulate confidence and recommendation status.
- `test_conflicts`: Simultaneous vehicle assignment, route capacity breaches, depot stock depletion, and timing conflicts trigger `REJECTED` status.
- `test_recommendation_validation`: 7-point validation pipeline.
- `test_recommendation_audit_trail`: Traceability to solver run ID, scenario ID, and evaluation ID.
- `test_api_endpoints`: REST endpoints for recommendation generation, filtering, and executive summaries.
- `test_determinism`: Identical seeds yield identical recommendations.
- `test_scenario_responsiveness`: Disruption changes cause recommendation shifts (e.g. `REROUTE` to `HOLD` when alternate routes block).

---

## 5. Demonstration Results Across All Phases

| Script | Purpose | Status | Key Output / Metrics |
| :--- | :--- | :--- | :--- |
| `scripts/run_demo.py` | Phase 1 Simulation Baseline | **PASS** | 15 nodes, 28 routes, 12 vehicles, compound disruption applied. |
| `scripts/run_intelligence_demo.py` | Phase 2 Intelligence & Risk | **PASS** | XGBoost quantile forecasts, Monte Carlo stockout probability, multi-factor risk propagation. |
| `scripts/run_optimization_core_demo.py` | Phase 3A Optimization Core | **PASS** | HiGHS linear flow solved in 8.06ms, 55 movements allocated, constraint checks pass. |
| `scripts/run_counterfactual_demo.py` | Phase 3B Counterfactual Validation | **PASS** | Baseline unmet demand 4127.0 vs Optimized 1135.6 (-72.48%), Tradeoff: MIXED. |
| `scripts/run_decision_demo.py` | Phase 3C Decision Engine | **PASS** | REALLOCATE recommendation generated with live baseline/optimized metrics, zero conflicts, HIGH confidence. |

---

## 6. Audit Trail & Traceability

Every recommendation records:
- `recommendation_id`: Unique identifier (e.g. `REC_D2C59A41_0`)
- `scenario_id`: Evaluated scenario (`COMPOUND_DISRUPTION`)
- `optimization_run_id`: Exact solver execution ID
- `evaluation_id`: Exact counterfactual simulation ID
- `demand_policy`: Quantile policy used (`P80`)
- `data_quality_state`: Telemetry gate state (`READY`)

---

## 7. Operational & Security Boundary

PRAVAH operates strictly as a synthetic decision-support research engine for Smart India Hackathon PS 26251. It does not fabricate real Indian Army operational data or issue live military dispatch directives.

---

## 8. Final Status Checklist

```text
✓ Solver semantics verified & honestly classified (Hybrid LP Flow + Heuristic Dispatch)
✓ No false MILP claims in system metadata
✓ Existing 94 tests pass without regression
✓ 25 new Phase 3C tests pass (119 total passed)
✓ DecisionEngine fully implemented
✓ MOVE, REROUTE, REALLOCATE, PRIORITIZE, HOLD, DEFER supported
✓ Evidence is traceable to system fields
✓ Explanations are deterministic and fact-grounded
✓ Expected effect cleanly separated from verified effect
✓ Tradeoffs are explicitly evaluated
✓ Confidence is evidence-derived
✓ Data quality gate affects recommendation status
✓ 4-way conflicts detected (vehicle, route, inventory, time)
✓ Invalid recommendations are rejected
✓ Counterfactual simulation results are integrated
✓ Audit trail links recommendations to solver and simulation IDs
✓ REST APIs operational
✓ All phase demos pass
✓ Zero fake improvement numbers
✓ Phase 4 Ready: YES
```
