"""Moving Average Baseline Forecaster conforming to unified PRAVAH interface."""

from __future__ import annotations
import numpy as np
import pandas as pd
from ml.models.base import BaseForecastModel, ForecastOutput


class MovingAverageForecaster(BaseForecastModel):
    """Moving Average baseline predicting recent rolling mean with empirical uncertainty."""

    def __init__(self, window_column: str = "rolling_mean_24h"):
        self.window_column = window_column
        self.residual_std: float = 1.0
        self.model_name = "MovingAverageBaseline"
        self.model_version = "ma-v1"

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "MovingAverageForecaster":
        """Calculates historical residuals to estimate prediction intervals."""
        if self.window_column in X.columns:
            preds = np.maximum(0.0, X[self.window_column].to_numpy())
        elif "lag_1" in X.columns:
            preds = np.maximum(0.0, X["lag_1"].to_numpy())
        else:
            preds = np.full(len(y), float(y.mean()))

        residuals = y.to_numpy() - preds
        self.residual_std = max(0.1, float(np.std(residuals)))
        return self

    def predict(self, X: pd.DataFrame) -> ForecastOutput:
        """Projects demand forward as P50, P80, and P95 quantiles."""
        if self.window_column in X.columns:
            p50 = np.maximum(0.0, X[self.window_column].to_numpy(dtype=np.float32))
        elif "lag_1" in X.columns:
            p50 = np.maximum(0.0, X["lag_1"].to_numpy(dtype=np.float32))
        else:
            p50 = np.zeros(len(X), dtype=np.float32)

        # Standard normal quantiles: z_0.80 = 0.8416, z_0.95 = 1.6449
        p80 = np.maximum(p50, p50 + 0.8416 * self.residual_std)
        p95 = np.maximum(p80, p50 + 1.6449 * self.residual_std)

        return ForecastOutput(
            p50=np.round(p50, 2),
            p80=np.round(p80, 2),
            p95=np.round(p95, 2),
            model_name=self.model_name,
            model_version=self.model_version,
            metadata={"residual_std": round(self.residual_std, 2)},
        )
