"""Forecasting Service for PRAVAH Logistics Intelligence.

Coordinates model training, expanding-window temporal cross validation,
probabilistic multi-horizon inference (1h, 6h, 24h, 72h, 168h), and
uncertainty-aware inventory stockout projection.
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import pandas as pd

from ml.features.feature_pipeline import FeaturePipeline, FEATURE_VERSION
from ml.models.base import BaseForecastModel, ForecastOutput
from ml.baselines.moving_average import MovingAverageForecaster
from ml.baselines.seasonal_naive import SeasonalNaiveForecaster
from ml.xgboost.forecaster import DemandXGBForecaster, XGBForecastConfig, MODEL_VERSION
from ml.evaluation.temporal_cv import TemporalCrossValidator
from ml.evaluation.metrics import evaluate_quantile_forecast
from backend.app.forecasting.inventory_projection import (
    InventoryProjectionEngine,
    InventoryProjectionResult,
    DynamicSafetyStockConfig,
)


class ForecastingService:
    """Production-oriented forecasting service supporting baselines and XGBoost quantile models."""

    def __init__(self):
        self.model_version = MODEL_VERSION
        self.feature_version = FEATURE_VERSION

        self.pipeline = FeaturePipeline()
        self.xgb_model = DemandXGBForecaster()
        self.ma_model = MovingAverageForecaster()
        self.snaive_model = SeasonalNaiveForecaster()

        self.inventory_engine = InventoryProjectionEngine()
        self.cv_validator = TemporalCrossValidator()

        self.is_trained: bool = False
        self.evaluation_results: Dict[str, Any] = {}
        self.cached_forecasts: Dict[Tuple[str, str], Dict[str, Any]] = {}
        self.cached_projections: Dict[Tuple[str, str], InventoryProjectionResult] = {}

    def train_models(
        self,
        history_df: pd.DataFrame,
        run_cv: bool = True,
    ) -> Dict[str, Any]:
        """Trains FeaturePipeline, Baselines, and XGBoost quantile models with optional temporal validation."""
        results = {}

        # 1. Temporal Cross-Validation if requested
        if run_cv and len(history_df) >= 500:
            try:
                # Lightweight config for rapid validation
                val_pipeline = FeaturePipeline()
                val_xgb = DemandXGBForecaster(XGBForecastConfig(n_estimators=60, max_depth=4))
                cv_xgb = self.cv_validator.evaluate_model(val_xgb, val_pipeline, history_df)
                cv_ma = self.cv_validator.evaluate_model(self.ma_model, val_pipeline, history_df)
                results["cv_xgboost"] = cv_xgb
                results["cv_moving_average"] = cv_ma
            except Exception as e:
                results["cv_error"] = str(e)

        # 2. Fit full feature pipeline
        X, y = self.pipeline.fit_transform(history_df)

        # 3. Fit models
        self.xgb_model.fit(X, y)
        self.ma_model.fit(X, y)
        self.snaive_model.fit(X, y)
        self.is_trained = True

        # 4. Evaluate in-sample / holdout metrics
        preds_xgb = self.xgb_model.predict(X)
        metrics_xgb = evaluate_quantile_forecast(
            y_true=y,
            p50=preds_xgb.p50,
            p80=preds_xgb.p80,
            p95=preds_xgb.p95,
            model_name="xgboost",
        )

        preds_ma = self.ma_model.predict(X)
        metrics_ma = evaluate_quantile_forecast(
            y_true=y,
            p50=preds_ma.p50,
            p80=preds_ma.p80,
            p95=preds_ma.p95,
            model_name="moving_average",
        )

        results["training_samples"] = len(y)
        results["features_count"] = len(self.pipeline.feature_columns)
        results["xgboost_metrics"] = metrics_xgb
        results["moving_average_metrics"] = metrics_ma
        results["top_features"] = self.xgb_model.get_feature_importances(top_k=8)

        self.evaluation_results = results
        return results

    def generate_forecast(
        self,
        node_id: str,
        item_id: str,
        horizon_hours: int = 24,
        recent_history: Optional[pd.DataFrame] = None,
        model_type: str = "xgboost",
    ) -> ForecastOutput:
        """Produces P50, P80, P95 demand projection across requested horizon (1h, 6h, 24h, 72h, 168h)."""
        if not self.is_trained:
            # Fit minimal baseline on synthetic data if not explicitly trained
            from simulation.world_generator import WorldGenerator
            from simulation.demand_generator import DemandGenerator
            w = WorldGenerator(seed=42).generate_world()
            d_gen = DemandGenerator(seed=42)
            hist = d_gen.generate_annual_history(w.nodes, months=2)
            self.train_models(hist, run_cv=False)

        # Select model
        if model_type == "moving_average":
            selected_model: BaseForecastModel = self.ma_model
        elif model_type == "seasonal_naive":
            selected_model = self.snaive_model
        else:
            selected_model = self.xgb_model

        # Build inference rows for future horizon
        base_hour = 100
        if recent_history is not None and not recent_history.empty:
            base_hour = int(recent_history["timestamp_hour"].max()) + 1

        future_rows = []
        for step in range(horizon_hours):
            h = base_hour + step
            future_rows.append({
                "node_id": node_id,
                "item": item_id,
                "timestamp_hour": h,
                "hour_of_day": h % 24,
                "day_of_week": (h // 24) % 7,
                "elevation": 3500.0,
                "temperature": -5.0,
                "rainfall": 0.0,
                "wind_speed": 15.0,
                "visibility": 10.0,
                "weather_severity": "NORMAL",
                "current_inventory": 1000.0,
                "inbound_quantity": 0.0,
                "vehicle_availability": 1.0,
                "node_priority": 3.0,
                "requested_demand": 50.0,  # placeholder shifted out
            })

        future_df = pd.DataFrame(future_rows)
        # Prepend recent history for lag continuity if provided
        if recent_history is not None and not recent_history.empty:
            combined = pd.concat([recent_history, future_df], ignore_index=True)
            X_all = self.pipeline.transform(combined)
            X_future = X_all.iloc[-horizon_hours:]
        else:
            X_future = self.pipeline.transform(future_df)

        forecast = selected_model.predict(X_future)

        # Cache forecast
        self.cached_forecasts[(node_id, item_id)] = {
            "node_id": node_id,
            "item_id": item_id,
            "horizon_hours": horizon_hours,
            "model_version": self.model_version,
            "feature_version": self.feature_version,
            "forecast_output": forecast,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        return forecast

    def project_node_inventory(
        self,
        node_id: str,
        item_id: str,
        current_inventory: float,
        horizon_hours: int = 72,
        lead_time_hours: float = 24.0,
        scheduled_inbound: Optional[Dict[int, float]] = None,
        simulation_count: int = 1000,
        seed: int = 42,
    ) -> InventoryProjectionResult:
        """Projects future inventory and calculates Monte Carlo stockout probability."""
        forecast = self.generate_forecast(
            node_id=node_id,
            item_id=item_id,
            horizon_hours=horizon_hours,
        )

        p50 = [float(x) for x in forecast.p50]
        p80 = [float(x) for x in forecast.p80]
        p95 = [float(x) for x in forecast.p95]

        demand_std = float(np.std(p50)) if len(p50) > 1 else 10.0

        projection = self.inventory_engine.run_monte_carlo_stockout(
            node_id=node_id,
            item_id=item_id,
            current_inventory=current_inventory,
            p50_series=p50,
            p80_series=p80,
            p95_series=p95,
            scheduled_inbound=scheduled_inbound,
            demand_std=max(1.0, demand_std),
            lead_time_hours=lead_time_hours,
            simulation_count=simulation_count,
            seed=seed,
        )

        self.cached_projections[(node_id, item_id)] = projection
        return projection
