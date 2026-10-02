"""Tests for Feature Engineering Pipeline and Zero Future Leakage Verification."""

import numpy as np
import pandas as pd
from ml.features.feature_pipeline import FeaturePipeline


def test_feature_pipeline_generation():
    # Construct synthetic hourly time series for 2 nodes and 1 item over 200 hours
    records = []
    for h in range(200):
        for node in ["NODE_A", "NODE_B"]:
            records.append({
                "node_id": node,
                "item": "FUEL",
                "timestamp_hour": h,
                "hour_of_day": h % 24,
                "day_of_week": (h // 24) % 7,
                "elevation": 3000.0,
                "temperature": 5.0,
                "rainfall": 0.0,
                "wind_speed": 10.0,
                "visibility": 10.0,
                "weather_severity": "NORMAL",
                "requested_demand": 10.0 + (h % 24) * 2.0,
            })
    df = pd.DataFrame(records)

    pipeline = FeaturePipeline(lag_hours=[1, 2, 24], rolling_windows=[6, 24])
    X, y = pipeline.fit_transform(df)

    assert len(X) > 0
    assert len(X) == len(y)

    # Verify presence of temporal, lag, rolling, and trend features
    expected_cols = [
        "hour", "day_of_week", "sin_hour", "cos_hour",
        "lag_1", "lag_2", "lag_24",
        "rolling_mean_6h", "rolling_mean_24h",
        "rolling_std_24h", "demand_change_1h",
    ]
    for col in expected_cols:
        assert col in X.columns


def test_no_future_leakage_and_lag_correctness():
    """Critical test: Features at index t must strictly use data from <= t-1."""
    records = []
    # Node sequence with easily verifiable sequential demands
    for h in range(50):
        records.append({
            "node_id": "NODE_TEST",
            "item": "FOOD",
            "timestamp_hour": h,
            "hour_of_day": h % 24,
            "day_of_week": (h // 24) % 7,
            "elevation": 2000.0,
            "temperature": 10.0,
            "rainfall": 0.0,
            "wind_speed": 5.0,
            "visibility": 10.0,
            "weather_severity": "NORMAL",
            "requested_demand": float(h * 10),  # h=0: 0, h=1: 10, h=2: 20, h=3: 30, ...
        })
    df = pd.DataFrame(records)

    pipeline = FeaturePipeline(lag_hours=[1, 2, 3], rolling_windows=[3])
    X, y = pipeline.fit_transform(df)

    # For any row corresponding to timestamp_hour = t:
    # y must be t * 10
    # lag_1 must be (t-1) * 10
    # lag_2 must be (t-2) * 10
    # rolling_mean_3h must be mean of [(t-1)*10, (t-2)*10, (t-3)*10]
    for idx in range(len(X)):
        target_val = y.iloc[idx]
        t = int(target_val / 10.0)

        assert X.iloc[idx]["lag_1"] == (t - 1) * 10.0
        assert X.iloc[idx]["lag_2"] == (t - 2) * 10.0
        assert X.iloc[idx]["lag_3"] == (t - 3) * 10.0

        # Rolling mean must NOT contain target_val
        expected_rolling = np.mean([(t - 1) * 10.0, (t - 2) * 10.0, (t - 3) * 10.0])
        assert abs(X.iloc[idx]["rolling_mean_3h"] - expected_rolling) < 1e-4

        # Demand change: lag_1 - lag_2
        assert X.iloc[idx]["demand_change_1h"] == 10.0
