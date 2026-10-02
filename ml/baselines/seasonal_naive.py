"""Seasonal Naive Forecaster using historical diurnal/weekly patterns."""

from __future__ import annotations
import numpy as np
import pandas as pd
from ml.models.base import BaseForecastModel, ForecastOutput


class SeasonalNaiveForecaster(BaseForecastModel):
    """Seasonal Naive model using same hour of previous week (t-168) or day (t-24)."""

    def __init__(self, primary_col: str = "lag_168", fallback_col: str = "lag_24"):
        self.primary_col = primary_col
        self.fallback_col = fallback_col
        self.residual_std: float = 1.0
        self.model_name = "SeasonalNaiveBaseline"
        self.model_version = "snaive-v1"

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "SeasonalNaiveForecaster":
        """Fits empirical variance based on historical seasonal errors."""
        preds = self._get_point_predictions(X)
        residuals = y.to_numpy() - preds
        self.residual_std = max(0.1, float(np.std(residuals)))
        return self

    def _get_point_predictions(self, X: pd.DataFrame) -> np.ndarray:
        if self.primary_col in X.columns and not X[self.primary_col].isna().all():
            preds = X[self.primary_col].fillna(X.get(self.fallback_col, 0.0)).to_numpy()
        elif self.fallback_col in X.columns:
            preds = X[self.fallback_col].to_numpy()
        elif "lag_1" in X.columns:
            preds = X["lag_1"].to_numpy()
        else:
            preds = np.zeros(len(X))
        return np.maximum(0.0, preds)

    def predict(self, X: pd.DataFrame) -> ForecastOutput:
        """Projects demand forward based on seasonal lag plus uncertainty bounds."""
        p50 = self._get_point_predictions(X).astype(np.float32)
        p80 = np.maximum(p50, p50 + 0.8416 * self.residual_std).astype(np.float32)
        p95 = np.maximum(p80, p50 + 1.6449 * self.residual_std).astype(np.float32)

        return ForecastOutput(
            p50=np.round(p50, 2),
            p80=np.round(p80, 2),
            p95=np.round(p95, 2),
            model_name=self.model_name,
            model_version=self.model_version,
            metadata={"residual_std": round(self.residual_std, 2)},
        )
