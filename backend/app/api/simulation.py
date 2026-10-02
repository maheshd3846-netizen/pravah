"""Simulation Execution and Inspection API Router."""

from __future__ import annotations
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from backend.app.schemas.simulation import (
    SimulationRunRequest,
    SimulationRunResponse,
    SimulationStateResponse,
    CriticalNodeSummary,
)
from backend.app.services.simulation_service import SimulationService

router = APIRouter(prefix="/simulation", tags=["Simulation"])
simulation_service = SimulationService()


@router.post("/run", response_model=SimulationRunResponse)
async def run_simulation(request: SimulationRunRequest) -> SimulationRunResponse:
    """Executes a full 1-hour discrete timestep simulation under requested scenario."""
    custom_disr = (
        [d.model_dump() for d in request.custom_disruptions]
        if request.custom_disruptions
        else None
    )

    result = simulation_service.execute_simulation(
        scenario_name=request.scenario_name,
        seed=request.seed,
        start_hour=request.start_hour,
        horizon_hours=request.horizon_hours,
        auto_replenish=request.auto_replenish,
        custom_disruptions=custom_disr,
    )

    critical_nodes_summary = [
        CriticalNodeSummary(
            node_code=cn["node_code"],
            unmet_demand=cn["unmet_demand"],
        )
        for cn in result.critical_nodes
    ]

    return SimulationRunResponse(
        run_id=result.run_id,
        scenario_name=result.scenario_name,
        seed=result.seed,
        horizon_hours=result.horizon_hours,
        total_requested_demand=result.total_requested_demand,
        total_fulfilled_demand=result.total_fulfilled_demand,
        total_unmet_demand=result.total_unmet_demand,
        fulfillment_rate_percent=result.fulfillment_rate_percent,
        total_stockout_events=result.total_stockout_events,
        stockout_hours_total=result.stockout_hours_total,
        critical_nodes=critical_nodes_summary,
        earliest_stockout_hour=result.earliest_stockout_hour,
        active_disruptions_count=result.active_disruptions_count,
        summary_metrics=result.summary_metrics,
        shipment_count=len(result.shipments),
    )


@router.get("/{run_id}/state", response_model=SimulationStateResponse)
async def get_simulation_state(run_id: str) -> SimulationStateResponse:
    """Returns runtime state, active shipments, and node status for an active or completed simulation run."""
    state = simulation_service.get_run_state(run_id)
    if not state:
        raise HTTPException(
            status_code=404,
            detail=f"Simulation run '{run_id}' not found in active or completed cache.",
        )
    return SimulationStateResponse(**state)
