"""Forecasting API Endpoints."""

from __future__ import annotations
from typing import Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException

from simulation.world_generator import WorldGenerator
from simulation.demand_generator import DemandGenerator
from backend.app.forecasting.service import ForecastingService
from backend.app.schemas.forecast import (
    ForecastTrainRequest,
    ForecastTrainResponse,
    ForecastRunRequest,
    ForecastItemResponse,
)

router = APIRouter(prefix="/forecast", tags=["Forecasting"])
forecasting_service = ForecastingService()


@router.post("/train", response_model=ForecastTrainResponse)
async def train_forecast_models(request: ForecastTrainRequest) -> ForecastTrainResponse:
    """Trains feature pipeline, baseline models, and XGBoost quantile models on demand history."""
    world = WorldGenerator(seed=42).generate_world()
    demand_gen = DemandGenerator(seed=42)
    history_df = demand_gen.generate_annual_history(world.nodes, months=request.months_history)

    train_results = forecasting_service.train_models(
        history_df=history_df,
        run_cv=request.run_cross_validation,
    )

    return ForecastTrainResponse(
        status="success",
        training_samples=train_results.get("training_samples", 0),
        features_count=train_results.get("features_count", 0),
        xgboost_metrics=train_results.get("xgboost_metrics", {}),
        moving_average_metrics=train_results.get("moving_average_metrics", {}),
        top_features=train_results.get("top_features", []),
        cv_summary=train_results.get("cv_xgboost"),
    )


@router.post("/run", response_model=ForecastItemResponse)
async def run_forecast(request: ForecastRunRequest) -> ForecastItemResponse:
    """Generates P50, P80, P95 demand forecasts and uncertainty-aware inventory projections."""
    world = WorldGenerator(seed=42).generate_world()
    target_node = world.nodes.get(request.node_id)
    if not target_node:
        # Match by node_code if id not found
        for n in world.nodes.values():
            if n.code == request.node_id:
                target_node = n
                break

    if not target_node:
        raise HTTPException(status_code=404, detail=f"Node '{request.node_id}' not found.")

    current_inv = (
        request.current_inventory_override
        if request.current_inventory_override is not None
        else target_node.initial_inventory.get(request.item_id, 1000.0)
    )

    # 1. Generate multi-quantile forecast
    forecast = forecasting_service.generate_forecast(
        node_id=target_node.id,
        item_id=request.item_id,
        horizon_hours=request.horizon_hours,
        model_type=request.model_type,
    )

    # 2. Inventory Projection & Monte Carlo simulation
    proj_result = None
    if request.include_stockout_simulation:
        proj_result = forecasting_service.project_node_inventory(
            node_id=target_node.id,
            item_id=request.item_id,
            current_inventory=current_inv,
            horizon_hours=request.horizon_hours,
        )

    return ForecastItemResponse(
        node_id=target_node.id,
        item_id=request.item_id,
        horizon_hours=request.horizon_hours,
        model_version=forecasting_service.model_version,
        feature_version=forecasting_service.feature_version,
        generated_at=datetime.now(timezone.utc).isoformat(),
        p50=[float(x) for x in forecast.p50],
        p80=[float(x) for x in forecast.p80],
        p95=[float(x) for x in forecast.p95],
        stockout_probability=proj_result.stockout_probability if proj_result else None,
        time_to_safety_stock_hours=proj_result.time_to_safety_stock_hours if proj_result else None,
        time_to_zero_hours=proj_result.time_to_zero_hours if proj_result else None,
        dynamic_safety_stock=proj_result.dynamic_safety_stock if proj_result else None,
    )


@router.get("/{node_id}/{item_id}", response_model=ForecastItemResponse)
async def get_forecast_for_node_item(node_id: str, item_id: str) -> ForecastItemResponse:
    """Retrieves current 24-hour demand projection and stockout risk for a specific node and supply category."""
    req = ForecastRunRequest(node_id=node_id, item_id=item_id, horizon_hours=24)
    return await run_forecast(req)
