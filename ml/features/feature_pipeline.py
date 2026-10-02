"""Feature Engineering Pipeline for Tactical Demand Forecasting.

Extracts temporal, cyclical, weather interaction, and lag features
from multi-node synthetic logistics time series.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from typing import List, Tuple


class FeaturePipeline:
    """Transforms raw hourly demand tables into ML-ready tabular feature matrices."""

    def __init__(self, lag_hours: List[int] = None):
        self.lag_hours = lag_hours or [1, 2, 3, 24, 48, 168]
        self.feature_columns: List[str] = []

    def fit_transform(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Generates lag, rolling, and cyclical features and splits X and y."""
        data = df.sort_values(by=["node_id", "item", "timestamp_hour"]).copy()

        # Cyclical temporal encoding
        data["sin_hour"] = np.sin(2 * np.pi * data["hour_of_day"] / 24.0)
        data["cos_hour"] = np.cos(2 * np.pi * data["hour_of_day"] / 24.0)
        data["sin_day"] = np.sin(2 * np.pi * data["day_of_week"] / 7.0)
        data["cos_day"] = np.cos(2 * np.pi * data["day_of_week"] / 7.0)

        # Categorical node & item frequency or dummy encoding
        node_dummies = pd.get_dummies(data["node_id"], prefix="node", drop_first=False)
        item_dummies = pd.get_dummies(data["item"], prefix="item", drop_first=False)

        # Lag features grouped by node and item
        lag_features = []
        for lag in self.lag_hours:
            col_name = f"lag_{lag}"
            data[col_name] = data.groupby(["node_id", "item"])["requested_demand"].shift(lag)
            lag_features.append(col_name)

        # Rolling statistics
        data["rolling_mean_24"] = (
            data.groupby(["node_id", "item"])["requested_demand"]
            .shift(1)
            .rolling(24, min_periods=1)
            .mean()
        )
        data["rolling_std_24"] = (
            data.groupby(["node_id", "item"])["requested_demand"]
            .shift(1)
            .rolling(24, min_periods=1)
            .std()
            .fillna(0.0)
        )

        base_features = [
            "elevation",
            "temperature",
            "rainfall",
            "wind_speed",
            "visibility",
            "sin_hour",
            "cos_hour",
            "sin_day",
            "cos_day",
            "rolling_mean_24",
            "rolling_std_24",
        ] + lag_features

        features_df = pd.concat([data[base_features], node_dummies, item_dummies], axis=1)
        # Drop rows with NaN from lags
        valid_idx = ~features_df.isna().any(axis=1)

        X = features_df.loc[valid_idx].astype(np.float32)
        y = data.loc[valid_idx, "requested_demand"].astype(np.float32)
        self.feature_columns = list(X.columns)

        return X, y
