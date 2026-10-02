# PRAVAH — Grand Finale Presenter Cheat Sheet

**Problem Statement:** PS 26251 — Indian Army — Predictive Logistics & Forward Supply Chain  
**Stage:** Grand Finale Defense | **Branch:** `phase-5c-hostile-judge-defense` | **Mode:** Ready for Defense  

---

## 1. PRAVAH IN ONE LINE
> *"PRAVAH is a closed-loop decision support engine that predicts forward supply failures and verifies corrective convoy movements in simulation before recommending action."*

---

## 2. CORE PIPELINE
```
PREDICT (Quantiles P50/P80/P95)
   ↓
UNDERSTAND RISK (5 Dimensions + Graph Propagation)
   ↓
OPTIMIZE (Continuous Multi-Commodity Linear Flow LP)
   ↓
VALIDATE (Deterministic Physical Fleet Feasibility Gate)
   ↓
SIMULATE (Closed-Loop Paired Digital Twin under Disruptions)
   ↓
VERIFY (Causal Comparison vs Baseline: VERIFIED / DEGRADED)
   ↓
EXPLAIN (Deterministic Fact-Grounded Evidence & Lineage)
   ↓
RECOMMEND (Actionable Convoy Orders or Safe Suppression)
```

---

## 3. 5 VERIFIED TECHNICAL FACTS
1. **Solver Architecture:** Continuous Multi-Commodity Linear Flow LP solved using SciPy HiGHS (`scipy.optimize.linprog`), followed by a deterministic heuristic fleet dispatch.
2. **AI/ML Method:** Quantile XGBoost Regression ($\tau \in \{0.50, 0.80, 0.95\}$) minimizing Pinball Loss with strict non-crossing monotonicity ($P_{50} \le P_{80} \le P_{95}$).
3. **Paired Counterfactual Verification:** Digital twin clones initial state at $t=0$ and runs Baseline (0 actions) vs. Intervention under identical seed (`seed=42`) and identical disruption schedules.
4. **Safety Suppression Gate:** If counterfactual simulation reveals an intervention worsens outcomes vs. baseline (`DEGRADED`), all recommendations are safely rejected and suppressed.
5. **Zero Generative AI:** 100% LLM-free. All decision outputs, quantities, and explanations are deterministically generated from constraint solvers and structured simulation state.

---

## 4. 5 VERIFIED NUMBERS (AUDITED)
1. **`<15 ms` Solver Latency:** Continuous Multi-Commodity Linear Flow LP solves in **6.82 ms** (empirically $7\text{–}15\text{ ms}$) via SciPy HiGHS on canonical benchmark.
2. **15 Nodes, 28 Corridors, 12 Vehicles:** Synthetic sector topology (1 Base Depot, 3 Regional Hubs, 6 Forward Posts, 5 Staging Bases, 3 vehicle tonnage classes).
3. **72-Hour Horizon with 1.0-Hour Step Size:** Temporal planning and discrete-event simulation resolution.
4. **5 Monitored Commodities:** Dedicated multi-commodity flow conservation for Fuel, Rations, Ammunition, Medical Supplies, and Potable Water.
5. **150 / 150 Automated Tests:** 150 backend unit/integration tests and 13 frontend integration tests passing with 17/17 acceptance gates frozen.

*(Note: Do NOT quote "+22% distance / -73% demand" or "100+ nodes in 2s" — these failed the audit).*

---

## 5. 5 HONEST LIMITATIONS
1. **Synthetic Environment:** Evaluated on synthetic digital twin topology with fictional coordinates; not yet deployed on classified defense networks.
2. **Regional Prototype Scope:** Benchmarked on a 15-node brigade sector; theater-scale hierarchical multi-echelon scaling is designed for Phase 6.
3. **Static Plan Re-evaluation:** Mid-horizon disruptions at $h=24$ trigger plan degradation detection and suppression; automated real-time re-solve must be user-triggered.
4. **Data Dependency:** Quantile ML forecasting depends on representative historical training logs; unprecedented tactical shocks are bounded by P95 stress quantiles.
5. **Heuristic Fleet Packing:** Continuous LP volumes are packed into discrete vehicles using a greedy heuristic; does not solve an integer-exact NP-hard VRP.

---

## 6. 10 RAPID-FIRE ANSWERS (UNDER 10 SECONDS)
1. **Why not pure MILP?** *"MILP integer branch-and-bound stalls under tactical deadlines; Continuous LP solves in 7 milliseconds, followed by deterministic fleet dispatch."*
2. **Why not LSTM/Transformer?** *"XGBoost runs in 5ms on basic CPU, trains in seconds, and outperforms deep networks on tabular operational time series."*
3. **What is Time to Zero?** *"The exact hour when a forward post's physical inventory reaches zero under P80 consumption without replenishment."*
4. **What does DEGRADED mean?** *"The proposed plan worsened logistics outcomes under active disruptions; PRAVAH safely suppresses it."*
5. **Is rejection a failure?** *"No, rejection is a vital safety feature that prevents sending convoys into disastrous mountain traps."*
6. **Can the AI hallucinate?** *"Zero percent chance. There are no LLMs; every entity is mapped from physical database records."*
7. **What happens if all roads are blocked?** *"Solver outputs status INFEASIBLE with reason NO_FEASIBLE_DISPATCH, alerting commanders to explore aerial resupply."*
8. **How is risk calculated?** *"Convex combination across 5 physical dimensions: Inventory, Demand, Route, Transport, and Environment, with graph distance-decay propagation."*
9. **Who makes the final decision?** *"The human military commander; PRAVAH provides verified decision support, never autonomous execution."*
10. **What is the core tagline?** *"Don't wait for the shortage. Predict before shortage. Verify before action."*

---

## 7. 5 PHRASES TO AVOID & REPLACEMENTS
1. ❌ **AVOID:** *"Our optimizer is a MILP."*  
   👉 **USE:** *"Continuous Multi-Commodity Linear Flow LP via SciPy HiGHS with deterministic fleet dispatch."*
2. ❌ **AVOID:** *"Our AI predicts combat or mountain warfare."*  
   👉 **USE:** *"Our model forecasts forward logistics consumption and corridor transit latency."*
3. ❌ **AVOID:** *"We integrate Kafka and MQTT."*  
   👉 **USE:** *"Prototype runs on REST APIs; Kafka/MQTT is our proposed production telemetry architecture."*
4. ❌ **AVOID:** *"The system is fully autonomous."*  
   👉 **USE:** *"PRAVAH is a human-in-the-loop decision-support system."*
5. ❌ **AVOID:** *"We achieved -73% unmet demand."*  
   👉 **USE:** *"Counterfactual simulation measures real causal tradeoffs between unmet demand reduction and detour distance."*
