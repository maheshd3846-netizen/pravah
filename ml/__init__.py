"""Machine Learning Forecasters & Evaluation Package for PRAVAH.

Provides baseline time-series predictors, feature engineering pipelines,
gradient boosting models, and uncertainty estimation.
"""

from ml.baselines.moving_average import MovingAverageForecaster, ExponentialSmoothingForecaster
from ml.features.feature_pipeline import FeaturePipeline
from ml.xgboost.forecaster import DemandXGBForecaster
from ml.evaluation.metrics import evaluate_forecast

__all__ = [
    "MovingAverageForecaster",
    "ExponentialSmoothingForecaster",
    "FeaturePipeline",
    "DemandXGBForecaster",
    "evaluate_forecast",
]
