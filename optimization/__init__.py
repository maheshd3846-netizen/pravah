"""Optimization Package for PRAVAH Tactical Logistics Decision Support.

Provides mathematical optimization models, vehicle routing & supply allocation
solvers (MILP via SciPy HiGHS & Heuristics), constraint validators, and input adapters.
"""

from optimization.types import (
    DemandPolicy,
    SolverType,
    OptimizationStatus,
    ReasonCode,
    ObjectiveWeights,
    MovementDecision,
    OptimizationResult,
)
from optimization.model import OptimizationProblem, SupplyDecision, OptimizationPlan
from optimization.variables import VariableRegistry
from optimization.constraints import ConstraintBuilder, validate_constraints
from optimization.objective import ObjectiveBuilder
from optimization.heuristic import PriorityHeuristicSolver
from optimization.solver import SolverAdapter, MilpSolver, LogisticsSolver
from optimization.adapters import OptimizationInputAdapter
from optimization.evaluator import PlanEvaluator

__all__ = [
    "DemandPolicy",
    "SolverType",
    "OptimizationStatus",
    "ReasonCode",
    "ObjectiveWeights",
    "MovementDecision",
    "OptimizationResult",
    "OptimizationProblem",
    "SupplyDecision",
    "OptimizationPlan",
    "VariableRegistry",
    "ConstraintBuilder",
    "validate_constraints",
    "ObjectiveBuilder",
    "PriorityHeuristicSolver",
    "SolverAdapter",
    "MilpSolver",
    "LogisticsSolver",
    "OptimizationInputAdapter",
    "PlanEvaluator",
]
