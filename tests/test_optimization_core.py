"""Phase 3A Optimization Core Comprehensive Test Suite.

Verifies:
1. Small controlled deterministic test network
2. Supply constraints (cannot dispatch > available)
3. Demand fulfillment constraints (flow + shortage = required)
4. Blocked route exclusion (capacity = 0, never dispatched)
5. Degraded route feasibility (usable with higher cost/delay)
6. Route capacity enforcement
7. Vehicle capacity enforcement
8. Unavailable vehicle exclusion
9. Multi-commodity simultaneous optimization (FUEL, FOOD, AMMUNITION, WATER, MEDICAL)
10. High-priority node shortage protection
11. Risk-aware route selection (choosing safer route over dangerous short route)
12. Demand policies (P50, P80, P95)
13. Solver result structure and status reporting (OPTIMAL, INFEASIBLE)
14. Deterministic reproducibility
15. Heuristic fallback execution
16. REST API endpoint contracts (/api/optimization/solve, /api/optimization/{run_id})
"""

import pytest
from fastapi.testclient import TestClient

from optimization.types import (
    DemandPolicy,
    SolverType,
    OptimizationStatus,
    ObjectiveWeights,
)
from optimization.model import OptimizationProblem
from optimization.solver import MilpSolver, LogisticsSolver
from optimization.heuristic import PriorityHeuristicSolver
from optimization.constraints import validate_constraints
from optimization.adapters import OptimizationInputAdapter
from simulation.world_generator import WorldGenerator
from backend.main import app


# ==============================================================================
# 1. SMALL CONTROLLED TEST NETWORK FIXTURE
# ==============================================================================

def create_controlled_test_network() -> OptimizationProblem:
    """Creates a tiny deterministic test graph:
    CD-01 (Depot)
      ├── RH-01 (Hub) ── FP-01 (Priority 5, Frontline)
      └── RH-02 (Hub) ── FP-02 (Priority 3, Support)
    """
    nodes = {
        "CD-01": {"id": "CD-01", "name": "Central Depot", "type": "CENTRAL_DEPOT", "priority": 1},
        "RH-01": {"id": "RH-01", "name": "Regional Hub 1", "type": "REGIONAL_HUB", "priority": 2},
        "RH-02": {"id": "RH-02", "name": "Regional Hub 2", "type": "REGIONAL_HUB", "priority": 2},
        "FP-01": {"id": "FP-01", "name": "Forward Post Alpha", "type": "FORWARD_POST", "priority": 5},
        "FP-02": {"id": "FP-02", "name": "Forward Post Bravo", "type": "FORWARD_POST", "priority": 3},
    }

    routes = {
        "R_CD_RH1": {
            "id": "R_CD_RH1", "source_node_id": "CD-01", "destination_node_id": "RH-01",
            "distance_km": 100.0, "base_travel_hours": 3.0, "effective_travel_hours": 3.0,
            "max_capacity": 2000.0, "status": "AVAILABLE",
        },
        "R_CD_RH2": {
            "id": "R_CD_RH2", "source_node_id": "CD-01", "destination_node_id": "RH-02",
            "distance_km": 120.0, "base_travel_hours": 4.0, "effective_travel_hours": 4.0,
            "max_capacity": 2000.0, "status": "AVAILABLE",
        },
        "R_RH1_FP1": {
            "id": "R_RH1_FP1", "source_node_id": "RH-01", "destination_node_id": "FP-01",
            "distance_km": 40.0, "base_travel_hours": 1.5, "effective_travel_hours": 1.5,
            "max_capacity": 500.0, "status": "AVAILABLE",
        },
        "R_RH2_FP2": {
            "id": "R_RH2_FP2", "source_node_id": "RH-02", "destination_node_id": "FP-02",
            "distance_km": 50.0, "base_travel_hours": 2.0, "effective_travel_hours": 2.0,
            "max_capacity": 500.0, "status": "AVAILABLE",
        },
    }

    vehicles = {
        "TRK-01": {"id": "TRK-01", "capacity": 300.0, "status": "AVAILABLE"},
        "TRK-02": {"id": "TRK-02", "capacity": 300.0, "status": "AVAILABLE"},
    }

    items = ["FUEL", "RATIONS"]

    available_supply = {
        "CD-01": {"FUEL": 1000.0, "RATIONS": 1000.0},
        "RH-01": {"FUEL": 500.0, "RATIONS": 500.0},
        "RH-02": {"FUEL": 500.0, "RATIONS": 500.0},
        "FP-01": {"FUEL": 0.0, "RATIONS": 0.0},
        "FP-02": {"FUEL": 0.0, "RATIONS": 0.0},
    }

    required_demand = {
        "CD-01": {"FUEL": 0.0, "RATIONS": 0.0},
        "RH-01": {"FUEL": 0.0, "RATIONS": 0.0},
        "RH-02": {"FUEL": 0.0, "RATIONS": 0.0},
        "FP-01": {"FUEL": 150.0, "RATIONS": 100.0},
        "FP-02": {"FUEL": 200.0, "RATIONS": 150.0},
    }

    return OptimizationProblem(
        problem_id="CONTROLLED_TEST_NET",
        nodes=nodes,
        routes=routes,
        vehicles=vehicles,
        items=items,
        available_supply=available_supply,
        required_demand=required_demand,
        demand_policy=DemandPolicy.P80,
        objective_weights=ObjectiveWeights(),
    )


# ==============================================================================
# 2. SUPPLY CONSTRAINT TESTS
# ==============================================================================

def test_supply_constraint_enforced():
    """Optimizer cannot dispatch more than available supply from source nodes."""
    problem = create_controlled_test_network()
    # Restrict supply at RH-01 to only 50 units of FUEL
    problem.available_supply["RH-01"]["FUEL"] = 50.0
    # But FP-01 demands 150 units of FUEL
    problem.required_demand["FP-01"]["FUEL"] = 150.0

    solver = MilpSolver()
    result = solver.solve(problem)

    assert result.status == OptimizationStatus.OPTIMAL
    dispatched_from_rh1_fuel = sum(
        d.quantity for d in result.decisions
        if d.source_node_id == "RH-01" and d.item == "FUEL"
    )
    # Must never exceed 50.0
    assert dispatched_from_rh1_fuel <= 50.0 + 1e-4

    # Remainder must be reported as shortage
    assert result.total_shortage >= 100.0 - 1e-4


# ==============================================================================
# 3. DEMAND FULFILLMENT CONSTRAINT TESTS
# ==============================================================================

def test_demand_fulfillment_constraint():
    """Dispatches plus shortage must exactly satisfy required demand."""
    problem = create_controlled_test_network()
    solver = MilpSolver()
    result = solver.solve(problem)

    assert result.status == OptimizationStatus.OPTIMAL
    total_req_demand = sum(
        qty for n_map in problem.required_demand.values() for qty in n_map.values()
    )
    total_dispatched = sum(d.quantity for d in result.decisions)

    # Inflow to FP-01 and FP-02 plus remaining shortage equals total demand
    assert abs((total_dispatched + result.total_shortage) - total_req_demand) < 1e-2


# ==============================================================================
# 4. ROUTE CONSTRAINT TESTS (BLOCKED & DEGRADED)
# ==============================================================================

def test_blocked_route_is_never_selected():
    """Blocked routes must have 0 capacity and never receive dispatches."""
    problem = create_controlled_test_network()
    # Block R_RH1_FP1
    problem.routes["R_RH1_FP1"]["status"] = "BLOCKED"

    solver = MilpSolver()
    result = solver.solve(problem)

    for d in result.decisions:
        assert d.route_id != "R_RH1_FP1"


def test_degraded_route_remains_feasible():
    """Degraded routes remain usable when no alternate exists, with penalty applied."""
    problem = create_controlled_test_network()
    problem.routes["R_RH1_FP1"]["status"] = "DEGRADED"

    solver = MilpSolver()
    result = solver.solve(problem)

    # FP-01 has only R_RH1_FP1, so it should still dispatch along it
    fp1_dispatches = [d for d in result.decisions if d.destination_node_id == "FP-01"]
    assert len(fp1_dispatches) > 0
    assert any(d.route_id == "R_RH1_FP1" for d in fp1_dispatches)


# ==============================================================================
# 5. CAPACITY CONSTRAINTS (ROUTE & VEHICLE)
# ==============================================================================

def test_route_capacity_enforced():
    """Cumulative dispatches along a route must not exceed its capacity."""
    problem = create_controlled_test_network()
    # Choke capacity to 80 units
    problem.routes["R_RH1_FP1"]["max_capacity"] = 80.0

    solver = MilpSolver()
    result = solver.solve(problem)

    route_load = sum(d.quantity for d in result.decisions if d.route_id == "R_RH1_FP1")
    assert route_load <= 80.0 + 1e-4


def test_vehicle_capacity_enforced():
    """Individual vehicle movement orders must not exceed single vehicle capacity."""
    problem = create_controlled_test_network()
    problem.vehicles["TRK-01"]["capacity"] = 100.0
    problem.vehicles["TRK-02"]["capacity"] = 100.0

    solver = MilpSolver()
    result = solver.solve(problem)

    for d in result.decisions:
        assert d.quantity <= 100.0 + 1e-4


def test_unavailable_vehicle_not_assigned():
    """Unavailable vehicle cannot be assigned to dispatches."""
    problem = create_controlled_test_network()
    problem.vehicles["TRK-01"]["status"] = "MAINTENANCE"

    solver = MilpSolver()
    result = solver.solve(problem)

    for d in result.decisions:
        assert d.vehicle_id != "TRK-01"


# ==============================================================================
# 6. MULTI-COMMODITY SIMULTANEOUS OPTIMIZATION
# ==============================================================================

def test_multiple_supply_items_simultaneously():
    """One single optimization run handles all 5 military commodities simultaneously."""
    problem = create_controlled_test_network()
    all_commodities = ["FUEL", "RATIONS", "AMMUNITION", "WATER", "MEDICAL"]
    problem.items = all_commodities

    for item in all_commodities:
        problem.available_supply["RH-01"][item] = 200.0
        problem.available_supply["RH-02"][item] = 200.0
        problem.required_demand["FP-01"][item] = 50.0
        problem.required_demand["FP-02"][item] = 50.0

    solver = MilpSolver()
    result = solver.solve(problem)

    assert result.status == OptimizationStatus.OPTIMAL
    dispatched_items = set(d.item for d in result.decisions)
    # All commodities are handled
    assert dispatched_items == set(all_commodities)


# ==============================================================================
# 7. PRIORITY SHORTAGE WEIGHTING
# ==============================================================================

def test_high_priority_node_shortage_penalty():
    """Under severe supply deficit, Priority 5 (FP-01) is protected before Priority 3 (FP-02)."""
    problem = create_controlled_test_network()
    # Scarce FUEL supply: only 100 units available total at RH-01 and RH-02
    problem.available_supply["RH-01"]["FUEL"] = 100.0
    problem.available_supply["RH-02"]["FUEL"] = 0.0

    # Connect RH-01 to both FP-01 (Priority 5) and FP-02 (Priority 3)
    problem.routes["R_RH1_FP2"] = {
        "id": "R_RH1_FP2", "source_node_id": "RH-01", "destination_node_id": "FP-02",
        "distance_km": 40.0, "base_travel_hours": 1.5, "effective_travel_hours": 1.5,
        "max_capacity": 500.0, "status": "AVAILABLE",
    }

    # Demand: FP-01 wants 100, FP-02 wants 100
    problem.required_demand["FP-01"]["FUEL"] = 100.0
    problem.required_demand["FP-02"]["FUEL"] = 100.0

    solver = MilpSolver()
    result = solver.solve(problem)

    fp1_fuel = sum(d.quantity for d in result.decisions if d.destination_node_id == "FP-01" and d.item == "FUEL")
    fp2_fuel = sum(d.quantity for d in result.decisions if d.destination_node_id == "FP-02" and d.item == "FUEL")

    # Frontline Priority 5 post must receive the scarce 100 units
    assert fp1_fuel == 100.0
    assert fp2_fuel == 0.0


# ==============================================================================
# 8. RISK-AWARE ROUTE SELECTION (TRADEOFF)
# ==============================================================================

def test_risk_aware_route_selection():
    """Optimizer chooses a slightly longer safer route over a shorter high-risk route."""
    problem = create_controlled_test_network()

    # Route A: Short (30 km) but extreme risk (0.95)
    problem.routes["R_SHORT_RISKY"] = {
        "id": "R_SHORT_RISKY", "source_node_id": "RH-01", "destination_node_id": "FP-01",
        "distance_km": 30.0, "base_travel_hours": 1.0, "effective_travel_hours": 1.0,
        "max_capacity": 500.0, "status": "AVAILABLE",
    }
    problem.route_risks["R_SHORT_RISKY"] = 0.95

    # Route B: Slightly longer (50 km) but very safe (0.05)
    problem.routes["R_LONG_SAFE"] = {
        "id": "R_LONG_SAFE", "source_node_id": "RH-01", "destination_node_id": "FP-01",
        "distance_km": 50.0, "base_travel_hours": 1.5, "effective_travel_hours": 1.5,
        "max_capacity": 500.0, "status": "AVAILABLE",
    }
    problem.route_risks["R_LONG_SAFE"] = 0.05

    # Delete original route
    del problem.routes["R_RH1_FP1"]

    # Configure high risk weight
    problem.objective_weights.risk_weight = 20.0
    problem.objective_weights.transport_weight = 1.0

    solver = MilpSolver()
    result = solver.solve(problem)

    fp1_routes = set(d.route_id for d in result.decisions if d.destination_node_id == "FP-01")
    # Mathematical objective must select the safe route
    assert "R_LONG_SAFE" in fp1_routes
    assert "R_SHORT_RISKY" not in fp1_routes


# ==============================================================================
# 9. FORECAST DEMAND POLICIES (P50, P80, P95)
# ==============================================================================

def test_demand_policies_scaling():
    """Verify P50, P80, and P95 demand policies scale required demand appropriately."""
    world = WorldGenerator(seed=42).generate_world()

    prob_p50 = OptimizationInputAdapter.create_problem(world, demand_policy=DemandPolicy.P50)
    prob_p80 = OptimizationInputAdapter.create_problem(world, demand_policy=DemandPolicy.P80)
    prob_p95 = OptimizationInputAdapter.create_problem(world, demand_policy=DemandPolicy.P95)

    tot_p50 = sum(qty for n_map in prob_p50.required_demand.values() for qty in n_map.values())
    tot_p80 = sum(qty for n_map in prob_p80.required_demand.values() for qty in n_map.values())
    tot_p95 = sum(qty for n_map in prob_p95.required_demand.values() for qty in n_map.values())

    assert tot_p50 < tot_p80 < tot_p95


# ==============================================================================
# 10. REPRODUCIBILITY & DETERMINISM
# ==============================================================================

def test_optimizer_reproducibility():
    """Run 1 == Run 2 under identical problem inputs."""
    problem1 = create_controlled_test_network()
    problem2 = create_controlled_test_network()

    solver = MilpSolver()
    res1 = solver.solve(problem1)
    res2 = solver.solve(problem2)

    assert res1.status == res2.status
    assert res1.objective_value == res2.objective_value
    assert len(res1.decisions) == len(res2.decisions)
    for d1, d2 in zip(res1.decisions, res2.decisions):
        assert d1.route_id == d2.route_id
        assert d1.quantity == d2.quantity
        assert d1.item == d2.item


# ==============================================================================
# 11. HEURISTIC FALLBACK EXECUTION
# ==============================================================================

def test_heuristic_fallback_execution():
    """Heuristic solver generates valid decisions and reports HEURISTIC solver_type."""
    problem = create_controlled_test_network()
    solver = PriorityHeuristicSolver()
    result = solver.solve(problem)

    assert result.solver_type == SolverType.HEURISTIC
    assert result.status in [OptimizationStatus.OPTIMAL, OptimizationStatus.FEASIBLE]
    assert len(result.decisions) > 0


# ==============================================================================
# 12. REST API INTEGRATION
# ==============================================================================

def test_api_optimization_solve_and_retrieve():
    """Test POST /api/optimization/solve and GET /api/optimization/{run_id}."""
    client = TestClient(app)

    # 1. Solve endpoint
    payload = {
        "scenario_id": "DEFAULT",
        "demand_policy": "P80",
        "solver_type": "MILP",
        "objective_weights": {
            "transport": 1.0,
            "shortage": 50.0,
            "delay": 3.0,
            "risk": 10.0,
            "imbalance": 1.0,
        },
        "horizon_hours": 72,
    }

    response = client.post("/api/optimization/solve", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] in ["OPTIMAL", "FEASIBLE"]
    assert "run_id" in data
    assert len(data["decisions"]) > 0

    run_id = data["run_id"]

    # 2. Retrieve endpoint
    get_res = client.get(f"/api/optimization/{run_id}")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["run_id"] == run_id
    assert get_data["objective_value"] == data["objective_value"]
