"""Evaluation Metrics for PRAVAH Demand Forecasts.

Computes point accuracy (MAE, RMSE, WAPE, MAPE) and probabilistic quantile
calibration metrics (P50 coverage, P80 coverage, P95 coverage, interval widths).
"""

from __future__ import annotations
from typing import Dict, Any, Union
import numpy as np


def evaluate_forecast(
    y_true: Union[np.ndarray, list],
    y_pred: Union[np.ndarray, list],
) -> Dict[str, float]:
    """Calculates MAE, RMSE, MAPE, and WAPE for point forecasts."""
    y_t = np.asarray(y_true, dtype=np.float64)
    y_p = np.asarray(y_pred, dtype=np.float64)

    mae = float(np.mean(np.abs(y_t - y_p)))
    rmse = float(np.sqrt(np.mean((y_t - y_p) ** 2)))

    sum_actual = float(np.sum(np.abs(y_t)))
    wape = float(np.sum(np.abs(y_t - y_p)) / max(1e-5, sum_actual)) * 100.0

    non_zero = y_t > 0.1
    if np.any(non_zero):
        mape = float(np.mean(np.abs((y_t[non_zero] - y_p[non_zero]) / y_t[non_zero]))) * 100.0
    else:
        mape = 0.0

    return {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "wape_percent": round(wape, 2),
        "mape_percent": round(mape, 2),
    }


def evaluate_quantile_forecast(
    y_true: Union[np.ndarray, list],
    p50: Union[np.ndarray, list],
    p80: Union[np.ndarray, list],
    p95: Union[np.ndarray, list],
    model_name: str = "xgboost",
    horizon_hours: int = 24,
) -> Dict[str, Any]:
    """Comprehensive evaluation of probabilistic quantile forecasts."""
    y_t = np.asarray(y_true, dtype=np.float64)
    q50 = np.asarray(p50, dtype=np.float64)
    q80 = np.asarray(p80, dtype=np.float64)
    q95 = np.asarray(p95, dtype=np.float64)

    point_metrics = evaluate_forecast(y_t, q50)

    # Coverage: empirical fraction of actuals that fall below or equal the predicted quantile
    n = len(y_t)
    p50_cov = float(np.sum(y_t <= q50) / max(1, n)) * 100.0
    p80_cov = float(np.sum(y_t <= q80) / max(1, n)) * 100.0
    p95_cov = float(np.sum(y_t <= q95) / max(1, n)) * 100.0

    # Interval widths
    width_80_50 = float(np.mean(np.maximum(0.0, q80 - q50)))
    width_95_50 = float(np.mean(np.maximum(0.0, q95 - q50)))

    return {
        "model": model_name,
        "horizon_hours": horizon_hours,
        "sample_count": n,
        "mae": point_metrics["mae"],
        "rmse": point_metrics["rmse"],
        "wape_percent": point_metrics["wape_percent"],
        "mape_percent": point_metrics["mape_percent"],
        "p50_coverage_percent": round(p50_cov, 2),
        "p80_coverage_percent": round(p80_cov, 2),
        "p95_coverage_percent": round(p95_cov, 2),
        "mean_interval_width_p80_p50": round(width_80_50, 2),
        "mean_interval_width_p95_p50": round(width_95_50, 2),
    }
