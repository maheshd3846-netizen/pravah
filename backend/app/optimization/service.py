"""Backend Optimization Service adapter."""

from __future__ import annotations
from typing import Dict, Any
from optimization.solver import LogisticsSolver
from optimization.evaluator import PlanEvaluator
from optimization.model import OptimizationProblem, OptimizationPlan


class OptimizationService:
    """Provides optimization planning and counterfactual validation."""

    def __init__(self):
        self.solver = LogisticsSolver()
        self.evaluator = PlanEvaluator()

    def generate_plan(self, problem: OptimizationProblem) -> OptimizationPlan:
        return self.solver.solve(problem)
