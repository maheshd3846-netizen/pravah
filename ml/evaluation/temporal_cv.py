"""Temporal Expanding-Window Cross-Validation for PRAVAH Demand Forecasting.

Implements rigorous chronological validation to prevent temporal lookahead bias:
- Never shuffles time series randomly.
- Uses expanding window splits across consecutive monthly horizons.
- Evaluates baseline models against XGBoost across every fold.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Generator, Tuple
import pandas as pd
import numpy as np

from ml.features.feature_pipeline import FeaturePipeline
from ml.models.base import BaseForecastModel
from ml.evaluation.metrics import evaluate_quantile_forecast


@dataclass
class FoldResult:
    fold_idx: int
    train_start_hour: int
    train_end_hour: int
    test_start_hour: int
    test_end_hour: int
    metrics: Dict[str, Any]


class TemporalCrossValidator:
    """Expanding-window time series validator for forward logistics demand.

    Validation Strategy:
    Given multi-month synthetic demand history, partition into monthly intervals (720h each).
    - Fold 1: Train on hours 0 to 6*720-1 (Months 1–6), Test on Month 7 (hours 6*720 to 7*720-1)
    - Fold 2: Train on hours 0 to 7*720-1 (Months 1–7), Test on Month 8 (hours 7*720 to 8*720-1)
    - Fold 3: Train on hours 0 to 8*720-1 (Months 1–8), Test on Month 9 (hours 8*720 to 9*720-1)
    - Fold 4: Train on hours 0 to 9*720-1 (Months 1–9), Test on Month 10 (hours 9*720 to 10*720-1)
    """

    def __init__(
        self,
        month_hours: int = 720,
        initial_train_months: int = 6,
        n_splits: int = 4,
    ):
        self.month_hours = month_hours
        self.initial_train_months = initial_train_months
        self.n_splits = n_splits

    def split(self, df: pd.DataFrame) -> Generator[Tuple[pd.DataFrame, pd.DataFrame, int], None, None]:
        """Yields (train_df, test_df, fold_idx) strictly partitioned by timestamp_hour."""
        for fold in range(self.n_splits):
            train_end = (self.initial_train_months + fold) * self.month_hours
            test_end = train_end + self.month_hours

            train_df = df[df["timestamp_hour"] < train_end].copy()
            test_df = df[
                (df["timestamp_hour"] >= train_end) & (df["timestamp_hour"] < test_end)
            ].copy()

            if len(train_df) > 0 and len(test_df) > 0:
                yield train_df, test_df, fold + 1

    def evaluate_model(
        self,
        model: BaseForecastModel,
        pipeline: FeaturePipeline,
        raw_df: pd.DataFrame,
        horizon_hours: int = 24,
    ) -> Dict[str, Any]:
        """Runs temporal expanding-window validation on a given model."""
        fold_results: List[FoldResult] = []

        for train_raw, test_raw, fold_idx in self.split(raw_df):
            # Fit feature pipeline and model on train fold only
            X_train, y_train = pipeline.fit_transform(train_raw)
            model.fit(X_train, y_train)

            # Transform test features
            X_test = pipeline.transform(test_raw)
            y_test = test_raw["requested_demand"].to_numpy(dtype=np.float32)

            forecast = model.predict(X_test)
            metrics = evaluate_quantile_forecast(
                y_true=y_test,
                p50=forecast.p50,
                p80=forecast.p80,
                p95=forecast.p95,
                model_name=getattr(model, "model_name", "unknown"),
                horizon_hours=horizon_hours,
            )

            train_min_h = int(train_raw["timestamp_hour"].min())
            train_max_h = int(train_raw["timestamp_hour"].max())
            test_min_h = int(test_raw["timestamp_hour"].min())
            test_max_h = int(test_raw["timestamp_hour"].max())

            fold_results.append(
                FoldResult(
                    fold_idx=fold_idx,
                    train_start_hour=train_min_h,
                    train_end_hour=train_max_h,
                    test_start_hour=test_min_h,
                    test_end_hour=test_max_h,
                    metrics=metrics,
                )
            )

        # Average metrics across folds
        avg_mae = float(np.mean([f.metrics["mae"] for f in fold_results])) if fold_results else 0.0
        avg_rmse = float(np.mean([f.metrics["rmse"] for f in fold_results])) if fold_results else 0.0
        avg_wape = float(np.mean([f.metrics["wape_percent"] for f in fold_results])) if fold_results else 0.0
        avg_p50_cov = float(np.mean([f.metrics["p50_coverage_percent"] for f in fold_results])) if fold_results else 0.0
        avg_p80_cov = float(np.mean([f.metrics["p80_coverage_percent"] for f in fold_results])) if fold_results else 0.0
        avg_p95_cov = float(np.mean([f.metrics["p95_coverage_percent"] for f in fold_results])) if fold_results else 0.0

        return {
            "model": getattr(model, "model_name", "unknown"),
            "folds_evaluated": len(fold_results),
            "mean_mae": round(avg_mae, 2),
            "mean_rmse": round(avg_rmse, 2),
            "mean_wape_percent": round(avg_wape, 2),
            "mean_p50_coverage_percent": round(avg_p50_cov, 2),
            "mean_p80_coverage_percent": round(avg_p80_cov, 2),
            "mean_p95_coverage_percent": round(avg_p95_cov, 2),
            "fold_details": [
                {
                    "fold": f.fold_idx,
                    "train_hours": f"{f.train_start_hour}-{f.train_end_hour}",
                    "test_hours": f"{f.test_start_hour}-{f.test_end_hour}",
                    "mae": f.metrics["mae"],
                    "wape_percent": f.metrics["wape_percent"],
                }
                for f in fold_results
            ],
        }
