"""XGBoost Quantile Forecaster for Tactical Military Logistics Demand.

Trains dedicated quantile regressors for P50, P80, and P95 with explicit
hyperparameter configuration objects and monotonic quantile guarantees.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import xgboost as xgb
from ml.models.base import BaseForecastModel, ForecastOutput

MODEL_VERSION = "xgb-demand-v1"


@dataclass
class XGBForecastConfig:
    """Hyperparameter configuration object preventing magic numbers throughout the codebase."""
    n_estimators: int = 120
    max_depth: int = 5
    learning_rate: float = 0.08
    subsample: float = 0.85
    colsample_bytree: float = 0.85
    random_state: int = 42
    n_jobs: int = -1

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DemandXGBForecaster(BaseForecastModel):
    """Multi-quantile gradient-boosted demand forecaster (P50, P80, P95)."""

    def __init__(self, config: Optional[XGBForecastConfig] = None):
        self.config = config or XGBForecastConfig()
        self.model_name = "XGBoostQuantileForecaster"
        self.model_version = MODEL_VERSION
        self.feature_columns: List[str] = []
        self.is_fitted: bool = False

        # Initialize dedicated quantile models
        self.model_p50 = xgb.XGBRegressor(
            objective="reg:quantileerror",
            quantile_alpha=0.50,
            n_estimators=self.config.n_estimators,
            max_depth=self.config.max_depth,
            learning_rate=self.config.learning_rate,
            subsample=self.config.subsample,
            colsample_bytree=self.config.colsample_bytree,
            random_state=self.config.random_state,
            n_jobs=self.config.n_jobs,
        )

        self.model_p80 = xgb.XGBRegressor(
            objective="reg:quantileerror",
            quantile_alpha=0.80,
            n_estimators=self.config.n_estimators,
            max_depth=self.config.max_depth,
            learning_rate=self.config.learning_rate,
            subsample=self.config.subsample,
            colsample_bytree=self.config.colsample_bytree,
            random_state=self.config.random_state,
            n_jobs=self.config.n_jobs,
        )

        self.model_p95 = xgb.XGBRegressor(
            objective="reg:quantileerror",
            quantile_alpha=0.95,
            n_estimators=self.config.n_estimators,
            max_depth=self.config.max_depth,
            learning_rate=self.config.learning_rate,
            subsample=self.config.subsample,
            colsample_bytree=self.config.colsample_bytree,
            random_state=self.config.random_state,
            n_jobs=self.config.n_jobs,
        )

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "DemandXGBForecaster":
        """Fits all three quantile regression models on training features and targets."""
        self.feature_columns = list(X.columns)
        self.model_p50.fit(X, y)
        self.model_p80.fit(X, y)
        self.model_p95.fit(X, y)
        self.is_fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> ForecastOutput:
        """Generates monotonically ordered P50, P80, and P95 demand predictions."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict() is called.")

        raw_p50 = np.maximum(0.0, self.model_p50.predict(X[self.feature_columns]))
        raw_p80 = np.maximum(0.0, self.model_p80.predict(X[self.feature_columns]))
        raw_p95 = np.maximum(0.0, self.model_p95.predict(X[self.feature_columns]))

        # Enforce quantile monotonicity: p50 <= p80 <= p95
        p50 = raw_p50
        p80 = np.maximum(p50, raw_p80)
        p95 = np.maximum(p80, raw_p95)

        return ForecastOutput(
            p50=np.round(p50, 2),
            p80=np.round(p80, 2),
            p95=np.round(p95, 2),
            model_name=self.model_name,
            model_version=self.model_version,
            metadata={"config": self.config.to_dict()},
        )

    def get_feature_importances(self, top_k: int = 10) -> List[Dict[str, Any]]:
        """Returns top model drivers based on P50 gradient boosting feature gains."""
        if not self.is_fitted:
            return []

        booster = self.model_p50.get_booster()
        score_dict = booster.get_score(importance_type="gain")

        # Map back to feature columns
        importances = []
        for feat_name, score in score_dict.items():
            importances.append({"feature": feat_name, "importance": round(float(score), 4)})

        # Sort descending
        importances.sort(key=lambda x: x["importance"], reverse=True)
        return importances[:top_k]
