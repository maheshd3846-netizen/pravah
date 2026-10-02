"""Machine Learning Forecasters & Evaluation Package for PRAVAH.

Provides baseline time-series predictors, feature engineering pipelines,
gradient boosting quantile models, and temporal cross-validation.
"""

from ml.models.base import BaseForecastModel, ForecastOutput
from ml.baselines.moving_average import MovingAverageForecaster
from ml.baselines.seasonal_naive import SeasonalNaiveForecaster
from ml.features.feature_pipeline import FeaturePipeline, FEATURE_VERSION
from ml.xgboost.forecaster import DemandXGBForecaster, XGBForecastConfig, MODEL_VERSION
from ml.evaluation.metrics import evaluate_forecast, evaluate_quantile_forecast
from ml.evaluation.temporal_cv import TemporalCrossValidator

__all__ = [
    "BaseForecastModel",
    "ForecastOutput",
    "MovingAverageForecaster",
    "SeasonalNaiveForecaster",
    "FeaturePipeline",
    "FEATURE_VERSION",
    "DemandXGBForecaster",
    "XGBForecastConfig",
    "MODEL_VERSION",
    "evaluate_forecast",
    "evaluate_quantile_forecast",
    "TemporalCrossValidator",
]
