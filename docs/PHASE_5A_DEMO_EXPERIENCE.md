# PRAVAH — Phase 5A: SIH Judge Demonstration Experience & Storyboard

**Problem Statement:** PS 26251 — Indian Army: Predictive Logistics & Forward Supply Chain  
**System Name:** PRAVAH — Predictive Logistics Intelligence & Resilience Engine  
**Target Window:** 2–3 Minutes (SIH Competition Live Evaluation)  
**System State:** Frozen (Phase 4.5.2 Accepted, 17/17 Gates Passed)  
**Branch:** `phase-5a-demo-experience`  
**Execution Environment:** Synthetic Simulation Grid (15 Nodes, 28 Corridors, Fictional Coordinates)  

---

## 1. Executive Summary & Demo Objective

The primary objective of the 2–3 minute PRAVAH demonstration is to give SIH judges an immediate, intuitive, and mathematically grounded understanding of why reactive logistics fails in high-altitude forward defense environments, and how PRAVAH's closed-loop intelligence pipeline solves the problem before shortages manifest.

### Within the first 30 seconds, judges must understand:
1. **The Problem:** Conventional logistics responds reactively after a forward post reports zero inventory.
2. **PRAVAH's Solution:** Continuously forecasts consumption, models 5-factor multi-dimensional risk, computes multi-commodity continuous network flow, validates physical fleet feasibility, and **verifies candidate interventions in counterfactual simulation before recommending action**.
3. **The Core Tagline:**  
   > *"Don't wait for the shortage. Predict the failure of the logistics network before it happens."*  
   > *"Predict before shortage. Verify before action."*

### The Core Intelligence Pipeline:
```
PREDICT
   ↓
UNDERSTAND RISK
   ↓
OPTIMIZE
   ↓
SIMULATE
   ↓
VERIFY
   ↓
EXPLAIN
   ↓
RECOMMEND
```

---

## 2. The Core Trust Story: Counterfactual Safety & Honest Rejection

A central differentiator of PRAVAH is that it **does not blindly trust optimization output**:

> *"PRAVAH does not recommend an action merely because an optimizer generated it.*  
> *It first tests the candidate intervention in a controlled, paired counterfactual simulation.*  
> *If the intervention worsens the outcome (CF = DEGRADED), PRAVAH rejects it.*  
> *Rejection is a critical safety feature, not a system failure."*

### Two Valid Demonstration Outcomes:
* **Outcome A (VERIFIED / MIXED):** If the counterfactual evaluation proves that the candidate intervention strictly decreases unmet demand or mitigates stockouts with acceptable operational tradeoffs (e.g., slight route detour distance), the system marks the action **VERIFIED** and outputs the actionable dispatch.
* **Outcome B (DEGRADED):** If active compound disruptions (e.g., route blockage + blizzard at $h=24$) render the $h=0$ planned movement counterproductive, the Counterfactual Evaluator returns **DEGRADED**. PRAVAH suppresses recommendation generation, categorizes the rejection as counterfactual degradation (distinct from physical vehicle conflicts), and explains the reason in plain language.

**Judges respect engineering honesty.** Neither the code nor the presenter should ever fabricate numbers or conceal a `DEGRADED` result.

---

## 3. Canonical Demonstration Scenario

To guarantee repeatability without hardcoding:

* **Scenario ID:** `COMPOUND_DISRUPTION`
* **Planning Horizon:** `72 hours`
* **Random Seed:** `42`
* **Disruptions Simulated:**
  1. **Route Interdiction:** Primary corridor `R-01` / `R-22` blocked (simulated high-altitude landslide).
  2. **Demand Surge:** $+30\%$ consumption pressure across forward posts (e.g., `FP-01`, `FP-04`).
  3. **Severe Weather:** Alpine blizzard imposing speed penalties and risk multipliers.
  4. **Fleet Degradation:** $-20\%$ vehicle availability due to sub-zero mechanical constraints.
* **Network Scope:** 1 Base Depot (`CD-01`), 3 Regional Supply Hubs (`RH-01`, `RH-02`, `RH-03`), 6 Forward Combat Posts (`FP-01`–`FP-06`), 28 multi-terrain corridors, 12 tactical fleet assets.
* **Data Classification:** All geographic coordinates, node names, and operational attributes are strictly synthetic, anonymized, and public. No real-world classified data is utilized.

---

## 4. Screen-by-Screen 2–3 Minute Storyboard

| Scene | Name | Screen / Tab | Target Time | Cumulative |
| :--- | :--- | :--- | :--- | :--- |
| **Scene 1** | Command Center & Normal Topology | `COMMAND_CENTER` | 15–20 s | 0:20 |
| **Scene 2** | Compound Disruption Event | `SIMULATION` / Controls | 10–15 s | 0:35 |
| **Scene 3** | Forecast Intelligence & Uncertainty | `FORECAST` | 15–20 s | 0:55 |
| **Scene 4** | 5-Factor Risk Intelligence & Propagation | `RISK` | 15–20 s | 1:15 |
| **Scene 5** | Continuous Flow LP Optimization | `OPTIMIZATION` | 20 s | 1:35 |
| **Scene 6** | Physical Fleet Feasibility Validation | `RECOMMENDATIONS` (Pipeline Strip) | 15 s | 1:50 |
| **Scene 7** | Closed-Loop Counterfactual Simulation | `SIMULATION` (Causal Comparison) | 20–25 s | 2:15 |
| **Scene 8** | Empirical Verification & Trust Story | `SIMULATION` / `VerificationPanel` | 15–20 s | 2:35 |
| **Scene 9** | Actionable Recommendations or Rejection Audit | `RECOMMENDATIONS` | 15–20 s | 2:55 |
| **Scene 10**| Explainability, Evidence & Provenance | `AUDIT` / Drawer | 10–15 s | 3:10 |
| **Scene 11**| Final Stance & Conclusion | Return to `COMMAND_CENTER` | 10 s | 3:20 |

---

### Detailed Scene Execution

#### SCENE 1 — COMMAND CENTER (15–20 seconds)
* **View:** Main `COMMAND_CENTER` Tab.
* **Visual Focus:**
  * Top left: 15-node Digital Twin topology map showing base depot `CD-01`, regional hubs, and forward posts connected via 28 corridors.
  * Top right: Risk Panel with green/normal operational indicators.
  * System status: `SYSTEM READY` / `SYNTHETIC SIMULATION`.
* **Presenter Script:**
  > *"Respected judges, in high-altitude forward logistics, waiting for a remote outpost to report a shortage is already too late.  
  > PRAVAH transforms forward supply operations from reactive firefighting to predictive resilience.  
  > Here in the Command Center, PRAVAH continuously monitors topology, inventory, route conditions, weather, and fleet availability across the synthetic sector before any failure occurs."*

---

#### SCENE 2 — COMPOUND DISRUPTION (10–15 seconds)
* **View:** Disruption Controls (or `SIMULATION` tab). Apply `COMPOUND_DISRUPTION`.
* **Visual Focus:**
  * Route corridor `R-01` turns red (Blocked).
  * Weather degrades to Severe Blizzard.
  * Demand surge applies ($+30\%$). Fleet reduced by $20\%$.
* **Presenter Script:**
  > *"Now we inject an operational compound disruption: a severe alpine blizzard, a major landslide blocking primary route R-01, a thirty percent surge in forward demand, and a twenty percent drop in operational fleet.  
  > In a traditional setup, headquarters wouldn't know the forward post is doomed until days later when fuel runs dry."*

---

#### SCENE 3 — PREDICT: FORECAST INTELLIGENCE (15–20 seconds)
* **View:** `FORECAST` Tab (Select Forward Post `FP-01`, Commodity: `FUEL`).
* **Visual Focus:**
  * Quantile curves: P50 (median), P80 (operational plan), P95 (stress surge).
  * Dynamic Safety Stock line and Inventory Runout trajectory.
  * Stockout Probability ($95\%+$) and Time to Zero (TTZ).
* **Presenter Script:**
  > *"PRAVAH's Forecast Intelligence does not rely on static averages. It generates probabilistic demand curves across P50, P80, and P95 stress bands.  
  > By projecting forward consumption against current reserves, the system calculates exact Time to Zero stockout hours ahead of time. It predicts logistics demand pressure—not combat events, but supply depletion."*

---

#### SCENE 4 — RISK INTELLIGENCE & PROPAGATION (15–20 seconds)
* **View:** `RISK` Tab.
* **Visual Focus:**
  * 5 normalized component bars: Inventory, Demand, Route, Transport, Environment.
  * Composite Risk Score ($\ge 0.35$ escalation).
  * Propagated network risk alerts showing how corridor `R-01` failure cascades into downstream forward posts.
* **Presenter Script:**
  > *"PRAVAH combines five distinct risk dimensions: inventory depletion, demand volatility, route accessibility, transport turnaround, and environmental weather penalties.  
  > Notice the network propagation: a blocked mountain corridor doesn't just isolate one road; it propagates acute inventory and transport risks to every dependent forward outpost."*

---

#### SCENE 5 — OPTIMIZE: CONTINUOUS FLOW LP SOLVER (20 seconds)
* **View:** `OPTIMIZATION` Tab.
* **Visual Focus:**
  * Solver Architecture banner: `Continuous Multi-Commodity Linear Flow LP (SciPy HiGHS)`.
  * Candidate movement decisions generated in $<15\text{ ms}$.
  * Objective value, total transported volume, and bypass routing selection.
* **Presenter Script:**
  > *"To solve the movement challenge, PRAVAH executes a Continuous Multi-Commodity Linear Flow LP using the SciPy HiGHS solver in under fifteen milliseconds, paired with a deterministic heuristic fleet dispatch layer.  
  > The LP computes optimal conservation of flow across alternate bypass corridors, balancing supply without manual guesswork."*

---

#### SCENE 6 — PHYSICAL FLEET FEASIBILITY VALIDATION (15 seconds)
* **View:** `RECOMMENDATIONS` Tab (Pipeline Stage Strip).
* **Visual Focus:**
  * Pipeline Strip: `55 Candidates Generated → Physical Validation & Counterfactual Verification → Feasible Actions (Rejected)`.
  * Dynamic values rendered directly from solver and conflict detector (no hardcoding).
* **Presenter Script:**
  > *"Here is a critical engineering distinction: an optimizer can produce mathematically valid flow candidates that cannot all be physically dispatched by the fleet simultaneously.  
  > PRAVAH's deterministic validation layer evaluates vehicle availability, route physical clearance, and inventory caps, filtering out conflicting candidates so only physically executable actions proceed."*

---

#### SCENE 7 — CLOSED-LOOP COUNTERFACTUAL SIMULATION (20–25 seconds)
* **View:** `SIMULATION` Tab (Closed-Loop Causal Comparison Table).
* **Visual Focus:**
  * Side-by-side table: `BASELINE (NO ACTION)` vs `INTERVENTION (PRAVAH)`.
  * Real causal deltas: Unmet Demand, Stockout Events & Duration, Fulfillment Rate %, Transport Distance km, Transit Delay hrs.
  * Tradeoff visibility: Service improves while transport distance and transit time increase.
* **Presenter Script:**
  > *"This is PRAVAH's core differentiator: Counterfactual Verification.  
  > We never execute an optimization plan blindly. We simulate the proposed dispatches in a closed-loop digital twin under the exact same disruption conditions and compare it directly against the baseline.  
  > We measure the causal impact: unmet demand drops, stockouts are averted, while acknowledging the realistic operational tradeoff of extra detour distance."*

---

#### SCENE 8 — EMPIRICAL VERIFICATION & THE TRUST STORY (15–20 seconds)
* **View:** `SIMULATION` Tab / `VerificationPanel` (Verdict Badge & Explanation).
* **Visual Focus:**
  * Verdict Badge: `VERIFIED` / `MIXED` or `DEGRADED`.
  * If `DEGRADED`: Red banner explaining that under active disruptions, the plan worsens outcomes, so PRAVAH suppressed it.
* **Presenter Script:**
  > *"What happens if high-altitude disruptions at hour 24 make the plan ineffective?  
  > In that situation, PRAVAH's counterfactual evaluator honestly returns DEGRADED.  
  > Unlike black-box optimizers that force an action, PRAVAH rejects the recommendation.  
  > This is a feature, not a bug: PRAVAH will never recommend an intervention that simulation proves makes the soldier's situation worse."*

---

#### SCENE 9 — RECOMMENDATION & REJECTION DIAGNOSTICS (15–20 seconds)
* **View:** `RECOMMENDATIONS` Tab.
* **Visual Focus:**
  * Filtered Table: Priority (P1/P2), Action (REALLOCATE/MOVE), Route, Quantity, Assigned Vehicle, Departure Window, Status (`VERIFIED` or `REJECTED`).
  * Rejection Summary Banner: Plain-language breakdown of vehicle conflicts or counterfactual degradation.
* **Presenter Script:**
  > *"In the Decision Center, commanders receive verified, executable movement orders with specific convoy assignments, departure windows, and route corridors.  
  > If candidates were rejected, the audit banner explains the exact reason in plain language—whether due to concurrent vehicle availability or counterfactual degradation."*

---

#### SCENE 10 — EXPLAINABILITY, EVIDENCE & LINEAGE (10–15 seconds)
* **View:** `AUDIT` Tab or Recommendation Detail Drawer.
* **Visual Focus:**
  * Structured bullets under `WHY THIS DECISION?`.
  * Provenance Audit Trail: `disruption_event`, `forecast_model`, `optimization_run_id`, `evaluation_id`.
  * Structured clickable evidence items.
* **Presenter Script:**
  > *"Every recommendation is fully auditable. A commander can trace any dispatch back to the sensor disruption that triggered it, the quantile forecast that quantified the pressure, the LP solve that routed it, and the simulation that verified it. Full deterministic provenance."*

---

#### SCENE 11 — FINAL MESSAGE (10 seconds)
* **View:** Return to `COMMAND_CENTER`.
* **Presenter Script:**
  > *"PRAVAH is not an autonomous commander making reckless automated decisions.  
  > It is an auditable, evidence-backed decision-support system built for forward logistics commanders.  
  > Don't wait for the shortage. Predict before shortage. Verify before action.  
  > Thank you, we are ready for your questions."*

---

## 5. Technical Architecture & Math Grounding for Judges

When technical judges ask deep-dive questions, use the exact verified engineering facts:

### 1. Forecasting Layer:
* **Model:** Quantile Gradient Boosted Regression (XGBoost) outputting $\tau \in \{0.50, 0.80, 0.95\}$.
* **Features:** Lagged consumption ($t-1, t-2, t-24$), rolling statistics ($6\text{h}, 24\text{h}$ means & std dev), weather condition index, road quality score, convoy status.
* **Uncertainty Propagation:** Monte Carlo simulation ($N=1,000$ iterations) calculates stockout probability and Time to Zero (TTZ).

### 2. Optimization Layer:
* **Formulation:** Continuous Multi-Commodity Linear Flow LP.
* **Solver:** SciPy HiGHS dual-simplex/interior point solver ($<15\text{ ms}$ solve time).
* **Decision Variables:** Continuous flow $f_{u, v, c, t} \ge 0$ for commodity $c$ across edge $(u,v)$ at time $t$, plus nodal shortage variables $s_{n, c, t} \ge 0$.
* **Constraints:** Flow conservation per node and commodity, corridor capacity, aggregate vehicle volume limits, dynamic inventory bounds.
* **Dispatch Layer:** Deterministic heuristic assigns continuous flow quantities to physical discrete vehicles ($V_{1}\dots V_{12}$), enforcing single vehicle assignment per hour.

### 3. Counterfactual Simulation Layer:
* **Engine:** Discrete-event logistics digital twin running deterministic step-by-step physics ($72\text{ hours}$, 1-hour resolution).
* **Controlled Evaluation:** Paired baseline run (zero intervention) vs intervention run, with identical random seed (`seed=42`) and identical disruption timeline.
* **Verdict Logic:** Evaluates causal deltas across unmet demand, stockouts, fulfillment rate, distance, and delays:
  * `VERIFIED`: Unmet demand improved, stockouts mitigated, no severe constraint violations.
  * `MIXED`: Forward service significantly improved, but transit distance/delay increased due to mountain detour.
  * `DEGRADED`: Unmet demand increased or stockouts exacerbated vs baseline. System immediately rejects candidates.

---

## 6. Live Demo Failure Protection & Fallback Flow

If a live network glitch, browser delay, or API failure occurs during the presentation:

| Point of Failure | System Behavior | Presenter Action / Script |
| :--- | :--- | :--- |
| **API Call Times Out / Fails** | Frontend retains last successfully loaded verified state. | *"The system preserves the last verified telemetry snapshot, maintaining mission continuity even under communication dropouts."* |
| **Solver Returns Zero Candidates** | Solver reports `NO_FEASIBLE_FLOW` (properly handled). | *"All corridors are interdicted; PRAVAH correctly flags network isolation rather than proposing impossible dispatches."* |
| **Evaluation Shows DEGRADED** | Status badge displays red `DEGRADED` and rejection banner. | *"Notice PRAVAH's safety verification: because the intervention worsens outcomes under active blizzard, the system safely rejects it."* |
| **Browser Refresh Needed** | Default seed 42 and `COMPOUND_DISRUPTION` auto-populate. | Continue immediately from Step 1; all states are fully deterministic and reproducible. |

**Golden Rule:** NEVER fabricate metrics. NEVER hardcode temporary numbers. Always explain the actual state.

---

## 7. Approved Terminology vs. Banned Phrases

| Concept | Approved Terminology (USE THIS) | Banned / Unsupported Phrase (DO NOT USE) |
| :--- | :--- | :--- |
| **System Role** | "predictive logistics decision support" | "battlefield autonomous decision-making" |
| **Automation** | "human-in-the-loop decision intelligence" | "fully autonomous military logistics" |
| **Forecasting** | "uncertainty-aware quantile demand forecast" | "combat prediction" / "100% accurate forecast" |
| **Guarantees** | "risk-aware forward stockout mitigation" | "guaranteed prevention of shortages" |
| **Validation** | "physical fleet feasibility validation" | "instant magical routing" |
| **Simulation** | "paired counterfactual closed-loop simulation" | "AI that knows the future" |
| **Optimization** | "Continuous Multi-Commodity Linear Flow LP" | "pure MILP" / "black-box deep learning optimizer" |
| **Operational Data**| "synthetic demonstration environment" | "real-time classified Army deployment" |

---

## 8. Demo Tour Quick Reference (In-App Guided Tour)

The in-app `DemoTour` component provides a 12-step guided interactive walkthrough accessible via the `DEMO MODE` button in the header:

1. **Step 1:** Normal Logistics Topology (Command Center overview)
2. **Step 2:** Trigger Compound Disruption (Corridor blockage, surge, blizzard)
3. **Step 3:** Risk Intelligence & Propagation (5 risk dimensions, network spread)
4. **Step 4:** Forward Outpost Drill-Down (Inspect `FP-01` fuel depletion)
5. **Step 5:** Uncertainty-Aware Demand Forecast (P50/P80/P95 quantiles)
6. **Step 6:** Monte Carlo Stockout Risk & TTZ (Time to zero projection)
7. **Step 7:** Continuous Multi-Commodity LP Optimization (SciPy HiGHS $<15\text{ ms}$)
8. **Step 8:** Physical Fleet Feasibility Validation (Eliminate conflicting assignments)
9. **Step 9:** Paired Counterfactual Simulation (Controlled baseline vs intervention)
10. **Step 10:** Empirical Verification & Safety Rejection (Trust story: VERIFIED vs DEGRADED)
11. **Step 11:** Evidence-Backed Recommendations (Executable orders with vehicle & route)
12. **Step 12:** Auditable Evidence & System Stance (Full deterministic causal lineage)

**Completion Time:** 2 minutes 15 seconds at conversational pacing.
