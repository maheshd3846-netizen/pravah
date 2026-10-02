"""API Router for Logistics Optimization Core Endpoints."""

from __future__ import annotations
from typing import Dict, Any
from fastapi import APIRouter, HTTPException

from backend.app.optimization.schemas import (
    OptimizationSolveRequest,
    OptimizationSolveResponse,
    MovementDecisionSchema,
)
from backend.app.optimization.service import OptimizationService

router = APIRouter(prefix="/optimization", tags=["Logistics Optimization"])
opt_service = OptimizationService()


@router.post("/solve", response_model=OptimizationSolveResponse)
async def solve_optimization(request: OptimizationSolveRequest) -> OptimizationSolveResponse:
    """Calculates risk-aware optimal supply allocation, convoy dispatches, and rerouting."""
    try:
        result = opt_service.solve_scenario(
            scenario_id=request.scenario_id,
            demand_policy=request.demand_policy,
            solver_type=request.solver_type,
            weights_dict=request.objective_weights,
            horizon_hours=request.horizon_hours,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization solver failure: {str(e)}")

    return OptimizationSolveResponse(
        run_id=result.run_id,
        status=result.status.value,
        solver_type=result.solver_type.value,
        objective_value=result.objective_value,
        execution_time_ms=result.execution_time_ms,
        demand_policy=result.demand_policy.value,
        total_transport_cost=result.total_transport_cost,
        total_shortage=result.total_shortage,
        total_delay=result.total_delay,
        total_risk_cost=result.total_risk_cost,
        vehicle_utilization=result.vehicle_utilization,
        route_utilization=result.route_utilization,
        decisions=[
            MovementDecisionSchema(
                decision_id=d.decision_id,
                source_node_id=d.source_node_id,
                destination_node_id=d.destination_node_id,
                item=d.item,
                quantity=d.quantity,
                route_id=d.route_id,
                vehicle_id=d.vehicle_id,
                dispatch_hour=d.dispatch_hour,
                estimated_arrival_hour=d.estimated_arrival_hour,
                priority=d.priority,
                reason_codes=d.reason_codes,
                rationale=d.rationale,
            )
            for d in result.decisions
        ],
        infeasibility_reasons=result.infeasibility_reasons,
        metadata=result.metadata,
    )


@router.get("/{run_id}", response_model=OptimizationSolveResponse)
async def get_optimization_run(run_id: str) -> OptimizationSolveResponse:
    """Retrieves an existing optimization run result by ID."""
    result = opt_service.get_result(run_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Optimization run '{run_id}' not found.")

    return OptimizationSolveResponse(
        run_id=result.run_id,
        status=result.status.value,
        solver_type=result.solver_type.value,
        objective_value=result.objective_value,
        execution_time_ms=result.execution_time_ms,
        demand_policy=result.demand_policy.value,
        total_transport_cost=result.total_transport_cost,
        total_shortage=result.total_shortage,
        total_delay=result.total_delay,
        total_risk_cost=result.total_risk_cost,
        vehicle_utilization=result.vehicle_utilization,
        route_utilization=result.route_utilization,
        decisions=[
            MovementDecisionSchema(
                decision_id=d.decision_id,
                source_node_id=d.source_node_id,
                destination_node_id=d.destination_node_id,
                item=d.item,
                quantity=d.quantity,
                route_id=d.route_id,
                vehicle_id=d.vehicle_id,
                dispatch_hour=d.dispatch_hour,
                estimated_arrival_hour=d.estimated_arrival_hour,
                priority=d.priority,
                reason_codes=d.reason_codes,
                rationale=d.rationale,
            )
            for d in result.decisions
        ],
        infeasibility_reasons=result.infeasibility_reasons,
        metadata=result.metadata,
    )
