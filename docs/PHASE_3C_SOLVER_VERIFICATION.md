# Solver Verification

## Actual Solver API
The primary solver implementation in [`optimization/solver.py`](file:///c:/Users/HP/Desktop/Pravah/optimization/solver.py) (`MilpSolver`) invokes:
```python
res = scipy.optimize.linprog(
    c=c,
    A_ub=A_ub if len(A_ub) > 0 else None,
    b_ub=b_ub if len(b_ub) > 0 else None,
    bounds=bounds,
    method="highs",
)
```
The underlying execution engine is the **HiGHS Simplex / Interior-Point C++ library** bundled with SciPy (`method="highs"`).

---

## Mathematical Problem Actually Solved
The mathematical formulation solved by `linprog` is a **Continuous Multi-Commodity Minimum-Cost Network Flow Linear Program (LP)** with shortage penalties:

$$\min_{x \ge 0, u \ge 0} \sum_{(i,j,r,k)} c_{i,j,r,k} x_{i,j,r,k} + \sum_{(j,k)} w_{\text{short}} u_{j,k}$$

Subject to:
1. **Supply Outflow Constraints** (depots/hubs):
   $$\sum_{j, r} x_{i,j,r,k} \le \text{AvailableSupply}_{i,k} \quad \forall i, k$$
2. **Demand Inflow with Shortage Penalties** (forward posts):
   $$\sum_{i, r} x_{i,j,r,k} + u_{j,k} \ge \text{RequiredDemand}_{j,k} \quad \forall j, k$$
3. **Route Capacity Constraints**:
   $$\sum_{k} x_{i,j,r,k} \le \text{EffectiveRouteCapacity}_r \quad \forall r$$
4. **Boundary Conditions**:
   $$0 \le x_{i,j,r,k} \le \min(\text{AvailableSupply}_{i,k}, \text{RouteCapacity}_r)$$
   $$0 \le u_{j,k} \le \text{RequiredDemand}_{j,k}$$

---

## Variable Types
All variables submitted to the HiGHS solver matrix are **continuous real numbers** ($\mathbb{R}_{\ge 0}$):
- $x_{i,j,r,k} \in [0, \text{ub}_{i,j,r,k}]$ (Flow volume of commodity $k$ across route $r$).
- $u_{j,k} \in [0, \text{demand}_{j,k}]$ (Unfulfilled demand slack / shortage).

No discrete or integer variables are present in the matrix vector $z = [x, u]^T$.

---

## Integer/Binary Enforcement
- **Matrix Level**: Binary vehicle assignment variables $v_{v,r} \in \{0, 1\}$ described in theoretical documentation are **not present** in the matrix passed to `linprog()`.
- **Integrality Parameter**: The `integrality` argument of `scipy.optimize.linprog(method="highs")` is **not passed**.
- **Conclusion**: There is **no mathematical mixed-integer programming (MILP) branch-and-bound/cut solve** occurring inside the matrix solver.

---

## Constraint Enforcement
- **Supply Constraints**: Genuinely and strictly enforced by the linear matrix inequalities $A_{\text{ub}} z \le b_{\text{ub}}$.
- **Demand Satisfaction**: Genuinely enforced via linear constraints with shortage slacks $u$.
- **Route Capacity**: Genuinely enforced, including reduced capacity on `DEGRADED` routes ($0.6 \times \text{capacity}$) and zero flow on `BLOCKED` routes ($0 \times \text{capacity}$).
- **Vehicle Constraints**: **Not enforced in the mathematical matrix**. Instead, vehicle constraints are handled downstream during post-solve assignment.

---

## Objective Calculation
The objective value returned by the solver is the exact scalar evaluation of the continuous linear program:
$$\text{obj} = c^T z = \text{transport\_cost} + \text{shortage\_penalty} + \text{risk\_cost} + \text{delay\_cost}$$
It accurately represents the cost of the optimal continuous network flow. It does not include fixed vehicle dispatch costs or post-hoc rounding adjustments.

---

## Rounding / Post-processing
Following the HiGHS continuous solve, the solver executes a deterministic post-solve conversion:
1. Flow paths where $x_{i,j,r,k} > 10^{-3}$ are extracted.
2. Available vehicles are assigned round-robin across active flows.
3. If a flow exceeds a vehicle's payload capacity, the flow is partitioned into sequential shipments of $\le \text{veh\_cap}$.
4. Shipment quantities are rounded to 1 decimal place (`round(batch_qty, 1)`).

### Potential Vulnerabilities of Post-Processing
1. **Fleet Over-Subscription**: If the number of flows exceeds available vehicles, vehicles are reused across routes at the same dispatch hour ($t=0$) without enforcing simultaneous temporal availability in the matrix.
2. **Rounding Slack**: While `round(batch_qty, 1)` is generally benign, in edge cases summing multiple rounded batches could theoretically drift by $\pm 0.1\text{ units}$. (Phase 3B's pre-simulation feasibility validator explicitly catches any resulting discrepancies).

---

## OPTIMAL Status Meaning
The status `OptimizationStatus.OPTIMAL` returned by the engine means:
> **The continuous multi-commodity network flow linear program (LP) was solved to global mathematical optimality by the HiGHS solver.**

It does **not** mean that an NP-hard Mixed Integer Linear Program with binary vehicle routing was solved to integer optimality.

---

## Determinism
The HiGHS solver and post-processing routine are **100% deterministic**:
- Identical network states and demand vectors produce bitwise identical continuous flow allocations $x^*$ and identical post-processed movement decisions.
- Regression tests (`test_deterministic_evaluation`) verify end-to-end reproducibility.

---

## Findings
1. The solver is **not a true MILP solver**; it is a **Continuous Linear Program (LP) solver coupled with a heuristic post-processing fleet allocator**.
2. Labeling the solver solely as "MILP" without qualification is a semantic misclassification.
3. The LP continuous flow formulation is mathematically rigorous, fast ($\approx 6\text{ ms}$), stable, and highly effective for bulk logistics commodities (fuel, rations, medical supplies, water).
4. The post-solve vehicle batching and subsequent Phase 3B physical simulation ensure that all movements are physically validated before execution.

---

## Required Corrections
1. **Semantic Transparency**: Update metadata in `OptimizationResult` to explicitly declare `solver_classification: "LP_FLOW_WITH_HEURISTIC_DISPATCH"` and `is_pure_milp: False`.
2. **Retain Backward Compatibility**: Retain `SolverType.MILP` as the public enum key to prevent breaking Phase 3A/3B callers and tests, while documenting its true hybrid LP nature.
3. **No Heavy External Solver Dependency**: Do not introduce heavy or non-portable external solvers (e.g. PuLP, Gurobi, or external binaries) when SciPy HiGHS solves the linear flow core with high performance and zero external dependencies.

---

## Final Solver Classification
```text
SOLVER CLASSIFICATION:
HYBRID (Continuous Multi-Commodity Network Flow LP via SciPy HiGHS + Heuristic Fleet Dispatch)
```
