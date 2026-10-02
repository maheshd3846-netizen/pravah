"""Baseline demand forecasting models."""

from ml.baselines.moving_average import MovingAverageForecaster
from ml.baselines.seasonal_naive import SeasonalNaiveForecaster

__all__ = ["MovingAverageForecaster", "SeasonalNaiveForecaster"]
