"""Evaluation Metrics for Supply Chain Demand & Inventory Predictions."""

from __future__ import annotations
from typing import Dict
import numpy as np


def evaluate_forecast(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculates MAE, RMSE, MAPE, and WAPE (Weighted Absolute Percentage Error)."""
    y_t = np.asarray(y_true, dtype=np.float64)
    y_p = np.asarray(y_pred, dtype=np.float64)

    mae = float(np.mean(np.abs(y_t - y_p)))
    rmse = float(np.sqrt(np.mean((y_t - y_p) ** 2)))

    # WAPE = sum(|y_true - y_pred|) / sum(y_true)
    sum_actual = float(np.sum(np.abs(y_t)))
    wape = float(np.sum(np.abs(y_t - y_p)) / max(1e-5, sum_actual)) * 100.0

    # MAPE bounded
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
