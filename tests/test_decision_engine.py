"""Comprehensive Test Suite for PRAVAH Phase 3C Decision Engine and Recommendations."""

from __future__ import annotations
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from simulation.world_generator import WorldGenerator, RouteStatus, VehicleStatus, NodeType
from simulation.disruption_engine import DisruptionEngine, Disruption
from optimization.types import MovementDecision, OptimizationResult, OptimizationStatus, DemandPolicy, SolverType
from optimization.evaluation_metrics import (
    PlanEvaluationResult,
    EvaluationStatus,
    SimulationRunMetrics,
    MetricDelta,
    MetricDirection,
)
from backend.app.decision.schemas import (
    ActionType,
    RecommendationStatus,
    ConfidenceLevel,
    DataQualityState,
    RecommendationGenerateRequest,
)
from backend.app.decision.engine import DecisionEngine
from backend.app.decision.evidence import EvidenceBuilder
from backend.app.decision.tradeoffs import TradeoffAnalyzer
from backend.app.decision.confidence import ConfidenceScorer
from backend.app.decision.explanations import ExplanationGenerator
from backend.app.decision.service import DecisionService


@pytest.fixture
def mock_world():
    return WorldGenerator(seed=42).generate_world()


@pytest.fixture
def sample_decision():
    return MovementDecision(
        decision_id="DEC_TEST_01",
        source_node_id="NODE_CD_01",
        destination_node_id="NODE_FP_01",
        item="FUEL",
        quantity=500.0,
        route_id="ROUTE_R_01",
        vehicle_id="VEH_HT_01",
        dispatch_hour=0,
        estimated_arrival_hour=4,
    )


@pytest.fixture
def sample_opt_result(sample_decision):
    return OptimizationResult(
        run_id="RUN_TEST_01",
        status=OptimizationStatus.OPTIMAL,
        solver_type=SolverType.MILP,
        objective_value=1200.0,
        execution_time_ms=5.0,
        demand_policy=DemandPolicy.P80,
        total_transport_cost=200.0,
        total_shortage=0.0,
        total_delay=0.0,
        total_risk_cost=1000.0,
        decisions=[sample_decision],
    )


@pytest.fixture
def sample_eval_result():
    base_metrics = SimulationRunMetrics(
        total_requested_demand=10000.0,
        total_fulfilled_demand=8000.0,
        total_unmet_demand=2000.0,
        fulfillment_rate_percent=80.0,
        total_stockout_events=15,
        stockout_duration_hours=15,
        nodes_affected_stockout=2,
        items_affected_stockout=1,
        safety_stock_breaches=15,
        safety_stock_breach_hours=15,
        initial_inventory_total=100000.0,
        final_inventory_total=90000.0,
        minimum_inventory_total=90000.0,
        average_inventory_total=95000.0,
        total_transport_distance_km=200.0,
        total_transit_hours=10.0,
        average_delay_hours=0.0,
        maximum_delay_hours=0.0,
        vehicle_utilization_rate=0.2,
        active_fleet_count=12,
        critical_node_metrics={},
    )
    opt_metrics = SimulationRunMetrics(
        total_requested_demand=10000.0,
        total_fulfilled_demand=9500.0,
        total_unmet_demand=500.0,
        fulfillment_rate_percent=95.0,
        total_stockout_events=3,
        stockout_duration_hours=3,
        nodes_affected_stockout=1,
        items_affected_stockout=1,
        safety_stock_breaches=3,
        safety_stock_breach_hours=3,
        initial_inventory_total=100000.0,
        final_inventory_total=89500.0,
        minimum_inventory_total=89500.0,
        average_inventory_total=94000.0,
        total_transport_distance_km=450.0,
        total_transit_hours=20.0,
        average_delay_hours=0.5,
        maximum_delay_hours=1.0,
        vehicle_utilization_rate=0.4,
        active_fleet_count=12,
        critical_node_metrics={},
    )
    deltas = {
        "unmet_demand": MetricDelta(
            metric_name="unmet_demand",
            baseline=2000.0,
            optimized=500.0,
            absolute_delta=-1500.0,
            relative_delta_percent=-75.0,
            direction=MetricDirection.IMPROVED,
            is_better=True,
        ),
        "stockout_events": MetricDelta(
            metric_name="stockout_events",
            baseline=15.0,
            optimized=3.0,
            absolute_delta=-12.0,
            relative_delta_percent=-80.0,
            direction=MetricDirection.IMPROVED,
            is_better=True,
        ),
        "transport_distance_km": MetricDelta(
            metric_name="transport_distance_km",
            baseline=200.0,
            optimized=450.0,
            absolute_delta=250.0,
            relative_delta_percent=125.0,
            direction=MetricDirection.DEGRADED,
            is_better=False,
        ),
    }
    return PlanEvaluationResult(
        evaluation_id="EVAL_TEST_01",
        optimization_run_id="RUN_TEST_01",
        scenario_id="DEFAULT",
        status=EvaluationStatus.MIXED,
        horizon_hours=72,
        seed=42,
        initial_state_hash="dummy_hash",
        baseline=base_metrics,
        optimized=opt_metrics,
        deltas=deltas,
        tradeoffs={"SERVICE": "IMPROVED", "TRANSPORT_COST": "INCREASED"},
        critical_nodes=[],
        shipment_trace=[],
        plan_validation_status="PLAN_FEASIBLE",
        plan_validation_violations=[],
        created_at="2026-10-02T12:00:00Z",
    )


# ==============================================================================
# 1. ACTION TYPE TESTS
# ==============================================================================

def test_recommendation_generation(mock_world, sample_opt_result, sample_eval_result):
    """Verify engine produces structured recommendations from valid pipeline outputs."""
    engine = DecisionEngine()
    recs = engine.generate_recommendations(
        world=mock_world,
        optimization_result=sample_opt_result,
        evaluation_result=sample_eval_result,
    )
    assert len(recs) > 0
    rec = recs[0]
    assert rec.recommendation_id.startswith("REC_")
    assert rec.item == "FUEL"
    assert rec.quantity == 500.0
    assert rec.status in [RecommendationStatus.VERIFIED.value, RecommendationStatus.MIXED.value]


def test_move_recommendation(mock_world, sample_opt_result, sample_eval_result):
    """Verify regular replenishment creates a MOVE or PRIORITIZE action."""
    engine = DecisionEngine()
    recs = engine.generate_recommendations(
        world=mock_world,
        optimization_result=sample_opt_result,
        evaluation_result=sample_eval_result,
    )
    assert recs[0].action_type in [ActionType.MOVE.value, ActionType.PRIORITIZE.value]


def test_reroute_recommendation(mock_world, sample_opt_result):
    """When parallel corridor is blocked, action is classified as REROUTE."""
    # Find parallel route to destination and block it
    mock_world.routes["ROUTE_R_03"].status = RouteStatus.BLOCKED
    engine = DecisionEngine()

    decision = MovementDecision(
        decision_id="DEC_REROUTE",
        source_node_id="NODE_CD_01",
        destination_node_id="NODE_RH_01",
        item="FUEL",
        quantity=300.0,
        route_id="ROUTE_R_01",  # Open route
        vehicle_id="VEH_HT_01",
        dispatch_hour=0,
        estimated_arrival_hour=4,
    )
    opt_res = OptimizationResult(
        run_id="OPT_REROUTE",
        status=OptimizationStatus.OPTIMAL,
        solver_type=SolverType.MILP,
        objective_value=100.0,
        execution_time_ms=1.0,
        demand_policy=DemandPolicy.P80,
        total_transport_cost=50.0,
        total_shortage=0.0,
        total_delay=0.0,
        total_risk_cost=0.0,
        decisions=[decision],
    )

    recs = engine.generate_recommendations(world=mock_world, optimization_result=opt_res)
    assert any(r.action_type == ActionType.REROUTE.value for r in recs)


def test_reallocate_recommendation(mock_world):
    """Supply moved from an intermediate regional hub to high priority post is marked REALLOCATE."""
    engine = DecisionEngine()
    decision = MovementDecision(
        decision_id="DEC_REALLOC",
        source_node_id="NODE_RH_01",  # Regional Hub
        destination_node_id="NODE_FP_01",  # Forward Post
        item="FUEL",
        quantity=200.0,
        route_id="ROUTE_R_03",
        vehicle_id="VEH_HT_01",
        dispatch_hour=0,
        estimated_arrival_hour=3,
    )
    opt_res = OptimizationResult(
        run_id="OPT_REALLOC",
        status=OptimizationStatus.OPTIMAL,
        solver_type=SolverType.MILP,
        objective_value=50.0,
        execution_time_ms=1.0,
        demand_policy=DemandPolicy.P80,
        total_transport_cost=20.0,
        total_shortage=0.0,
        total_delay=0.0,
        total_risk_cost=0.0,
        decisions=[decision],
    )
    recs = engine.generate_recommendations(world=mock_world, optimization_result=opt_res)
    assert any(r.action_type == ActionType.REALLOCATE.value for r in recs)


def test_hold_recommendation(mock_world):
    """When no feasible moves exist and risk is elevated, HOLD is recommended."""
    engine = DecisionEngine()
    risk_assessments = {
        "NODE_FP_01": type("MockRisk", (), {"overall_risk": 0.65})()
    }
    # Empty decisions
    opt_empty = OptimizationResult(
        run_id="OPT_EMPTY",
        status=OptimizationStatus.INFEASIBLE,
        solver_type=SolverType.MILP,
        objective_value=float("inf"),
        execution_time_ms=1.0,
        demand_policy=DemandPolicy.P80,
        total_transport_cost=0.0,
        total_shortage=1000.0,
        total_delay=0.0,
        total_risk_cost=0.0,
        decisions=[],
    )
    recs = engine.generate_recommendations(
        world=mock_world,
        optimization_result=opt_empty,
        risk_assessments=risk_assessments,
    )
    assert any(r.action_type == ActionType.HOLD.value for r in recs)


def test_defer_recommendation(mock_world):
    """Simulated vehicle conflict triggers DEFER/REJECTED diagnostic state."""
    engine = DecisionEngine()
    d1 = MovementDecision("D1", "NODE_CD_01", "NODE_RH_01", "FUEL", 200.0, "ROUTE_R_01", "VEH_HT_01", 0, 3)
    d2 = MovementDecision("D2", "NODE_CD_01", "NODE_RH_02", "FUEL", 200.0, "ROUTE_R_02", "VEH_HT_01", 0, 3)

    opt_res = OptimizationResult(
        run_id="OPT_CONF",
        status=OptimizationStatus.OPTIMAL,
        solver_type=SolverType.MILP,
        objective_value=100.0,
        execution_time_ms=1.0,
        demand_policy=DemandPolicy.P80,
        total_transport_cost=50.0,
        total_shortage=0.0,
        total_delay=0.0,
        total_risk_cost=0.0,
        decisions=[d1, d2],
    )
    recs = engine.generate_recommendations(world=mock_world, optimization_result=opt_res)
    assert any(r.conflict_detected for r in recs)


# ==============================================================================
# 2. EVIDENCE & EXPLANATION TESTS
# ==============================================================================

def test_evidence_traceability(mock_world, sample_opt_result):
    """Every recommendation maps directly to verifiable system fields."""
    engine = DecisionEngine()
    recs = engine.generate_recommendations(world=mock_world, optimization_result=sample_opt_result)
    rec = recs[0]
    types = [e.type for e in rec.evidence]
    assert "STOCKOUT_PROBABILITY" in types
    assert "TIME_TO_ZERO" in types
    assert "ROUTE_STATUS" in types
    assert "SOURCE_INVENTORY" in types
    assert "VEHICLE_CAPACITY" in types


def test_explanation_is_fact_grounded(mock_world, sample_opt_result):
    """Explanations contain actual route codes, quantities, and node names."""
    engine = DecisionEngine()
    recs = engine.generate_recommendations(world=mock_world, optimization_result=sample_opt_result)
    rec = recs[0]
    assert "Why:" in rec.reason
    assert "FUEL" in rec.reason
    assert "R-01" in rec.reason or "corridor" in rec.reason


def test_verified_vs_expected_effect(mock_world, sample_opt_result, sample_eval_result):
    """Expected effect and verified effect are kept cleanly separate."""
    engine = DecisionEngine()
    recs = engine.generate_recommendations(
        world=mock_world,
        optimization_result=sample_opt_result,
        evaluation_result=sample_eval_result,
    )
    rec = recs[0]
    assert "Projected to fulfill" in rec.expected_effect
    assert "Counterfactual simulation verified" in rec.verified_effect
    assert "-1500.0" in rec.verified_effect


def test_tradeoff_generation():
    """TradeoffAnalyzer produces multidimensional tradeoff structure."""
    tradeoffs = TradeoffAnalyzer.analyze_tradeoffs(quantity=500.0, distance_km=120.0)
    assert "SERVICE" in tradeoffs
    assert "RISK" in tradeoffs
    assert "TRANSPORT_COST" in tradeoffs
    assert "NET_RESULT" in tradeoffs


def test_confidence_data_quality():
    """Confidence responds quantitatively to sensor data quality gates."""
    # READY telemetry
    conf_ready, _ = ConfidenceScorer.evaluate_confidence(
        data_quality="READY",
        has_sufficient_source_inventory=True,
        is_route_open=True,
        is_vehicle_available=True,
        counterfactual_verified=True,
    )
    assert conf_ready.level == ConfidenceLevel.HIGH.value

    # DEGRADED telemetry caps confidence
    conf_deg, _ = ConfidenceScorer.evaluate_confidence(
        data_quality="DEGRADED",
        has_sufficient_source_inventory=True,
        is_route_open=True,
        is_vehicle_available=True,
        counterfactual_verified=True,
    )
    assert conf_deg.level in [ConfidenceLevel.MEDIUM.value, ConfidenceLevel.LOW.value]


def test_insufficient_data_handling():
    """INSUFFICIENT data quality forces LOW confidence and INCONCLUSIVE status."""
    conf, status_override = ConfidenceScorer.evaluate_confidence(
        data_quality="INSUFFICIENT",
        has_sufficient_source_inventory=True,
        is_route_open=True,
        is_vehicle_available=True,
        counterfactual_verified=True,
    )
    assert conf.level == ConfidenceLevel.LOW.value
    assert status_override == RecommendationStatus.INCONCLUSIVE.value


# ==============================================================================
# 3. CONFLICT DETECTION TESTS
# ==============================================================================

def test_vehicle_conflict(mock_world):
    """Simultaneous dispatches on the same vehicle trigger conflict."""
    engine = DecisionEngine()
    d1 = MovementDecision("D1", "NODE_CD_01", "NODE_RH_01", "FUEL", 100.0, "ROUTE_R_01", "VEH_HT_01", 0, 3)
    d2 = MovementDecision("D2", "NODE_CD_01", "NODE_RH_02", "FUEL", 100.0, "ROUTE_R_02", "VEH_HT_01", 0, 3)
    opt_res = OptimizationResult(
        run_id="OPT_CONF",
        status=OptimizationStatus.OPTIMAL,
        solver_type=SolverType.MILP,
        objective_value=10.0,
        execution_time_ms=1.0,
        demand_policy=DemandPolicy.P80,
        total_transport_cost=5.0,
        total_shortage=0.0,
        total_delay=0.0,
        total_risk_cost=0.0,
        decisions=[d1, d2],
    )
    recs = engine.generate_recommendations(world=mock_world, optimization_result=opt_res)
    conflicting_rec = next((r for r in recs if r.conflict_detected), None)
    assert conflicting_rec is not None
    assert any("Vehicle conflict" in c for c in conflicting_rec.conflict_details)


def test_route_conflict(mock_world):
    """Aggregate volume exceeding route capacity triggers conflict."""
    engine = DecisionEngine()
    mock_world.routes["ROUTE_R_01"].max_capacity = 1000.0
    mock_world.vehicles["VEH_HT_01"].capacity = 50000.0
    d = MovementDecision("D1", "NODE_CD_01", "NODE_RH_01", "FUEL", 2500.0, "ROUTE_R_01", "VEH_HT_01", 0, 3)
    opt_res = OptimizationResult(
        run_id="OPT_ROUTE_CONF",
        status=OptimizationStatus.OPTIMAL,
        solver_type=SolverType.MILP,
        objective_value=10.0,
        execution_time_ms=1.0,
        demand_policy=DemandPolicy.P80,
        total_transport_cost=5.0,
        total_shortage=0.0,
        total_delay=0.0,
        total_risk_cost=0.0,
        decisions=[d],
    )
    recs = engine.generate_recommendations(world=mock_world, optimization_result=opt_res)
    assert recs[0].conflict_detected
    assert any("exceeds capacity" in c for c in recs[0].conflict_details)


def test_inventory_conflict(mock_world):
    """Aggregate dispatches exceeding depot stock trigger inventory conflict."""
    engine = DecisionEngine()
    # Deplete depot stock in mock world
    mock_world.nodes["NODE_CD_01"].initial_inventory["FUEL"] = 100.0
    d = MovementDecision("D1", "NODE_CD_01", "NODE_RH_01", "FUEL", 500.0, "ROUTE_R_01", "VEH_HT_01", 0, 3)
    opt_res = OptimizationResult(
        run_id="OPT_INV_CONF",
        status=OptimizationStatus.OPTIMAL,
        solver_type=SolverType.MILP,
        objective_value=10.0,
        execution_time_ms=1.0,
        demand_policy=DemandPolicy.P80,
        total_transport_cost=5.0,
        total_shortage=0.0,
        total_delay=0.0,
        total_risk_cost=0.0,
        decisions=[d],
    )
    recs = engine.generate_recommendations(world=mock_world, optimization_result=opt_res)
    assert recs[0].conflict_detected
    assert any("exceed stock" in c for c in recs[0].conflict_details)


def test_time_conflict(mock_world, sample_opt_result):
    """Validation states ensure departure and arrival hours are physically non-negative."""
    engine = DecisionEngine()
    recs = engine.generate_recommendations(world=mock_world, optimization_result=sample_opt_result)
    for r in recs:
        assert r.planned_departure >= 0
        assert r.expected_arrival >= r.planned_departure


# ==============================================================================
# 4. AUDIT TRAIL & DETERMINISM TESTS
# ==============================================================================

def test_recommendation_validation(mock_world, sample_opt_result, sample_eval_result):
    """Every recommendation carries comprehensive validation states."""
    engine = DecisionEngine()
    recs = engine.generate_recommendations(
        world=mock_world,
        optimization_result=sample_opt_result,
        evaluation_result=sample_eval_result,
    )
    for r in recs:
        assert "source_inventory" in r.validation_state
        assert "route" in r.validation_state
        assert "vehicle" in r.validation_state
        assert "optimization" in r.validation_state
        assert "counterfactual" in r.validation_state


def test_recommendation_audit_trail(mock_world, sample_opt_result, sample_eval_result):
    """Recommendations link to optimization_run_id, evaluation_id, and forecast version."""
    engine = DecisionEngine()
    recs = engine.generate_recommendations(
        world=mock_world,
        optimization_result=sample_opt_result,
        evaluation_result=sample_eval_result,
    )
    rec = recs[0]
    assert rec.audit_trail["optimization_run_id"] == "RUN_TEST_01"
    assert rec.audit_trail["evaluation_id"] == "EVAL_TEST_01"
    assert "forecast_version" in rec.audit_trail
    assert "risk_version" in rec.audit_trail


def test_deterministic_recommendations(mock_world, sample_opt_result, sample_eval_result):
    """Running recommendation generation twice yields identical outputs."""
    engine = DecisionEngine()
    r1 = engine.generate_recommendations(mock_world, sample_opt_result, sample_eval_result)
    r2 = engine.generate_recommendations(mock_world, sample_opt_result, sample_eval_result)
    assert len(r1) == len(r2)
    assert r1[0].title == r2[0].title
    assert r1[0].status == r2[0].status
    assert r1[0].priority == r2[0].priority


# ==============================================================================
# 5. REST API TESTS
# ==============================================================================

def test_recommendation_api():
    """Test POST /api/recommendations/generate and GET /api/recommendations."""
    client = TestClient(app)

    # 1. Generate recommendations
    gen_res = client.post("/api/recommendations/generate", json={
        "scenario_id": "DEFAULT",
        "demand_policy": "P80",
        "data_quality_state": "READY",
        "horizon_hours": 48,
        "seed": 42,
    })
    assert gen_res.status_code == 200
    data = gen_res.json()
    assert "recommendations" in data
    assert data["total_recommendations"] > 0

    first_rec = data["recommendations"][0]
    rec_id = first_rec["recommendation_id"]

    # 2. Get single recommendation
    single_res = client.get(f"/api/recommendations/{rec_id}")
    assert single_res.status_code == 200
    assert single_res.json()["recommendation_id"] == rec_id

    # 3. List with filter
    filter_res = client.get(f"/api/recommendations?scenario_id=DEFAULT")
    assert filter_res.status_code == 200
    assert len(filter_res.json()["recommendations"]) > 0


def test_decision_summary_api():
    """Test GET /api/decision/summary endpoint for command-center readiness."""
    client = TestClient(app)
    sum_res = client.get("/api/decision/summary")
    assert sum_res.status_code == 200
    sum_data = sum_res.json()
    assert sum_data["readiness"] == "OPERATIONAL"
    assert "critical_nodes" in sum_data
    assert "top_recommendations" in sum_data
    assert "overall_tradeoffs" in sum_data


# ==============================================================================
# 6. CRITICAL NEGATIVE & RESPONSIVENESS TESTS
# ==============================================================================

def test_critical_negative_no_supply(mock_world):
    """When source inventory is 0, no executable MOVE recommendation is issued."""
    engine = DecisionEngine()
    mock_world.nodes["NODE_CD_01"].initial_inventory["FUEL"] = 0.0
    d = MovementDecision("D1", "NODE_CD_01", "NODE_RH_01", "FUEL", 200.0, "ROUTE_R_01", "VEH_HT_01", 0, 3)
    opt_res = OptimizationResult(
        run_id="OPT_NO_SUP",
        status=OptimizationStatus.OPTIMAL,
        solver_type=SolverType.MILP,
        objective_value=10.0,
        execution_time_ms=1.0,
        demand_policy=DemandPolicy.P80,
        total_transport_cost=5.0,
        total_shortage=0.0,
        total_delay=0.0,
        total_risk_cost=0.0,
        decisions=[d],
    )
    recs = engine.generate_recommendations(world=mock_world, optimization_result=opt_res)
    assert recs[0].status == RecommendationStatus.REJECTED.value
    assert recs[0].validation_state["source_inventory"] == "FAIL"


def test_critical_negative_blocked_route(mock_world):
    """When assigned route is BLOCKED, recommendation is REJECTED with route BLOCKED state."""
    engine = DecisionEngine()
    mock_world.routes["ROUTE_R_01"].status = RouteStatus.BLOCKED
    d = MovementDecision("D1", "NODE_CD_01", "NODE_RH_01", "FUEL", 200.0, "ROUTE_R_01", "VEH_HT_01", 0, 3)
    opt_res = OptimizationResult(
        run_id="OPT_BLK",
        status=OptimizationStatus.OPTIMAL,
        solver_type=SolverType.MILP,
        objective_value=10.0,
        execution_time_ms=1.0,
        demand_policy=DemandPolicy.P80,
        total_transport_cost=5.0,
        total_shortage=0.0,
        total_delay=0.0,
        total_risk_cost=0.0,
        decisions=[d],
    )
    recs = engine.generate_recommendations(world=mock_world, optimization_result=opt_res)
    assert recs[0].status == RecommendationStatus.REJECTED.value
    assert recs[0].validation_state["route"] == "BLOCKED"


def test_critical_negative_counterfactual_degradation(mock_world, sample_opt_result):
    """If counterfactual simulation shows degradation, recommendation cannot be marked VERIFIED."""
    engine = DecisionEngine()
    degraded_eval = PlanEvaluationResult(
        evaluation_id="EVAL_DEG",
        optimization_run_id="RUN_DEG",
        scenario_id="DEFAULT",
        status=EvaluationStatus.DEGRADED,
        horizon_hours=72,
        seed=42,
        initial_state_hash="dummy",
        baseline=SimulationRunMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, {}),
        optimized=SimulationRunMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, {}),
        deltas={
            "unmet_demand": MetricDelta("unmet_demand", 100.0, 300.0, 200.0, 200.0, MetricDirection.DEGRADED, False),
        },
        tradeoffs={"SERVICE": "DEGRADED"},
        critical_nodes=[],
        shipment_trace=[],
        plan_validation_status="PLAN_FEASIBLE",
        plan_validation_violations=[],
        created_at="2026-10-02T12:00:00Z",
    )
    recs = engine.generate_recommendations(
        world=mock_world,
        optimization_result=sample_opt_result,
        evaluation_result=degraded_eval,
    )
    assert recs[0].status == RecommendationStatus.REJECTED.value
    assert recs[0].status != RecommendationStatus.VERIFIED.value


def test_recommendation_quality_scenario_responsiveness(mock_world):
    """Engine dynamically alters recommendation when network conditions change."""
    engine = DecisionEngine()
    d = MovementDecision("D1", "NODE_CD_01", "NODE_RH_01", "FUEL", 200.0, "ROUTE_R_01", "VEH_HT_01", 0, 3)
    opt_res = OptimizationResult(
        run_id="OPT_R",
        status=OptimizationStatus.OPTIMAL,
        solver_type=SolverType.MILP,
        objective_value=10.0,
        execution_time_ms=1.0,
        demand_policy=DemandPolicy.P80,
        total_transport_cost=5.0,
        total_shortage=0.0,
        total_delay=0.0,
        total_risk_cost=0.0,
        decisions=[d],
    )

    # 1. Open alternative route
    recs1 = engine.generate_recommendations(world=mock_world, optimization_result=opt_res)
    assert recs1[0].action_type in [ActionType.MOVE.value, ActionType.PRIORITIZE.value]

    # 2. Block alternative route R-03 -> shifts to REROUTE
    mock_world.routes["ROUTE_R_03"].status = RouteStatus.BLOCKED
    recs2 = engine.generate_recommendations(world=mock_world, optimization_result=opt_res)
    assert recs2[0].action_type == ActionType.REROUTE.value

