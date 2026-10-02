# PRAVAH — Phase 3C Decision Engine & Recommendation Layer Architecture

## 1. Decision Architecture

PRAVAH transforms raw operational telemetry, machine learning predictions, and mathematical optimization into auditable, explainable decision-support recommendations.

The closed-loop decision flow operates deterministically:

```text
PREDICT (Quantile Demand Forecasting)
   ↓
UNDERSTAND RISK (Multi-Factor Risk Assessment & Propagation)
   ↓
OPTIMIZE (Multi-Commodity Linear Network Flow via SciPy HiGHS)
   ↓
SIMULATE (Baseline & Counterfactual Disrupted Simulation)
   ↓
VERIFY (Closed-Loop Causal Metric Delta Verification)
   ↓
EXPLAIN (Evidence-Grounded Rationale Generation)
   ↓
RECOMMEND (Conflict-Free, Prioritized Action Recommendations)
```

The system is decoupled into modular layers located in `backend/app/decision/`:
- `schemas.py`: Strongly-typed Pydantic schemas for recommendations, evidence, confidence, tradeoffs, and API contracts.
- `evidence.py`: `EvidenceBuilder` extracting verifiable operational facts directly mapped to system fields.
- `tradeoffs.py`: `TradeoffAnalyzer` assessing service, risk, transport distance, delay, and fleet utilization.
- `confidence.py`: `ConfidenceScorer` implementing the data quality gate (`READY`, `DEGRADED`, `INSUFFICIENT`) and composite confidence scoring.
- `explanations.py`: `ExplanationGenerator` formulating deterministic, fact-grounded natural language explanations and route alternative comparisons without LLM hallucination.
- `engine.py`: `DecisionEngine` synthesizing recommendations, enforcing priority sorting, detecting 4-way conflicts, and computing expected vs. verified effects.
- `service.py`: `DecisionService` coordinating end-to-end execution, in-memory persistence, querying/filtering, and decision summaries.
- `routes.py`: FastAPI endpoints exposing the decision engine to frontends and external command systems.

---

## 2. Recommendation Model

Every recommendation represents a concrete operational decision support artifact. The data model (`RecommendationSchema`) includes:

```python
class RecommendationSchema(BaseModel):
    recommendation_id: str
    scenario_id: str
    optimization_run_id: str
    evaluation_id: Optional[str]

    priority: int  # 1 (Highest / Most Urgent) to 5 (Lowest)
    action_type: str  # MOVE, REROUTE, REALLOCATE, PRIORITIZE, HOLD, DEFER

    source_node: str
    destination_node: str
    item: str
    quantity: float
    route: str
    vehicle: str

    planned_departure: int  # Dispatch hour (t)
    expected_arrival: int   # Estimated arrival hour (t + transit_time)

    title: str
    reason: str             # Bulleted deterministic rationale

    evidence: List[DecisionEvidenceItem]
    tradeoffs: Dict[str, Any]

    expected_effect: str    # Analytical expectation from optimizer
    verified_effect: str    # Verified empirical delta from counterfactual simulator

    status: str             # PROPOSED, VERIFIED, MIXED, REJECTED, INCONCLUSIVE
    confidence: DecisionConfidence

    validation_state: Dict[str, str]
    conflict_detected: bool
    conflict_details: List[str]
    alternatives: List[RouteAlternative]
    audit_trail: Dict[str, str]
    created_at: str
```

---

## 3. Action Types

The decision engine produces deterministic action categories reflecting operational intent:

| Action Type | Operational Semantics | Trigger Condition |
| :--- | :--- | :--- |
| **MOVE** | Standard replenishment transfer from source depot to destination. | Stockout probability elevated or time-to-zero below horizon on standard corridor. |
| **REROUTE** | Dispatch convoy via an alternate corridor avoiding a blocked or high-risk primary corridor. | Primary route status is `BLOCKED` or risk $\ge 0.50$, and a valid bypass corridor is available. |
| **REALLOCATE** | Shift scarce or critical supply across regional depots or forward posts. | Destination has active demand while primary source capacity or network constraints require reallocation from secondary hubs. |
| **PRIORITIZE** | Assign emergency priority dispatch to combat forward outposts facing imminent stockout. | Destination is a critical forward defense post (`FP-*`), stockout probability $\ge 0.70$, or time-to-zero $\le 24$ hours. |
| **HOLD** | Withhold dispatch; preserve inventory at source depot. | Route is blocked with no bypass, or zero transport justification exists. |
| **DEFER** | Postpone dispatch; current movement provides marginal or negative benefit. | Destination inventory is fully secure ($TTZ > 72$h) and vehicle assets are constrained. |

---

## 4. Evidence Model

Every recommendation is backed by a structured list of `DecisionEvidenceItem` elements. Evidence is directly extracted from system state fields:

```json
[
  {
    "type": "STOCKOUT_PROBABILITY",
    "value": 0.85,
    "source": "Phase 2 Monte Carlo Engine",
    "details": "Projected probability of stockout at destination node"
  },
  {
    "type": "TIME_TO_ZERO",
    "value": 18,
    "source": "Phase 2 Inventory Projection",
    "details": "Projected hours until inventory hits 0"
  },
  {
    "type": "ROUTE_STATUS",
    "value": "AVAILABLE",
    "source": "Network Registry",
    "details": "Corridor operational condition"
  },
  {
    "type": "SOURCE_INVENTORY",
    "value": 19200.0,
    "source": "Depot Stock Registry",
    "details": "Verified available source inventory at dispatch hour"
  },
  {
    "type": "VEHICLE_CAPACITY",
    "value": 10000.0,
    "source": "Fleet Registry",
    "details": "Payload capacity of assigned logistics vehicle"
  },
  {
    "type": "COUNTERFACTUAL_DELTA",
    "value": -4486.9,
    "source": "Phase 3B Closed-Loop Simulation",
    "details": "Verified change in total unmet demand (units)"
  }
]
```

No evidence is generated from unverified text or synthetic guesses.

---

## 5. Explanation Model

Natural language explanations are generated deterministically by `ExplanationGenerator` using verified evidence items and optimization alternatives:

### Rationale Format
```text
FUEL -> FP-01
Recommended Action: REALLOCATE
Why:
• FP-01 requires forward inventory replenishment under active operational demand.
• Primary corridor R-01 is BLOCKED; alternate corridor R-11 was selected.
• Transport corridor R-11 is confirmed AVAILABLE and traversable.
• Source depot RH-03 has verified available stock (19200.0 units of FUEL).
• Assigned asset ALS-104 provides 10000.0 units payload capacity.
• Closed-loop simulation verified reduction of unmet demand by 4486.9 units.
```

### Route Alternative Comparative Analysis
For each selected route, the engine evaluates all parallel corridors connecting the same node pair:
- **Selected Route**: Distance (km), status, risk score, transport cost.
- **Alternative Routes**: Status (e.g., `BLOCKED`), risk score, distance.
- **Selection Reason**: e.g., *"Selected R-11 because primary route R-01 is BLOCKED"* or *"Selected R-11 because risk (0.12) is lower than alternative R-14 (0.68) despite +15 km distance."*

---

## 6. Tradeoff Model

`TradeoffAnalyzer` evaluates multi-dimensional operational impacts between baseline and intervention:

1. **Service**:
   - `IMPROVED`: Unmet demand decreased by $\ge 5\%$ or stockout hours decreased.
   - `DEGRADED`: Unmet demand increased.
   - `NEUTRAL`: Delta within $\pm 1\%$.
2. **Risk**:
   - `MITIGATED`: High-risk destination replenished before zero-stockout breach.
   - `ELEVATED`: Convoy traversed severe risk corridors.
   - `UNRESOLVED`: Risk persists unmitigated.
3. **Transport Distance / Cost**:
   - `INCREASED`: Detours or extensive inter-hub transfers increased total fleet kilometers.
   - `MINIMAL_INCREASE`: Minor increase ($< 10\%$).
   - `REDUCED`: More direct routing achieved.
4. **Delay**:
   - `INCREASED`: Adverse weather or detour routes increased average transit hours.
   - `NEUTRAL`: Transit hours unaffected.
5. **Fleet Utilization**:
   - Monitored as a ratio of allocated vehicle capacity vs available fleet.

---

## 7. Confidence Model

PRAVAH does not invent artificial probability scores. Confidence is calculated from measurable system indicators:

### Scoring Components:
- **Data Quality State**:
  - `READY`: Base score 0.40.
  - `DEGRADED`: Base score 0.20.
  - `INSUFFICIENT`: Base score 0.00.
- **Supply Availability**: +0.15 if verified depot stock $\ge$ dispatch volume.
- **Route Viability**: +0.15 if route is `AVAILABLE` and traversable.
- **Fleet Viability**: +0.15 if vehicle is available and capacity is respected.
- **Optimization Feasibility**: +0.05 if solver returned `OPTIMAL`.
- **Counterfactual Verification**: +0.10 if closed-loop simulation demonstrated metric improvement.

### Levels:
- **HIGH** ($\ge 0.85$): All telemetry, supply, route, vehicle, and counterfactual checks passed.
- **MEDIUM** ($0.60 - 0.84$): Minor degradation or unverified counterfactual simulation.
- **LOW** ($< 0.60$): Degraded or insufficient data, or missing validation.

---

## 8. Data-Quality Behavior

The decision engine directly integrates with `DataQualityGate`:
- **`READY`**: Normal recommendation generation with full confidence scoring.
- **`DEGRADED`**: Recommendations are generated with explicit degradation warning factors in `confidence.factors` (e.g., *"Data quality is DEGRADED: operating under stale or incomplete telemetry"*), confidence capped at `MEDIUM` or `LOW`.
- **`INSUFFICIENT`**: Recommendation status is forced to `INCONCLUSIVE` or `REJECTED`, confidence is forced to `LOW` (score $\le 0.30$), and operational dispatches are withheld.

---

## 9. Conflict Detection

`DecisionEngine` evaluates every recommendation against four operational constraints:

1. **Vehicle Assignment Conflicts**: Ensures no vehicle asset is scheduled for two simultaneous dispatches at the same hour ($v_{slot} = (vehicle\_id, hour)$).
2. **Route Capacity Conflicts**: Ensures aggregate convoy volume traversing a route within the planning window does not exceed corridor throughput capacity ($C_{route}$).
3. **Source Inventory Conflicts**: Ensures total volume drawn across all simultaneous dispatches from a depot does not exceed on-hand inventory ($S_{depot, item}$).
4. **Time / Horizon Conflicts**: Ensures dispatches are scheduled within valid operational planning horizons ($0 \le t_{dispatch} < H$).

When a conflict is detected:
- `conflict_detected = True`
- Details recorded in `conflict_details`
- Recommendation status transitioned to `REJECTED`
- Priority sorting ensures critical forward posts (`FP-*`) claim vehicle slots and depot inventory first.

---

## 10. Recommendation Validation

Before publishing, each recommendation receives a 7-point validation check:
1. `source_inventory`: `PASS`, `CONFLICT`, or `FAIL`
2. `route`: `PASS`, `BLOCKED`, or `CONFLICT`
3. `vehicle`: `PASS`, `UNAVAILABLE`, `CONFLICT`, or `EXCEEDED_CAPACITY`
4. `quantity`: `PASS` or `ZERO`
5. `optimization`: `PASS` or `FEASIBLE`
6. `counterfactual`: `PASS` or `NOT_RUN`
7. `data_quality`: `READY`, `DEGRADED`, or `INSUFFICIENT`

Recommendations with validation failures are marked `REJECTED` or `INCONCLUSIVE`.

---

## 11. Audit Trail

Every recommendation includes a complete provenance trace:
```json
"audit_trail": {
  "scenario_id": "COMPOUND_DISRUPTION",
  "optimization_run_id": "RUN_91B1F34A",
  "evaluation_id": "EVAL_A2F4810C",
  "demand_policy": "P80",
  "data_quality_state": "READY",
  "decision_id": "DEC_RH03_FP01_FUEL_0"
}
```
Any operator can trace a recommendation back to the exact solver run, counterfactual simulation, forecast quantiles, and scenario disruption state.

---

## 12. API Reference

### `POST /api/recommendations/generate`
Generates prioritized, auditable recommendations.
- **Request Body**:
  ```json
  {
    "scenario_id": "COMPOUND_DISRUPTION",
    "demand_policy": "P80",
    "data_quality_state": "READY",
    "horizon_hours": 72,
    "seed": 42
  }
  ```
- **Response**: `RecommendationListResponse` with counts and recommendations.

### `GET /api/recommendations`
Lists recommendations with optional query filters:
- `scenario_id`: Filter by scenario.
- `status`: Filter by `PROPOSED`, `VERIFIED`, `MIXED`, `REJECTED`, `INCONCLUSIVE`.
- `priority`: Filter by priority level ($1 - 5$).
- `node`: Filter by destination or source node code.
- `item`: Filter by commodity type.

### `GET /api/recommendations/{recommendation_id}`
Returns full detail of an individual recommendation including evidence, alternatives, and audit trail.

### `GET /api/decision/summary`
Returns executive situational readiness and command summary:
- `readiness`: `OPERATIONAL` or `DEGRADED`.
- `data_quality`: Current gate status.
- `critical_nodes`: Nodes facing imminent stockout.
- `active_risks`: Elevated risk areas.
- `recommendations_count` & `verified_actions_count`.
- `top_recommendations`: Top 5 highest priority recommendations.
- `overall_tradeoffs`: Aggregate service vs transport tradeoffs.

---

## 13. Test Strategy

Phase 3C is validated by 25 unit and integration tests in `tests/test_decision_engine.py`:
- All 6 action types: `MOVE`, `REROUTE`, `REALLOCATE`, `PRIORITIZE`, `HOLD`, `DEFER`.
- Evidence traceability: Field mapping and factual provenance.
- Fact-grounded explanations: Absence of hallucinations or ungrounded assertions.
- Expected vs. verified effect separation.
- Multi-dimensional tradeoff analysis.
- Confidence scoring and data quality gate degradation/insufficient handling.
- 4-way conflict detection: vehicle, route capacity, source inventory, time.
- 7-point validation pipeline and audit trail integrity.
- REST API endpoint verification for generation, listing, filtering, and executive summaries.
- Determinism test: Identical seeds produce byte-identical recommendation payloads.
- Controlled scenario responsiveness: Blocking an alternate route changes the decision from REROUTE to HOLD.

---

## 14. Limitations & Boundaries

1. **Synthetic Nature**: PRAVAH operates in a reproducible, synthetic logistics environment designed for Smart India Hackathon PS 26251. Recommendations are decision-support outputs, not real military orders.
2. **Deterministic Heuristic Vehicle Dispatch**: As audited in `docs/PHASE_3C_SOLVER_VERIFICATION.md`, vehicle assignment is performed via priority-ordered heuristic dispatch over continuous LP flow volumes rather than true binary branch-and-cut optimization.
3. **Discrete Hourly Time-Steps**: Logistics dispatches are scheduled in discrete 1-hour epochs over a 72-hour or 168-hour planning horizon.
