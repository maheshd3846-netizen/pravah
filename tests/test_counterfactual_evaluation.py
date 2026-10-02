"""Comprehensive Test Suite for Counterfactual Plan Evaluation & Closed-Loop Validation."""

import pytest
from fastapi.testclient import TestClient

from simulation.world_generator import WorldGenerator, RouteStatus, VehicleStatus
from simulation.simulator import Simulator, SimulationConfig
from simulation.state_snapshot import StateSnapshot
from optimization.types import MovementDecision, DemandPolicy, SolverType
from optimization.evaluator import PlanEvaluator
from optimization.plan_adapter import OptimizationPlanAdapter
from optimization.evaluation_metrics import EvaluationStatus, MetricDirection
from optimization.solver import LogisticsSolver
from optimization.adapters import OptimizationInputAdapter
from backend.main import app


# ==============================================================================
# 1. STATE SNAPSHOT & INITIAL STATE INTEGRITY TESTS
# ==============================================================================

def test_state_snapshot_integrity():
    """Verify StateSnapshot capture, hash, clone, and restore determinism."""
    cfg = SimulationConfig(seed=42, horizon_hours=72, scenario_name="NORMAL")
    sim = Simulator(config=cfg)

    snap1 = StateSnapshot.capture(sim)
    hash1 = snap1.hash()

    # Clone snapshot
    snap2 = snap1.clone()
    hash2 = snap2.hash()

    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 length


def test_baseline_and_intervention_same_initial_state():
    """Verify baseline and intervention start from bitwise identical state hash."""
    cfg = SimulationConfig(seed=42, horizon_hours=72, scenario_name="COMPOUND_DISRUPTION")
    sim1 = Simulator(config=cfg)
    snap1 = StateSnapshot.capture(sim1)

    sim2 = Simulator(config=cfg)
    snap1.restore_into(sim2)
    snap2 = StateSnapshot.capture(sim2)

    assert snap1.hash() == snap2.hash()


# ==============================================================================
# 2. INTEGRITY & CONTROL EXPERIMENTS
# ==============================================================================

def test_empty_plan_produces_zero_delta():
    """An empty optimization plan must produce baseline == intervention (all deltas = 0)."""
    evaluator = PlanEvaluator()
    cfg = SimulationConfig(seed=42, horizon_hours=48, scenario_name="NORMAL", auto_replenish=True)

    result = evaluator.evaluate_plan(
        plan_or_result=[],
        base_config=cfg,
        horizon_hours=48,
        seed=42,
    )

    assert result.status == EvaluationStatus.INCONCLUSIVE
    assert result.deltas["unmet_demand"].absolute_delta == 0.0
    assert result.deltas["stockout_events"].absolute_delta == 0.0
    assert result.deltas["fulfillment_rate_percent"].absolute_delta == 0.0


def test_positive_control_intervention():
    """Positive Control: Pre-positioning supply to an under-stocked post must improve fulfillment."""
    evaluator = PlanEvaluator()
    cfg = SimulationConfig(seed=42, horizon_hours=48, scenario_name="NORMAL", auto_replenish=False)

    sim_init = Simulator(cfg)
    sim_init.inventory_engine.current_inventory["NODE_RH_01"]["FUEL"] = 0.0
    initial_snap = StateSnapshot.capture(sim_init)

    # Known intervention: Dispatch 2000 units of FUEL from Central Depot to Regional Hub 1
    decision = MovementDecision(
        decision_id="POS_CTRL_01",
        source_node_id="NODE_CD_01",
        destination_node_id="NODE_RH_01",
        item="FUEL",
        quantity=2000.0,
        route_id="ROUTE_R_01",
        vehicle_id="VEH_HT_01",
        dispatch_hour=0,
        estimated_arrival_hour=3,
        priority=5,
    )

    eval_result = evaluator.evaluate_plan(
        plan_or_result=[decision],
        base_config=cfg,
        horizon_hours=48,
        seed=42,
        initial_state=initial_snap,
    )

    assert eval_result.plan_validation_status == "PLAN_FEASIBLE"
    assert eval_result.status in [EvaluationStatus.IMPROVED, EvaluationStatus.MIXED]
    assert eval_result.deltas["unmet_demand"].is_better
    assert len(eval_result.shipment_trace) == 1
    assert eval_result.shipment_trace[0].status == "DELIVERED"


def test_negative_control_no_supply():
    """Negative Control: When source inventory is exhausted, planned dispatches cannot execute."""
    evaluator = PlanEvaluator()
    cfg = SimulationConfig(seed=42, horizon_hours=48, scenario_name="NORMAL", auto_replenish=False)

    # Plan with 50,000 units exceeding all possible depot supply
    excessive_decision = MovementDecision(
        decision_id="NEG_CTRL_01",
        source_node_id="NODE_CD_01",
        destination_node_id="NODE_RH_01",
        item="FUEL",
        quantity=999999.0,
        route_id="ROUTE_R_01",
        vehicle_id="VEH_HT_01",
        dispatch_hour=0,
        estimated_arrival_hour=3,
    )

    eval_result = evaluator.evaluate_plan(
        plan_or_result=[excessive_decision],
        base_config=cfg,
        horizon_hours=48,
        seed=42,
    )

    # Must be caught by pre-simulation validation as INVALID
    assert eval_result.status == EvaluationStatus.INVALID
    assert eval_result.plan_validation_status == "PLAN_INVALID"
    assert any("lacks sufficient" in v for v in eval_result.plan_validation_violations)


# ==============================================================================
# 3. PLAN VALIDATION & INFEASIBILITY TESTS
# ==============================================================================

def test_blocked_route_intervention():
    """Planning shipment across a BLOCKED route fails validation."""
    world = WorldGenerator(seed=42).generate_world()
    world.routes["ROUTE_R_01"].status = RouteStatus.BLOCKED

    decision = MovementDecision(
        decision_id="BLOCKED_TEST",
        source_node_id="NODE_CD_01",
        destination_node_id="NODE_RH_01",
        item="FUEL",
        quantity=50.0,
        route_id="ROUTE_R_01",
        vehicle_id="VEH_HT_01",
        dispatch_hour=0,
        estimated_arrival_hour=3,
    )

    inv_data = {
        nid: n.initial_inventory for nid, n in world.nodes.items()
    }
    validation = OptimizationPlanAdapter.validate_plan(
        [decision], inv_data, world.routes, world.vehicles
    )

    assert not validation.is_feasible
    assert any("BLOCKED" in v for v in validation.violations)


def test_vehicle_capacity_intervention():
    """Planning shipment exceeding vehicle payload fails validation."""
    world = WorldGenerator(seed=42).generate_world()

    decision = MovementDecision(
        decision_id="CAP_TEST",
        source_node_id="NODE_CD_01",
        destination_node_id="NODE_RH_01",
        item="FUEL",
        quantity=25000.0,  # Max heavy truck capacity is 12000.0
        route_id="ROUTE_R_01",
        vehicle_id="VEH_HT_01",
        dispatch_hour=0,
        estimated_arrival_hour=3,
    )

    inv_data = {
        nid: n.initial_inventory for nid, n in world.nodes.items()
    }
    validation = OptimizationPlanAdapter.validate_plan(
        [decision], inv_data, world.routes, world.vehicles
    )

    assert not validation.is_feasible
    assert any("Vehicle" in v and "capacity exceeded" in v for v in validation.violations)


# ==============================================================================
# 4. COUNTERFACTUAL DELTA & TRADEOFF TESTS
# ==============================================================================

def test_stockout_and_unmet_demand_deltas():
    """Verify delta calculation correctly reports values, percentage, and direction."""
    evaluator = PlanEvaluator()

    delta_unmet = evaluator._compute_delta(
        "unmet_demand", base_val=1000.0, opt_val=600.0, lower_is_better=True
    )
    assert delta_unmet.absolute_delta == -400.0
    assert delta_unmet.relative_delta_percent == -40.0
    assert delta_unmet.direction == MetricDirection.IMPROVED
    assert delta_unmet.is_better

    delta_dist = evaluator._compute_delta(
        "transport_distance", base_val=500.0, opt_val=800.0, lower_is_better=True
    )
    assert delta_dist.absolute_delta == 300.0
    assert delta_dist.direction == MetricDirection.DEGRADED
    assert not delta_dist.is_better


def test_stockout_delta():
    """Verify stockout events delta calculation."""
    evaluator = PlanEvaluator()
    delta = evaluator._compute_delta("stockout_events", base_val=10.0, opt_val=4.0, lower_is_better=True)
    assert delta.absolute_delta == -6.0
    assert delta.direction == MetricDirection.IMPROVED
    assert delta.is_better


def test_unmet_demand_delta():
    """Verify unmet demand delta calculation."""
    evaluator = PlanEvaluator()
    delta = evaluator._compute_delta("unmet_demand", base_val=500.0, opt_val=0.0, lower_is_better=True)
    assert delta.absolute_delta == -500.0
    assert delta.relative_delta_percent == -100.0
    assert delta.direction == MetricDirection.IMPROVED
    assert delta.is_better


def test_fulfillment_delta():
    """Verify fulfillment percentage delta (higher is better)."""
    evaluator = PlanEvaluator()
    delta = evaluator._compute_delta("fulfillment_rate_percent", base_val=80.0, opt_val=98.5, lower_is_better=False)
    assert delta.absolute_delta == 18.5
    assert delta.direction == MetricDirection.IMPROVED
    assert delta.is_better


def test_time_to_zero_delta():
    """Verify critical node survival extension calculation."""
    evaluator = PlanEvaluator()
    cfg = SimulationConfig(seed=42, horizon_hours=48, scenario_name="NORMAL", auto_replenish=False)
    result = evaluator.evaluate_plan([], base_config=cfg, horizon_hours=48, seed=42)
    assert isinstance(result.critical_nodes, list)
    for cn in result.critical_nodes:
        assert "survival_hours_difference" in cn
        assert "stockout_prevented" in cn


def test_safety_stock_delta():
    """Verify safety stock breach tracking."""
    evaluator = PlanEvaluator()
    delta = evaluator._compute_delta("safety_stock_breaches", base_val=5.0, opt_val=1.0, lower_is_better=True)
    assert delta.absolute_delta == -4.0
    assert delta.is_better


def test_risk_delta():
    """Verify risk mitigation tradeoff summary."""
    evaluator = PlanEvaluator()
    cfg = SimulationConfig(seed=42, horizon_hours=48, scenario_name="NORMAL", auto_replenish=True)
    result = evaluator.evaluate_plan([], base_config=cfg, horizon_hours=48, seed=42)
    assert "RISK" in result.tradeoffs


def test_delay_delta():
    """Verify average and maximum delay tracking."""
    evaluator = PlanEvaluator()
    delta = evaluator._compute_delta("average_delay_hours", base_val=3.5, opt_val=1.2, lower_is_better=True)
    assert delta.absolute_delta < 0
    assert delta.is_better


def test_shipment_arrival_trace():
    """Verify optimizer shipment movements are traced with physical arrival and delays."""
    evaluator = PlanEvaluator()
    cfg = SimulationConfig(seed=42, horizon_hours=48, scenario_name="NORMAL", auto_replenish=False)

    decision = MovementDecision(
        decision_id="TRACE_TEST_01",
        source_node_id="NODE_CD_01",
        destination_node_id="NODE_RH_01",
        item="FUEL",
        quantity=500.0,
        route_id="ROUTE_R_01",
        vehicle_id="VEH_HT_01",
        dispatch_hour=0,
        estimated_arrival_hour=3,
    )
    result = evaluator.evaluate_plan([decision], base_config=cfg, horizon_hours=48, seed=42)
    assert len(result.shipment_trace) == 1
    trace = result.shipment_trace[0]
    assert trace.decision_id == "TRACE_TEST_01"
    assert trace.actual_dispatched_quantity == 500.0
    assert trace.arrival_hour >= trace.departure_hour
    assert trace.status in ["DELIVERED", "IN_TRANSIT"]


def test_tradeoff_reporting():
    """Verify multidimensional tradeoff reporting."""
    evaluator = PlanEvaluator()
    cfg = SimulationConfig(seed=42, horizon_hours=48, scenario_name="NORMAL", auto_replenish=True)

    result = evaluator.evaluate_plan([], base_config=cfg, horizon_hours=48, seed=42)
    assert "SERVICE" in result.tradeoffs
    assert "RISK" in result.tradeoffs
    assert "TRANSPORT_COST" in result.tradeoffs
    assert "DELAY" in result.tradeoffs
    assert "FLEET_UTILIZATION" in result.tradeoffs


def test_invalid_plan_detection():
    """Invalid plans with non-existent routes or vehicles are rejected early."""
    evaluator = PlanEvaluator()
    decision = MovementDecision(
        decision_id="INV_01",
        source_node_id="NODE_CD_01",
        destination_node_id="NODE_RH_01",
        item="FUEL",
        quantity=100.0,
        route_id="NON_EXISTENT_ROUTE",
        vehicle_id="NON_EXISTENT_VEH",
        dispatch_hour=0,
        estimated_arrival_hour=3,
    )
    result = evaluator.evaluate_plan([decision], horizon_hours=48, seed=42)
    assert result.status == EvaluationStatus.INVALID
    assert result.plan_validation_status == "PLAN_INVALID"
    assert len(result.plan_validation_violations) > 0


# ==============================================================================
# 5. DETERMINISM & REPRODUCIBILITY TEST
# ==============================================================================

def test_deterministic_evaluation():
    """Evaluating identical plans under identical seeds yields identical results."""
    evaluator = PlanEvaluator()
    cfg = SimulationConfig(seed=42, horizon_hours=48, scenario_name="NORMAL", auto_replenish=True)

    res1 = evaluator.evaluate_plan([], base_config=cfg, horizon_hours=48, seed=42)
    res2 = evaluator.evaluate_plan([], base_config=cfg, horizon_hours=48, seed=42)

    assert res1.initial_state_hash == res2.initial_state_hash
    assert res1.baseline.total_unmet_demand == res2.baseline.total_unmet_demand
    assert res1.status == res2.status


# ==============================================================================
# 6. REST API INTEGRATION TESTS
# ==============================================================================

def test_api_evaluation():
    """Test POST /api/optimization/evaluate and GET /api/optimization/evaluations/{id}."""
    client = TestClient(app)

    # 1. First solve a plan
    solve_res = client.post("/api/optimization/solve", json={
        "scenario_id": "DEFAULT",
        "demand_policy": "P80",
        "solver_type": "MILP",
        "horizon_hours": 48,
    })
    assert solve_res.status_code == 200
    opt_run_id = solve_res.json()["run_id"]

    # 2. Evaluate the plan
    eval_req = {
        "optimization_run_id": opt_run_id,
        "scenario_id": "DEFAULT",
        "horizon_hours": 48,
        "seed": 42,
    }
    eval_res = client.post("/api/optimization/evaluate", json=eval_req)
    assert eval_res.status_code == 200
    eval_data = eval_res.json()

    assert "evaluation_id" in eval_data
    assert eval_data["status"] in ["IMPROVED", "MIXED", "INCONCLUSIVE", "DEGRADED"]
    assert "baseline" in eval_data
    assert "optimized" in eval_data
    assert "deltas" in eval_data
    assert "tradeoffs" in eval_data

    eval_id = eval_data["evaluation_id"]

    # 3. Retrieve evaluation record
    get_res = client.get(f"/api/optimization/evaluations/{eval_id}")
    assert get_res.status_code == 200
    assert get_res.json()["evaluation_id"] == eval_id
