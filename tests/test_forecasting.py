"""Tests for Baseline Models, XGBoost Quantile Forecaster, and Validation."""

import numpy as np
import pandas as pd

from ml.features.feature_pipeline import FeaturePipeline
from ml.baselines.moving_average import MovingAverageForecaster
from ml.baselines.seasonal_naive import SeasonalNaiveForecaster
from ml.xgboost.forecaster import DemandXGBForecaster, XGBForecastConfig
from ml.evaluation.metrics import evaluate_quantile_forecast
from ml.evaluation.temporal_cv import TemporalCrossValidator


def _generate_synthetic_demand_data(n_hours: int = 500) -> pd.DataFrame:
    records = []
    for h in range(n_hours):
        for node in ["FP-01", "FP-02"]:
            # Daily sinusoidal demand with diurnal cycle
            d = 30.0 + 15.0 * np.sin(2 * np.pi * (h % 24) / 24.0) + (h % 7) * 2.0
            records.append({
                "node_id": node,
                "item": "FUEL",
                "timestamp_hour": h,
                "hour_of_day": h % 24,
                "day_of_week": (h // 24) % 7,
                "elevation": 3500.0,
                "temperature": -8.0,
                "rainfall": 0.0,
                "wind_speed": 15.0,
                "visibility": 8.0,
                "weather_severity": "NORMAL",
                "requested_demand": float(max(5.0, d)),
            })
    return pd.DataFrame(records)


def test_baseline_forecasters():
    df = _generate_synthetic_demand_data(300)
    pipeline = FeaturePipeline(lag_hours=[1, 24, 168], rolling_windows=[6, 24])
    X, y = pipeline.fit_transform(df)

    # Test Moving Average Baseline
    ma = MovingAverageForecaster()
    ma.fit(X, y)
    out_ma = ma.predict(X)

    assert len(out_ma.p50) == len(X)
    assert len(out_ma.p80) == len(X)
    assert len(out_ma.p95) == len(X)
    # Check monotonicity
    assert np.all(out_ma.p50 <= out_ma.p80 + 1e-4)
    assert np.all(out_ma.p80 <= out_ma.p95 + 1e-4)

    # Test Seasonal Naive Baseline
    snaive = SeasonalNaiveForecaster(primary_col="lag_24")
    snaive.fit(X, y)
    out_snaive = snaive.predict(X)

    assert len(out_snaive.p50) == len(X)
    assert np.all(out_snaive.p50 <= out_snaive.p80 + 1e-4)
    assert np.all(out_snaive.p80 <= out_snaive.p95 + 1e-4)


def test_xgboost_quantile_forecaster_monotonicity():
    df = _generate_synthetic_demand_data(300)
    pipeline = FeaturePipeline(lag_hours=[1, 2, 24], rolling_windows=[6, 24])
    X, y = pipeline.fit_transform(df)

    cfg = XGBForecastConfig(n_estimators=30, max_depth=3, random_state=42)
    xgb_forecaster = DemandXGBForecaster(config=cfg)
    xgb_forecaster.fit(X, y)

    out = xgb_forecaster.predict(X)

    # Monotonicity test: P50 <= P80 <= P95 for all samples
    diff_80_50 = out.p80 - out.p50
    diff_95_80 = out.p95 - out.p80

    assert np.all(diff_80_50 >= 0.0), "P80 must be >= P50"
    assert np.all(diff_95_80 >= 0.0), "P95 must be >= P80"

    # Feature importance retrieval
    importances = xgb_forecaster.get_feature_importances(top_k=5)
    assert len(importances) > 0
    assert "feature" in importances[0]
    assert "importance" in importances[0]


def test_quantile_evaluation_metrics():
    y_true = np.array([20.0, 25.0, 30.0, 35.0, 40.0])
    p50 = np.array([20.0, 24.0, 29.0, 34.0, 41.0])
    p80 = np.array([24.0, 28.0, 33.0, 38.0, 45.0])
    p95 = np.array([28.0, 32.0, 38.0, 42.0, 50.0])

    metrics = evaluate_quantile_forecast(y_true, p50, p80, p95, model_name="test_model", horizon_hours=24)

    assert "mae" in metrics
    assert "rmse" in metrics
    assert "wape_percent" in metrics
    assert "p50_coverage_percent" in metrics
    assert "p80_coverage_percent" in metrics
    assert "p95_coverage_percent" in metrics

    assert 0.0 <= metrics["p50_coverage_percent"] <= 100.0
    assert metrics["p95_coverage_percent"] == 100.0  # all actuals are <= p95


def test_chronological_cross_validation_split():
    # 8 months of data: 8 * 100 hours
    records = []
    for h in range(800):
        records.append({
            "node_id": "FP-01",
            "item": "FUEL",
            "timestamp_hour": h,
            "hour_of_day": h % 24,
            "day_of_week": (h // 24) % 7,
            "elevation": 3000.0,
            "temperature": 0.0,
            "rainfall": 0.0,
            "wind_speed": 10.0,
            "visibility": 10.0,
            "weather_severity": "NORMAL",
            "requested_demand": 20.0 + (h % 24),
        })
    df = pd.DataFrame(records)

    # Use 100 hours per "month" for test
    cv = TemporalCrossValidator(month_hours=100, initial_train_months=4, n_splits=3)
    folds = list(cv.split(df))

    assert len(folds) == 3

    # Fold 1: train < 400, test 400-500
    train1, test1, idx1 = folds[0]
    assert idx1 == 1
    assert train1["timestamp_hour"].max() < 400
    assert test1["timestamp_hour"].min() >= 400
    assert test1["timestamp_hour"].max() < 500

    # Fold 2: train < 500, test 500-600
    train2, test2, idx2 = folds[1]
    assert idx2 == 2
    assert train2["timestamp_hour"].max() < 500
    assert test2["timestamp_hour"].min() >= 500
