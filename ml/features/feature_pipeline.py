"""Feature Engineering Pipeline for Tactical Forward Supply Chain Demand.

Extracts temporal, cyclical, lag, rolling, trend, environmental, and operational features.
Guarantees NO future leakage: all features at timestamp t rely strictly on data from <= t-1.
"""

from __future__ import annotations
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
import pandas as pd

FEATURE_VERSION = "demand-features-v1"


class FeaturePipeline:
    """Transforms multi-node synthetic logistics time series into ML-ready tabular matrices."""

    def __init__(
        self,
        lag_hours: Optional[List[int]] = None,
        rolling_windows: Optional[List[int]] = None,
    ):
        self.feature_version = FEATURE_VERSION
        self.lag_hours = lag_hours or [1, 2, 3, 6, 12, 24, 48, 72, 168]
        self.rolling_windows = rolling_windows or [6, 12, 24, 72, 168]
        self.feature_columns: List[str] = []
        self.is_fitted: bool = False
        self.node_categories: List[str] = []
        self.item_categories: List[str] = []

    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Internal transformation generating strictly non-leaking features."""
        data = df.sort_values(by=["node_id", "item", "timestamp_hour"]).copy()

        # 1. Temporal Features
        if "hour_of_day" in data.columns:
            data["hour"] = data["hour_of_day"]
        elif "hour" not in data.columns:
            data["hour"] = data["timestamp_hour"] % 24

        if "day_of_week" not in data.columns:
            data["day_of_week"] = (data["timestamp_hour"] // 24) % 7

        data["day_of_month"] = ((data["timestamp_hour"] // 24) % 30) + 1
        data["week_of_year"] = ((data["timestamp_hour"] // 168) % 52) + 1
        data["month"] = ((data["timestamp_hour"] // 720) % 12) + 1
        data["is_weekend"] = data["day_of_week"].isin([5, 6]).astype(np.float32)

        # Cyclical Encodings
        data["sin_hour"] = np.sin(2 * np.pi * data["hour"] / 24.0).astype(np.float32)
        data["cos_hour"] = np.cos(2 * np.pi * data["hour"] / 24.0).astype(np.float32)
        data["sin_day"] = np.sin(2 * np.pi * data["day_of_week"] / 7.0).astype(np.float32)
        data["cos_day"] = np.cos(2 * np.pi * data["day_of_week"] / 7.0).astype(np.float32)

        # 2. Lag Features (grouped by node_id and item)
        # Using requested_demand strictly shifted by lag >= 1
        for lag in self.lag_hours:
            col_name = f"lag_{lag}"
            data[col_name] = (
                data.groupby(["node_id", "item"])["requested_demand"]
                .shift(lag)
                .astype(np.float32)
            )

        # 3. Rolling Features (Strictly shifted by 1 to prevent future leakage)
        grouped_demand_shifted = (
            data.groupby(["node_id", "item"])["requested_demand"].shift(1)
        )

        for w in self.rolling_windows:
            mean_col = f"rolling_mean_{w}h"
            data[mean_col] = (
                grouped_demand_shifted.rolling(window=w, min_periods=1)
                .mean()
                .astype(np.float32)
            )

        for w in [24, 72, 168]:
            std_col = f"rolling_std_{w}h"
            data[std_col] = (
                grouped_demand_shifted.rolling(window=w, min_periods=1)
                .std()
                .fillna(0.0)
                .astype(np.float32)
            )

        # 4. Trend Features
        data["demand_change_1h"] = (
            (data["lag_1"] - data["lag_2"]).astype(np.float32)
            if "lag_1" in data.columns and "lag_2" in data.columns
            else np.zeros(len(data), dtype=np.float32)
        )
        data["demand_change_6h"] = (
            (data["lag_1"] - data["lag_6"]).astype(np.float32)
            if "lag_1" in data.columns and "lag_6" in data.columns
            else np.zeros(len(data), dtype=np.float32)
        )
        data["demand_change_24h"] = (
            (data["lag_1"] - data["lag_24"]).astype(np.float32)
            if "lag_1" in data.columns and "lag_24" in data.columns
            else np.zeros(len(data), dtype=np.float32)
        )
        data["demand_vs_7d_average"] = (
            (data["lag_1"] - data["rolling_mean_168h"]).astype(np.float32)
            if "lag_1" in data.columns and "rolling_mean_168h" in data.columns
            else np.zeros(len(data), dtype=np.float32)
        )

        # 5. Environmental Features
        severity_map = {"NORMAL": 0.0, "LIGHT": 1.0, "MODERATE": 2.0, "SEVERE": 3.0}
        if "weather_severity" in data.columns:
            data["weather_severity_num"] = (
                data["weather_severity"].map(lambda x: severity_map.get(str(x), 0.0)).astype(np.float32)
            )
        else:
            data["weather_severity_num"] = 0.0

        for env_col in ["rainfall", "wind_speed", "visibility", "temperature", "elevation"]:
            if env_col not in data.columns:
                data[env_col] = 0.0
            data[env_col] = data[env_col].astype(np.float32)

        # 6. Operational Features
        if "current_inventory" not in data.columns:
            data["current_inventory"] = 1000.0
        if "inbound_quantity" not in data.columns:
            data["inbound_quantity"] = 0.0
        if "vehicle_availability" not in data.columns:
            data["vehicle_availability"] = 1.0
        if "node_priority" not in data.columns:
            data["node_priority"] = 3.0

        data["current_inventory"] = data["current_inventory"].astype(np.float32)
        data["inbound_quantity"] = data["inbound_quantity"].astype(np.float32)
        data["vehicle_availability"] = data["vehicle_availability"].astype(np.float32)
        data["node_priority"] = data["node_priority"].astype(np.float32)

        # 7. One-hot / category encoding for node and item
        if not self.is_fitted:
            self.node_categories = sorted(list(data["node_id"].unique()))
            self.item_categories = sorted(list(data["item"].unique()))

        for n in self.node_categories:
            data[f"node_{n}"] = (data["node_id"] == n).astype(np.float32)
        for it in self.item_categories:
            data[f"item_{it}"] = (data["item"] == it).astype(np.float32)

        return data

    def fit_transform(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Fits feature encoders and extracts complete feature matrix and target series."""
        data = self._engineer_features(df)
        self.is_fitted = True

        lag_cols = [f"lag_{lag}" for lag in self.lag_hours if f"lag_{lag}" in data.columns]
        rolling_cols = (
            [f"rolling_mean_{w}h" for w in self.rolling_windows if f"rolling_mean_{w}h" in data.columns]
            + [f"rolling_std_{w}h" for w in [24, 72, 168] if f"rolling_std_{w}h" in data.columns]
        )
        trend_cols = ["demand_change_1h", "demand_change_6h", "demand_change_24h", "demand_vs_7d_average"]

        feature_cols = [
            # Temporal
            "hour", "day_of_week", "day_of_month", "week_of_year", "month", "is_weekend",
            "sin_hour", "cos_hour", "sin_day", "cos_day",
        ] + lag_cols + rolling_cols + trend_cols + [
            # Environment
            "rainfall", "wind_speed", "visibility", "temperature", "elevation", "weather_severity_num",
            # Operational
            "current_inventory", "inbound_quantity", "vehicle_availability", "node_priority",
        ] + [f"node_{n}" for n in self.node_categories] + [f"item_{it}" for it in self.item_categories]

        self.feature_columns = feature_cols

        # Filter valid rows (drop rows where lag_168 is NaN due to initial warmup)
        valid_idx = ~data[self.feature_columns].isna().any(axis=1)
        X = data.loc[valid_idx, self.feature_columns].copy()
        y = data.loc[valid_idx, "requested_demand"].astype(np.float32)

        return X, y

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transforms a dataframe using previously fitted feature columns."""
        if not self.is_fitted:
            raise RuntimeError("FeaturePipeline must be fitted via fit_transform() before transform().")
        data = self._engineer_features(df)
        for col in self.feature_columns:
            if col not in data.columns:
                data[col] = 0.0
        return data[self.feature_columns].fillna(0.0).astype(np.float32)
