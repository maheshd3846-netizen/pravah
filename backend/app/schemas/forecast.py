"""Pydantic Schemas for Forecasting and Inventory Projection APIs."""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ForecastTrainRequest(BaseModel):
    months_history: int = Field(default=3, ge=1, le=12)
    run_cross_validation: bool = Field(default=True)
    n_estimators: int = Field(default=80, ge=10, le=500)
    max_depth: int = Field(default=4, ge=2, le=10)


class ForecastTrainResponse(BaseModel):
    status: str
    training_samples: int
    features_count: int
    xgboost_metrics: Dict[str, Any]
    moving_average_metrics: Dict[str, Any]
    top_features: List[Dict[str, Any]]
    cv_summary: Optional[Dict[str, Any]] = None


class ForecastRunRequest(BaseModel):
    node_id: str
    item_id: str
    horizon_hours: int = Field(default=24, ge=1, le=168)
    model_type: str = Field(default="xgboost")  # xgboost, moving_average, seasonal_naive
    include_stockout_simulation: bool = Field(default=True)
    current_inventory_override: Optional[float] = None


class ForecastItemResponse(BaseModel):
    node_id: str
    item_id: str
    horizon_hours: int
    model_version: str
    feature_version: str
    generated_at: str
    p50: List[float]
    p80: List[float]
    p95: List[float]
    stockout_probability: Optional[float] = None
    time_to_safety_stock_hours: Optional[int] = None
    time_to_zero_hours: Optional[int] = None
    dynamic_safety_stock: Optional[float] = None
