"""
tests/test_forecasting.py
Unit tests for time-series forecasting models and error metrics.
"""

import pytest
import pandas as pd
import numpy as np
from src.forecasting.models import (
    prepare_daily_series,
    train_test_split_series,
    forecast_moving_average,
    forecast_exponential_smoothing,
    build_features_for_xgboost,
    forecast_xgboost,
    evaluate_forecast
)


def test_prepare_daily_series():
    dates = pd.date_range("2026-01-01", periods=10, freq="D")
    demand_df = pd.DataFrame({
        "date_id": dates.astype(str),
        "product_id": ["P001"] * 10,
        "demand_quantity": [10, 20, 15, 30, 25, 40, 35, 50, 45, 60]
    })

    series = prepare_daily_series(demand_df, "P001")
    assert len(series) == 10
    assert series.iloc[0] == 10
    assert series.iloc[-1] == 60


def test_evaluate_forecast():
    actual = np.array([100.0, 200.0, 300.0])
    predicted = np.array([110.0, 190.0, 300.0])

    metrics = evaluate_forecast(actual, predicted)
    assert "MAE" in metrics
    assert "RMSE" in metrics
    assert "MAPE" in metrics
    assert metrics["MAE"] == pytest.approx(20.0 / 3.0, 0.01)


def test_forecast_moving_average():
    train = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0])
    preds = forecast_moving_average(train, horizon=3, window=7)
    assert len(preds) == 3
    assert preds[0] == 40.0 # mean of 10..70 is 40


def test_xgboost_features():
    dates = pd.date_range("2026-01-01", periods=30, freq="D")
    series = pd.Series(np.arange(30, dtype=float), index=dates)
    features_df = build_features_for_xgboost(series)
    assert not features_df.empty
    assert "lag_1" in features_df.columns
    assert "rolling_mean_7" in features_df.columns
    assert "day_of_week" in features_df.columns
