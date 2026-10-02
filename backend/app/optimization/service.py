"""Backend Optimization Service Adapter and Run Manager."""

from __future__ import annotations
from typing import Dict, List, Optional, Any

from simulation.world_generator import WorldGenerator, DisruptionType
from simulation.disruption_engine import Disruption
from backend.app.services.scenario_service import ScenarioService
from backend.app.risk.service import RiskIntelligenceService
from optimization.types import (
    DemandPolicy,
    SolverType,
    ObjectiveWeights,
    OptimizationResult,
)
from optimization.adapters import OptimizationInputAdapter
from optimization.solver import LogisticsSolver
from optimization.evaluator import PlanEvaluator


class OptimizationService:
    """Manages end-to-end optimization runs, problem synthesis, and run caching."""

    def __init__(self):
        self.risk_service = RiskIntelligenceService()
        self.scenario_service = ScenarioService()
        self.evaluator = PlanEvaluator()
        self._cached_results: Dict[str, OptimizationResult] = {}

    def solve_scenario(
        self,
        scenario_id: str = "DEFAULT",
        demand_policy: DemandPolicy = DemandPolicy.P80,
        solver_type: SolverType = SolverType.MILP,
        weights_dict: Optional[Dict[str, float]] = None,
        horizon_hours: int = 72,
    ) -> OptimizationResult:
        """Constructs and executes a mathematical optimization run."""
        # 1. Generate world state
        world = WorldGenerator(seed=42).generate_world()

        # Apply disruption if specified
        if scenario_id and scenario_id.upper() not in ["DEFAULT", "BASELINE"]:
            sc_dict = self.scenario_service.get_scenario(scenario_id)
            if sc_dict and "disruptions" in sc_dict:
                from simulation.disruption_engine import DisruptionEngine
                dis_list = [Disruption.from_dict(d_data) for d_data in sc_dict["disruptions"]]
                dis_engine = DisruptionEngine(dis_list)
                dis_engine.apply_route_disruptions(world.routes, current_hour=40)
                dis_engine.apply_vehicle_disruptions(world.vehicles, current_hour=40)

        # 2. Risk evaluation
        self.risk_service.evaluate_world_risk(world)
        risk_assessments = self.risk_service._cached_assessments

        # 3. Configure objective weights
        if weights_dict:
            weights = ObjectiveWeights(
                transport_weight=weights_dict.get("transport", 1.0),
                shortage_weight=weights_dict.get("shortage", 50.0),
                delay_weight=weights_dict.get("delay", 3.0),
                risk_weight=weights_dict.get("risk", 10.0),
                imbalance_weight=weights_dict.get("imbalance", 1.0),
            )
        else:
            weights = ObjectiveWeights()

        # 4. Synthesize optimization problem
        problem = OptimizationInputAdapter.create_problem(
            world=world,
            risk_assessments=risk_assessments,
            demand_policy=demand_policy,
            objective_weights=weights,
            horizon_hours=horizon_hours,
            scenario_id=scenario_id,
        )

        # 5. Solve using chosen engine
        solver = LogisticsSolver(solver_type=solver_type)
        result = solver.solve(problem)

        # Cache run result
        self._cached_results[result.run_id] = result
        return result

    def get_result(self, run_id: str) -> Optional[OptimizationResult]:
        """Retrieves a previously computed optimization run from cache."""
        return self._cached_results.get(run_id)

    def evaluate_plan(
        self,
        optimization_run_id: str,
        scenario_id: str = "COMPOUND_DISRUPTION",
        horizon_hours: int = 72,
        seed: int = 42,
    ) -> Any:
        """Executes counterfactual paired simulation evaluating the given optimization run."""
        from simulation.simulator import SimulationConfig
        opt_res = self.get_result(optimization_run_id)
        if not opt_res:
            opt_res = self.solve_scenario(scenario_id=scenario_id, horizon_hours=horizon_hours)

        dis_list = []
        if scenario_id and scenario_id.upper() not in ["DEFAULT", "BASELINE"]:
            sc_dict = self.scenario_service.get_scenario(scenario_id)
            if sc_dict and "disruptions" in sc_dict:
                dis_list = [Disruption.from_dict(d_data) for d_data in sc_dict["disruptions"]]

        base_config = SimulationConfig(
            seed=seed,
            horizon_hours=horizon_hours,
            scenario_name=scenario_id,
            auto_replenish=True,
            disruptions=dis_list,
        )

        eval_result = self.evaluator.evaluate_plan(
            plan_or_result=opt_res,
            base_config=base_config,
            scenario_id=scenario_id,
            horizon_hours=horizon_hours,
            seed=seed,
        )
        if not hasattr(self, "_cached_evaluations"):
            self._cached_evaluations = {}
        self._cached_evaluations[eval_result.evaluation_id] = eval_result
        return eval_result

    def get_evaluation(self, evaluation_id: str) -> Optional[Any]:
        """Retrieves a previously computed evaluation result from cache."""
        if not hasattr(self, "_cached_evaluations"):
            self._cached_evaluations = {}
        return self._cached_evaluations.get(evaluation_id)
