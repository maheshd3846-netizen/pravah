"""Baseline Time-Series Forecasters for Supply Chain Demand.

Provides naive Moving Average and Holt-Winters-style Exponential Smoothing
baselines to compare with advanced machine learning models.
"""

from __future__ import annotations
from typing import Dict, List, Optional
import numpy as np
import pandas as pd


class MovingAverageForecaster:
    """Simple moving average forecaster over a rolling window."""

    def __init__(self, window: int = 24):
        self.window = window

    def predict(self, series: pd.Series, horizon: int = 24) -> np.ndarray:
        """Projects demand forward based on last window values."""
        if len(series) == 0:
            return np.zeros(horizon)
        val = float(series.tail(self.window).mean())
        return np.full(horizon, val)


class ExponentialSmoothingForecaster:
    """Exponentially weighted moving average with alpha smoothing factor."""

    def __init__(self, alpha: float = 0.3):
        self.alpha = alpha

    def predict(self, series: pd.Series, horizon: int = 24) -> np.ndarray:
        """Forecasts flat future projection based on smoothed level."""
        if len(series) == 0:
            return np.zeros(horizon)
        ewm_val = float(series.ewm(alpha=self.alpha).mean().iloc[-1])
        return np.full(horizon, ewm_val)
