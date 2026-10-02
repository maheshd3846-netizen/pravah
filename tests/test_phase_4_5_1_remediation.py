"""Phase 4.5.1 Remediation Tests.

Covers three audit findings:
    Fix #1  - INFEASIBLE vs OPTIMAL status when all routes are blocked
    Fix #2  - compute_estimated_arrival() edge cases; solver dispatch timing
    Fix #3  - rejection_summary in RecommendationListResponse

These tests do NOT replace or modify existing tests; they add new coverage.
"""

from __future__ import annotations
import math
import pytest
from dataclasses import dataclass
from typing import Dict

from optimization.types import (
    DemandPolicy,
    SolverType,
    OptimizationStatus,
    ObjectiveWeights,
    compute_estimated_arrival,
)
from optimization.model import OptimizationProblem
from optimization.solver import LogisticsSolver, MilpSolver
from optimization.heuristic import PriorityHeuristicSolver
from optimization.adapters import OptimizationInputAdapter
from simulation.world_generator import WorldGenerator, RouteStatus


# ==============================================================================
# HELPERS
# ==============================================================================

def _make_problem_all_blocked(seed: int = 7) -> OptimizationProblem:
    """World with all routes BLOCKED and non-zero demand."""
    world = WorldGenerator(seed=seed).generate_world()
    for r in world.routes.values():
        r.status = RouteStatus.BLOCKED
    return OptimizationInputAdapter.create_problem(
        world=world,
        risk_assessments={},
        demand_policy=DemandPolicy.P80,
        objective_weights=ObjectiveWeights(),
    )


def _make_problem_zero_demand(seed: int = 7) -> OptimizationProblem:
    """All routes BLOCKED + zero required_demand."""
    problem = _make_problem_all_blocked(seed=seed)
    problem.required_demand = {}
    return problem


def _make_problem_normal(seed: int = 42) -> OptimizationProblem:
    """Normal world with available routes and finite demand."""
    world = WorldGenerator(seed=seed).generate_world()
    return OptimizationInputAdapter.create_problem(
        world=world,
        risk_assessments={},
        demand_policy=DemandPolicy.P80,
        objective_weights=ObjectiveWeights(),
    )


# ==============================================================================
# FIX #1 - INFEASIBLE STATUS WHEN ALL ROUTES BLOCKED, POSITIVE DEMAND
# ==============================================================================

class TestInfeasibleStatusClassification:
    """Verify the LP vs application-level INFEASIBLE distinction."""

    def test_all_routes_blocked_positive_demand_is_application_infeasible(self):
        problem = _make_problem_all_blocked()
        result = MilpSolver(allow_fallback=False).solve(problem)
        assert result.status == OptimizationStatus.INFEASIBLE, (
            f"Expected INFEASIBLE (application-level), got {result.status.value}"
        )
        assert len(result.decisions) == 0
        assert result.total_shortage > 0
        assert any("NO_FEASIBLE_DISPATCH" in r for r in result.infeasibility_reasons), (
            f"infeasibility_reasons must contain NO_FEASIBLE_DISPATCH, got: {result.infeasibility_reasons}"
        )

    def test_all_routes_blocked_metadata_preserves_lp_status(self):
        problem = _make_problem_all_blocked()
        result = MilpSolver(allow_fallback=False).solve(problem)
        assert "lp_solver_status" in result.metadata, (
            "metadata must contain lp_solver_status"
        )
        assert result.metadata["lp_solver_status"] == "OPTIMAL", (
            "HiGHS internally succeeds; lp_solver_status should be OPTIMAL"
        )
        assert result.status == OptimizationStatus.INFEASIBLE

    def test_all_routes_blocked_zero_demand_is_optimal(self):
        problem = _make_problem_zero_demand()
        result = MilpSolver(allow_fallback=False).solve(problem)
        assert result.status == OptimizationStatus.OPTIMAL, (
            f"Expected OPTIMAL when demand is zero, got {result.status.value}"
        )
        assert not any("NO_FEASIBLE_DISPATCH" in r for r in result.infeasibility_reasons)

    def test_available_routes_feasible_demand_is_optimal(self):
        problem = _make_problem_normal()
        result = MilpSolver(allow_fallback=False).solve(problem)
        assert result.status == OptimizationStatus.OPTIMAL
        assert len(result.decisions) > 0

    def test_infeasibility_reason_distinguishes_from_solver_error(self):
        problem = _make_problem_all_blocked()
        result = MilpSolver(allow_fallback=False).solve(problem)
        assert result.status != OptimizationStatus.ERROR
        reason_text = " ".join(result.infeasibility_reasons)
        assert "NO_FEASIBLE_DISPATCH" in reason_text
        assert "Solver reported failure" not in reason_text

    def test_status_enum_docstring_documents_distinction(self):
        doc = OptimizationStatus.__doc__ or ""
        assert "INFEASIBLE" in doc
        assert "OPTIMAL" in doc
        assert "lp_solver_status" in doc or "LP solver" in doc


# ==============================================================================
# FIX #2 - compute_estimated_arrival() UNIT TESTS
# ==============================================================================

@dataclass
class _FakeRoute:
    base_travel_hours: float


class TestComputeEstimatedArrival:
    """Unit tests for compute_estimated_arrival() canonical utility."""

    def test_route_2h_gives_arrival_2(self):
        assert compute_estimated_arrival(_FakeRoute(2.0)) == 2

    def test_route_7h_gives_arrival_7(self):
        assert compute_estimated_arrival(_FakeRoute(7.0)) == 7

    def test_route_7_6h_rounds_to_8(self):
        assert compute_estimated_arrival(_FakeRoute(7.6)) == 8

    def test_route_7_4h_rounds_to_7(self):
        assert compute_estimated_arrival(_FakeRoute(7.4)) == 7

    def test_none_route_default_fallback(self):
        assert compute_estimated_arrival(None) == 4

    def test_none_route_custom_fallback(self):
        assert compute_estimated_arrival(None, fallback_hours=6.0) == 6

    def test_zero_hours_gives_at_least_1(self):
        result = compute_estimated_arrival(_FakeRoute(0.0))
        assert result >= 1

    def test_negative_hours_uses_fallback(self):
        result = compute_estimated_arrival(_FakeRoute(-5.0))
        assert result >= 1

    def test_nan_hours_uses_fallback(self):
        result = compute_estimated_arrival(_FakeRoute(float("nan")))
        assert math.isfinite(result)
        assert result >= 1

    def test_inf_hours_uses_fallback(self):
        result = compute_estimated_arrival(_FakeRoute(float("inf")))
        assert math.isfinite(result)
        assert result >= 1

    def test_dict_route_style(self):
        assert compute_estimated_arrival({"base_travel_hours": 5.0}) == 5

    def test_dict_missing_key_uses_fallback(self):
        assert compute_estimated_arrival({"distance_km": 100.0}) == 4

    def test_output_always_positive_int(self):
        cases = [
            _FakeRoute(2.0), _FakeRoute(7.0), _FakeRoute(7.6), _FakeRoute(0.0),
            _FakeRoute(-1.0), _FakeRoute(float("nan")), _FakeRoute(float("inf")),
            None, {"base_travel_hours": 3.0}, {},
        ]
        for case in cases:
            result = compute_estimated_arrival(case)
            assert isinstance(result, int), f"Got {type(result)} for {case}"
            assert result >= 1, f"Got {result} for {case}"
            assert math.isfinite(result), f"Got non-finite {result} for {case}"

    def test_docstring_documents_estimate_vs_simulation_distinction(self):
        doc = compute_estimated_arrival.__doc__ or ""
        assert "Optimization estimate" in doc or "optimization estimate" in doc.lower()
        assert "Simulation" in doc or "simulation" in doc.lower()


# ==============================================================================
# FIX #2 - INTEGRATION: SOLVER PRODUCES REALISTIC ARRIVAL HOURS
# ==============================================================================

class TestSolverDispatchTiming:

    def test_lp_decisions_have_arrival_geq_1(self):
        problem = _make_problem_normal()
        result = MilpSolver(allow_fallback=False).solve(problem)
        assert result.decisions
        for d in result.decisions:
            assert d.estimated_arrival_hour >= 1, (
                f"Decision {d.decision_id} has invalid arrival {d.estimated_arrival_hour}"
            )

    def test_heuristic_decisions_have_arrival_geq_1(self):
        problem = _make_problem_normal()
        result = PriorityHeuristicSolver().solve(problem)
        assert result.decisions
        for d in result.decisions:
            assert d.estimated_arrival_hour >= 1

    def test_lp_arrival_matches_route_base_travel(self):
        world = WorldGenerator(seed=42).generate_world()
        problem = OptimizationInputAdapter.create_problem(
            world=world, risk_assessments={},
            demand_policy=DemandPolicy.P80,
            objective_weights=ObjectiveWeights(),
        )
        result = MilpSolver(allow_fallback=False).solve(problem)
        assert result.decisions
        for dec in result.decisions[:5]:
            route = world.routes.get(dec.route_id)
            if route is not None:
                expected = max(1, int(round(route.base_travel_hours)))
                assert dec.estimated_arrival_hour == expected, (
                    f"Decision {dec.decision_id}: expected {expected} "
                    f"(base_travel_hours={route.base_travel_hours:.2f}), "
                    f"got {dec.estimated_arrival_hour}"
                )

    def test_heuristic_arrival_matches_route_base_travel(self):
        world = WorldGenerator(seed=42).generate_world()
        problem = OptimizationInputAdapter.create_problem(
            world=world, risk_assessments={},
            demand_policy=DemandPolicy.P80,
            objective_weights=ObjectiveWeights(),
        )
        result = PriorityHeuristicSolver().solve(problem)
        assert result.decisions
        for dec in result.decisions[:5]:
            route = world.routes.get(dec.route_id)
            if route is not None:
                expected = max(1, int(round(route.base_travel_hours)))
                assert dec.estimated_arrival_hour == expected, (
                    f"Heuristic {dec.decision_id}: expected {expected}, "
                    f"got {dec.estimated_arrival_hour}"
                )

    def test_lp_and_heuristic_use_same_canonical_function(self):
        """Both solvers must produce the same estimated_arrival for the same route."""
        world = WorldGenerator(seed=42).generate_world()
        problem = OptimizationInputAdapter.create_problem(
            world=world, risk_assessments={},
            demand_policy=DemandPolicy.P80,
            objective_weights=ObjectiveWeights(),
        )
        lp_result = MilpSolver(allow_fallback=False).solve(problem)
        heur_result = PriorityHeuristicSolver().solve(problem)

        # Build route_id -> estimated_arrival for both solvers
        lp_by_route = {d.route_id: d.estimated_arrival_hour for d in lp_result.decisions}
        heur_by_route = {d.route_id: d.estimated_arrival_hour for d in heur_result.decisions}

        # For any route used by both, arrivals must agree
        shared_routes = set(lp_by_route.keys()) & set(heur_by_route.keys())
        for rid in shared_routes:
            assert lp_by_route[rid] == heur_by_route[rid], (
                f"Route {rid}: LP says {lp_by_route[rid]}, "
                f"heuristic says {heur_by_route[rid]}. Both must use compute_estimated_arrival()."
            )


# ==============================================================================
# FIX #3 - REJECTION SUMMARY IN RecommendationListResponse
# ==============================================================================

class TestRejectionSummary:

    def test_rejection_summary_populated_when_conflicts_exist(self):
        from backend.app.decision.service import DecisionService
        from backend.app.decision.schemas import RecommendationGenerateRequest
        svc = DecisionService()
        req = RecommendationGenerateRequest(scenario_id="COMPOUND_DISRUPTION", seed=42)
        response = svc.generate_recommendations(req)
        rejected_count = response.status_counts.get("REJECTED", 0)
        if rejected_count > 0:
            assert response.rejection_summary is not None
            assert len(response.rejection_summary) > 0

    def test_rejection_summary_contains_rejected_count(self):
        from backend.app.decision.service import DecisionService
        from backend.app.decision.schemas import RecommendationGenerateRequest
        svc = DecisionService()
        req = RecommendationGenerateRequest(scenario_id="COMPOUND_DISRUPTION", seed=42)
        response = svc.generate_recommendations(req)
        rejected_count = response.status_counts.get("REJECTED", 0)
        if rejected_count > 0:
            assert str(rejected_count) in (response.rejection_summary or "")

    def test_rejection_summary_none_when_no_rejections(self):
        from backend.app.decision.schemas import RecommendationListResponse
        response = RecommendationListResponse(
            total_recommendations=2,
            status_counts={"VERIFIED": 2},
            action_counts={"MOVE": 2},
            recommendations=[],
            rejection_summary=None,
        )
        assert response.rejection_summary is None

    def test_conflict_detector_still_rejects_vehicle_conflicts(self):
        """Conflict detector must NOT have been weakened by Fix #3."""
        from backend.app.decision.service import DecisionService
        from backend.app.decision.schemas import RecommendationGenerateRequest
        svc = DecisionService()
        req = RecommendationGenerateRequest(scenario_id="COMPOUND_DISRUPTION", seed=42)
        response = svc.generate_recommendations(req)
        rejected = [r for r in response.recommendations if r.status == "REJECTED"]
        for r in rejected:
            assert r.conflict_detected is True
            assert len(r.conflict_details) > 0

    def test_rejection_summary_explains_vehicle_conflict_cause(self):
        from backend.app.decision.service import DecisionService
        from backend.app.decision.schemas import RecommendationGenerateRequest
        svc = DecisionService()
        req = RecommendationGenerateRequest(scenario_id="COMPOUND_DISRUPTION", seed=42)
        response = svc.generate_recommendations(req)
        rejected_count = response.status_counts.get("REJECTED", 0)
        if rejected_count > 0 and response.rejection_summary:
            summary_lower = response.rejection_summary.lower()
            assert "vehicle" in summary_lower or "conflict" in summary_lower

    def test_rejection_summary_is_schema_field_not_a_workaround(self):
        """rejection_summary must be a first-class field on RecommendationListResponse."""
        from backend.app.decision.schemas import RecommendationListResponse
        fields = RecommendationListResponse.model_fields
        assert "rejection_summary" in fields, (
            "rejection_summary must be declared as a Pydantic model field"
        )
