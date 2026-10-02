"""Forecasting Service for tactical demand projection."""

from __future__ import annotations
from typing import Dict, Any, List
import pandas as pd
from ml.baselines.moving_average import MovingAverageForecaster
from ml.xgboost.forecaster import DemandXGBForecaster


class ForecastingService:
    """Provides baseline and ML-driven demand projections."""

    def __init__(self):
        self.baseline_forecaster = MovingAverageForecaster(window=24)
        self.xgb_forecaster = DemandXGBForecaster()

    def generate_baseline_forecast(self, history_series: List[float], horizon: int = 24) -> List[float]:
        series = pd.Series(history_series)
        preds = self.baseline_forecaster.predict(series, horizon=horizon)
        return [round(float(v), 2) for v in preds]
