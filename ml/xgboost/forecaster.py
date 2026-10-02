"""XGBoost Forecaster for Tactical Forward Demand.

Wraps XGBoost regressor with uncertainty bounds (quantile / residual variance)
and serialization support.
"""

from __future__ import annotations
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
import xgboost as xgb
from ml.features.feature_pipeline import FeaturePipeline


class DemandXGBForecaster:
    """Trains and executes gradient-boosted demand forecasting models."""

    def __init__(self, n_estimators: int = 100, max_depth: int = 5, learning_rate: float = 0.08):
        self.model = xgb.XGBRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            random_state=42,
            n_jobs=-1,
        )
        self.pipeline = FeaturePipeline()
        self.residual_std: float = 1.0
        self.is_fitted: bool = False

    def train(self, df: pd.DataFrame) -> Dict[str, float]:
        """Trains model on historical dataframe and computes residual variance for uncertainty bands."""
        X, y = self.pipeline.fit_transform(df)
        self.model.fit(X, y)
        preds = self.model.predict(X)
        residuals = y - preds
        self.residual_std = float(np.std(residuals))
        self.is_fitted = True

        mae = float(np.mean(np.abs(residuals)))
        rmse = float(np.sqrt(np.mean(residuals**2)))
        return {"mae": round(mae, 2), "rmse": round(rmse, 2), "sample_count": len(y)}

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Generates point predictions."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict.")
        return np.maximum(0.0, self.model.predict(X))

    def predict_with_uncertainty(self, X: pd.DataFrame) -> Dict[str, np.ndarray]:
        """Returns point forecast plus 10th and 90th percentile prediction intervals."""
        point = self.predict(X)
        # 1.645 * std for 90% confidence interval
        lower = np.maximum(0.0, point - 1.645 * self.residual_std)
        upper = point + 1.645 * self.residual_std
        return {
            "forecast": point,
            "lower_bound_p10": lower,
            "upper_bound_p90": upper,
        }
