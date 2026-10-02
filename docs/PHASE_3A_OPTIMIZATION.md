# PRAVAH Phase 3A: Mathematical Optimization Core

**PS 26251 — Indian Army Predictive Logistics & Forward Supply Chain**  
**Component:** Risk-Aware Multi-Echelon Logistics Optimization Engine  
**Branch:** `phase-3-optimization`  

---

## 1. System Role & Conceptual Distinction

PRAVAH maintains a strict conceptual and architectural separation between three core operational engines:

| Engine | Primary Question | Underlying Methodology | Determinism |
| :--- | :--- | :--- | :--- |
| **Prediction Engine** (Phase 2) | *What will forward consumption and operational risk look like in the next 24h, 72h, and 168h?* | Quantile Gradient Boosting (`xgb.XGBRegressor`), Autoregressive Lags, Monte Carlo Uncertainty Sampling | Probabilistic (P50, P80, P95) |
| **Simulation Engine** (Phase 1) | *What happens dynamically to stock, convoys, and pass accessibility as time advances hour-by-hour under disruption?* | Discrete-Time Multi-Echelon State-Transition Simulator | Deterministic state evolution |
| **Optimization Engine** (Phase 3A) | *Given current stock, predicted demand, uncertainty, route conditions, vehicle limits, and risks, what movement plan minimizes expected logistics failure?* | Mixed-Integer / Linear Programming (SciPy HiGHS MILP) & Priority Greedy Heuristic | Deterministic mathematical optimum |

---

## 2. Mathematical Optimization Formulation

The logistics network is modeled as a directed multi-commodity network graph:
$$\mathcal{G} = (\mathcal{V}, \mathcal{E})$$
where:
* $\mathcal{V}$ is the set of logistics nodes (Central Depots, Regional Hubs, Transit Points, Forward Posts).
* $\mathcal{E}$ is the set of directed, traversable route segments between nodes.
* $\mathcal{K} = \{\text{FUEL}, \text{RATIONS}, \text{AMMUNITION}, \text{MEDICAL}, \text{WATER}\}$ is the set of critical supply commodities.

---

## 3. Decision Variables

The model registers the following decision variables:

1. **Flow Variables ($x_{i,j,r,k} \ge 0$):**  
   Quantity of commodity $k \in \mathcal{K}$ transported from source node $i$ to destination node $j$ along route segment $r \in \mathcal{E}$.
   $$\text{Bounds: } 0 \le x_{i,j,r,k} \le \min\left(\text{AvailableSupply}[i, k], \; \text{RouteCapacity}[r]\right)$$

2. **Shortage Variables ($u_{j,k} \ge 0$):**  
   Shortage / unmet demand quantity of commodity $k$ at destination node $j$ over the planning horizon.
   $$\text{Bounds: } 0 \le u_{j,k} \le \text{RequiredDemand}[j, k]$$

3. **Vehicle Assignment Variables ($v_{v,r} \in \{0, 1\}$):**  
   Binary assignment of available transport vehicle $v$ to route corridor $r$.

---

## 4. Constraints

### A. Source Supply Constraints
No source depot or regional hub may dispatch more volume of any commodity than its verified on-hand stock:
$$\sum_{(j, r) \in \text{Out}(i)} x_{i,j,r,k} \le \text{AvailableSupply}[i, k], \quad \forall i \in \mathcal{V}_{\text{source}}, \; \forall k \in \mathcal{K}$$

### B. Destination Demand Fulfillment & Shortage Balance
For every destination forward post or transit hub, inbound dispatches plus permissible shortage slack must satisfy required demand:
$$\sum_{(i, r) \in \text{In}(j)} x_{i,j,r,k} + u_{j,k} \ge \text{RequiredDemand}[j, k], \quad \forall j \in \mathcal{V}_{\text{dest}}, \; \forall k \in \mathcal{K}$$

### C. Route Capacity Constraints
The sum of all commodity flows traversing route corridor $r$ must not exceed its physical throughput limit:
$$\sum_{k \in \mathcal{K}} x_{i,j,r,k} \le \text{Capacity}[r], \quad \forall r = (i, j) \in \mathcal{E}$$
* **Blocked Routes:** If $\text{Status}[r] = \text{BLOCKED}$, $\text{Capacity}[r] = 0$.
* **Degraded Routes:** If $\text{Status}[r] = \text{DEGRADED}$, $\text{Capacity}[r] = 0.60 \times \text{MaxCapacity}[r]$.

### D. Vehicle Capacity Constraints
Each individual movement order allocated to vehicle $v$ is bounded by its payload rating:
$$x_{i,j,r,k} \le \text{Capacity}[v]$$
Unavailable vehicles ($\text{Status} \ne \text{AVAILABLE}$) cannot be assigned to any route.

---

## 5. Objective Function

The optimizer minimizes total operational penalty across five transparent, configurable dimensions:

$$\min Z = C_{\text{transport}} + \lambda_{\text{shortage}} \cdot C_{\text{shortage}} + \lambda_{\text{delay}} \cdot C_{\text{delay}} + \lambda_{\text{risk}} \cdot C_{\text{risk}} + \lambda_{\text{imbalance}} \cdot C_{\text{imbalance}}$$

### Component Formulations:
1. **Transport Cost:**
   $$C_{\text{transport}} = \sum_{i,j,r,k} x_{i,j,r,k} \cdot \left(\frac{\text{Distance}[r]}{50.0}\right)$$

2. **Shortage Penalty with Priority Protection:**
   $$C_{\text{shortage}} = \sum_{j, k} u_{j,k} \cdot \left(1.0 + 0.5 \cdot (\text{Priority}[j] - 1)\right) \cdot (1.0 + \text{Risk}[j])$$
   *Frontline Forward Posts (Priority 5) incur a $3.0\times$ heavier base shortage penalty than base depots (Priority 1), ensuring scarce supplies protect frontline positions first.*

3. **Transit Delay Cost:**
   $$C_{\text{delay}} = \sum_{i,j,r,k} x_{i,j,r,k} \cdot \max\left(0, \text{EffectiveTravelHours}[r] - \text{BaseTravelHours}[r]\right)$$

4. **Risk-Aware Corridor Penalty:**
   $$C_{\text{risk}} = \sum_{i,j,r,k} x_{i,j,r,k} \cdot \left(\text{RouteRisk}[r] \cdot 10.0 + \mathbb{I}_{\text{DEGRADED}}[r] \cdot 15.0\right)$$
   *Mathematical Tradeoff: When a short route has extreme risk ($\text{Risk} = 0.95$), the risk penalty dominates the distance term, naturally directing the solver to choose a slightly longer, safer detour.*

---

## 6. Demand Policies

The optimizer supports three configurable forecast policies:
* **`P50` Policy:** Calibrated for nominal baseline operations under normal weather.
* **`P80` Policy:** Elevated buffer policy for tactical defense operations with anticipated friction.
* **`P95` Policy:** Extreme surge policy under compound disruption, extreme cold, or active conflict.

Every run records `demand_policy`, `forecast_version`, and `feature_version` for audit traceability.

---

## 7. Solver Architecture & Heuristic Fallback

```text
       ┌───────────────────────────────┐
       │     OptimizationProblem       │
       └──────────────┬────────────────┘
                      │
                      ▼
       ┌───────────────────────────────┐
       │         MilpSolver            │
       │    (SciPy HiGHS Solver)       │
       └──────┬─────────────────┬──────┘
              │                 │
     Success  │                 │ Infeasible / Error
              ▼                 ▼
   ┌────────────────────┐   ┌──────────────────────────────┐
   │ OptimizationResult │   │   PriorityHeuristicSolver    │
   │  (Status: OPTIMAL) │   │ (Greedy Safe-Path Fallback)  │
   └────────────────────┘   └──────────────┬───────────────┘
                                           │
                                           ▼
                                ┌────────────────────┐
                                │ OptimizationResult │
                                │ (fallback_used)    │
                                └────────────────────┘
```

* **Primary Engine:** `scipy.optimize.linprog(method='highs')`, executing in $\approx 10\text{ ms}$.
* **Deterministic Fallback:** `PriorityHeuristicSolver` ranks deficits by priority and routes supply greedily along safest topological paths using NetworkX Dijkstra shortest-path calculations.

---

## 8. Infeasibility & Bound Handling

The solver explicitly returns standard OR status codes:
* `OPTIMAL`: Feasible optimal plan found satisfying all constraints.
* `FEASIBLE`: Sub-optimal or heuristic plan found.
* `INFEASIBLE`: No feasible movement can satisfy constraints; returns structured root-cause list (`infeasibility_reasons`).
* `UNBOUNDED` / `ERROR`: Handled cleanly without throwing uncaught exceptions.

---

## 9. REST API Contract

### Solve Endpoint
* **Method:** `POST /api/optimization/solve`
* **Payload:**
```json
{
  "scenario_id": "COMPOUND_DISRUPTION",
  "demand_policy": "P80",
  "solver_type": "MILP",
  "objective_weights": {
    "transport": 1.0,
    "shortage": 50.0,
    "delay": 3.0,
    "risk": 10.0,
    "imbalance": 1.0
  },
  "horizon_hours": 72
}
```

### Retrieval Endpoint
* **Method:** `GET /api/optimization/{run_id}`
* **Response:** Returns complete `OptimizationSolveResponse` containing all allocated decisions and utilization metrics.

---

## 10. Security & Safety Boundary

PRAVAH is a decision-support and logistics research platform. All entities, geographic coordinates, pass networks, and fleet assignments are synthetic abstractions designed to model the mathematical constraints of high-altitude logistics. Plans generated are decision-support recommendations for simulation analysis.
