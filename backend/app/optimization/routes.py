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


from backend.app.optimization.schemas import (
    OptimizationEvaluateRequest,
    OptimizationEvaluateResponse,
    MetricDeltaSchema,
)


@router.post("/evaluate", response_model=OptimizationEvaluateResponse)
async def evaluate_plan_counterfactual(
    request: OptimizationEvaluateRequest,
) -> OptimizationEvaluateResponse:
    """Executes closed-loop counterfactual simulation comparing baseline vs optimized outcomes."""
    try:
        eval_result = opt_service.evaluate_plan(
            optimization_run_id=request.optimization_run_id,
            scenario_id=request.scenario_id,
            horizon_hours=request.horizon_hours,
            seed=request.seed,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Counterfactual evaluation failure: {str(e)}")

    deltas_dict = {}
    for k, d in eval_result.deltas.items():
        deltas_dict[k] = MetricDeltaSchema(
            metric_name=d.metric_name,
            baseline=d.baseline,
            optimized=d.optimized,
            absolute_delta=d.absolute_delta,
            relative_delta_percent=d.relative_delta_percent,
            direction=d.direction.value,
            is_better=d.is_better,
        )

    return OptimizationEvaluateResponse(
        evaluation_id=eval_result.evaluation_id,
        optimization_run_id=eval_result.optimization_run_id,
        scenario_id=eval_result.scenario_id,
        status=eval_result.status.value,
        horizon_hours=eval_result.horizon_hours,
        seed=eval_result.seed,
        initial_state_hash=eval_result.initial_state_hash,
        baseline=eval_result.baseline.to_dict(),
        optimized=eval_result.optimized.to_dict(),
        deltas=deltas_dict,
        tradeoffs=eval_result.tradeoffs,
        critical_nodes=eval_result.critical_nodes,
        shipment_trace=[t.to_dict() for t in eval_result.shipment_trace],
        plan_validation={
            "status": eval_result.plan_validation_status,
            "violations": eval_result.plan_validation_violations,
        },
        created_at=eval_result.created_at,
    )


@router.get("/evaluations/{evaluation_id}", response_model=OptimizationEvaluateResponse)
async def get_evaluation_record(evaluation_id: str) -> OptimizationEvaluateResponse:
    """Retrieves an existing closed-loop evaluation record by evaluation ID."""
    eval_result = opt_service.get_evaluation(evaluation_id)
    if not eval_result:
        raise HTTPException(status_code=404, detail=f"Evaluation record '{evaluation_id}' not found.")

    deltas_dict = {}
    for k, d in eval_result.deltas.items():
        deltas_dict[k] = MetricDeltaSchema(
            metric_name=d.metric_name,
            baseline=d.baseline,
            optimized=d.optimized,
            absolute_delta=d.absolute_delta,
            relative_delta_percent=d.relative_delta_percent,
            direction=d.direction.value,
            is_better=d.is_better,
        )

    return OptimizationEvaluateResponse(
        evaluation_id=eval_result.evaluation_id,
        optimization_run_id=eval_result.optimization_run_id,
        scenario_id=eval_result.scenario_id,
        status=eval_result.status.value,
        horizon_hours=eval_result.horizon_hours,
        seed=eval_result.seed,
        initial_state_hash=eval_result.initial_state_hash,
        baseline=eval_result.baseline.to_dict(),
        optimized=eval_result.optimized.to_dict(),
        deltas=deltas_dict,
        tradeoffs=eval_result.tradeoffs,
        critical_nodes=eval_result.critical_nodes,
        shipment_trace=[t.to_dict() for t in eval_result.shipment_trace],
        plan_validation={
            "status": eval_result.plan_validation_status,
            "violations": eval_result.plan_validation_violations,
        },
        created_at=eval_result.created_at,
    )
