"""Unified Solver Interface for PRAVAH Logistics Decision Engine."""

from __future__ import annotations
from typing import Dict, Any, Optional
from optimization.model import OptimizationProblem, OptimizationPlan
from optimization.heuristic import PriorityHeuristicSolver


class LogisticsSolver:
    """Dispatches optimization problems to MILP or heuristic solvers."""

    def __init__(self, solver_type: str = "heuristic"):
        self.solver_type = solver_type
        self.heuristic_solver = PriorityHeuristicSolver()

    def solve(self, problem: OptimizationProblem) -> OptimizationPlan:
        # Default to robust deterministic heuristic with MILP-ready signature
        return self.heuristic_solver.solve(problem)
