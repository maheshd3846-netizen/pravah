"""Base Interface and Data Structures for PRAVAH Demand Forecast Models."""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd


@dataclass
class ForecastOutput:
    p50: np.ndarray
    p80: np.ndarray
    p95: np.ndarray
    model_name: str
    model_version: str = "v1"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "p50": self.p50.tolist() if isinstance(self.p50, np.ndarray) else list(self.p50),
            "p80": self.p80.tolist() if isinstance(self.p80, np.ndarray) else list(self.p80),
            "p95": self.p95.tolist() if isinstance(self.p95, np.ndarray) else list(self.p95),
            "metadata": self.metadata,
        }


class BaseForecastModel(ABC):
    """Abstract interface that all baseline and ML forecasting models adhere to."""

    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series) -> "BaseForecastModel":
        """Fits the model on historical training features and target values."""
        pass

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> ForecastOutput:
        """Generates P50, P80, and P95 probabilistic demand forecasts."""
        pass
