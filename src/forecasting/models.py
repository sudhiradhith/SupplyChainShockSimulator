"""
Demand Forecasting Module
Three models: Moving Average, Exponential Smoothing, XGBoost.
Compared on MAE, RMSE, MAPE. Best model selected per product.
"""

import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import xgboost as xgb


def prepare_daily_series(demand_df: pd.DataFrame, product_id: str) -> pd.Series:
    """
    Aggregate demand for one product across all warehouses into a
    single daily time series, indexed by date.
    """
    product_demand = demand_df[demand_df["product_id"] == product_id].copy()
    daily = product_demand.groupby("date_id")["demand_quantity"].sum().sort_index()
    daily.index = pd.to_datetime(daily.index)
    daily = daily.asfreq("D").ffill()  # fill any gap days
    return daily


def train_test_split_series(series: pd.Series, test_days: int = 30):
    train = series.iloc[:-test_days]
    test = series.iloc[-test_days:]
    return train, test


def forecast_moving_average(train: pd.Series, horizon: int, window: int = 7) -> np.ndarray:
    """Simple moving average: repeat the last `window`-day average forward."""
    avg = train.tail(window).mean()
    return np.full(horizon, avg)


def forecast_exponential_smoothing(train: pd.Series, horizon: int) -> np.ndarray:
    """Holt-Winters exponential smoothing with weekly seasonality."""
    model = ExponentialSmoothing(
        train, trend="add", seasonal="add", seasonal_periods=7
    ).fit()
    forecast = model.forecast(horizon)
    return forecast.values


def build_features_for_xgboost(series: pd.Series) -> pd.DataFrame:
    """Create lag + calendar features for XGBoost."""
    df = series.to_frame("demand")
    df["day_of_week"] = df.index.dayofweek
    df["day_of_month"] = df.index.day
    df["month"] = df.index.month
    for lag in [1, 2, 3, 7, 14]:
        df[f"lag_{lag}"] = df["demand"].shift(lag)
    df["rolling_mean_7"] = df["demand"].shift(1).rolling(7).mean()
    return df.dropna()


def forecast_xgboost(train: pd.Series, test: pd.Series) -> np.ndarray:
    """
    XGBoost using lag/calendar features. Trains on train set,
    predicts iteratively over the test horizon.
    """
    full_series = pd.concat([train, test])
    features_df = build_features_for_xgboost(full_series)

    train_features = features_df.loc[features_df.index.isin(train.index)]
    test_features = features_df.loc[features_df.index.isin(test.index)]

    X_train = train_features.drop(columns=["demand"])
    y_train = train_features["demand"]
    X_test = test_features.drop(columns=["demand"])

    model = xgb.XGBRegressor(n_estimators=200, max_depth=4, learning_rate=0.05, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    return preds, test_features.index


def evaluate_forecast(actual: np.ndarray, predicted: np.ndarray) -> dict:
    mae = mean_absolute_error(actual, predicted)
    rmse = np.sqrt(mean_squared_error(actual, predicted))
    mape = np.mean(np.abs((actual - predicted) / np.where(actual == 0, np.nan, actual))) * 100
    return {"MAE": mae, "RMSE": rmse, "MAPE": mape}


def compare_models_for_product(demand_df: pd.DataFrame, product_id: str, test_days: int = 30) -> dict:
    """
    Runs all three models for one product, returns metrics + predictions
    so you can pick the best model per product (or overall).
    """
    series = prepare_daily_series(demand_df, product_id)
    if len(series) < test_days + 30:
        return None  # not enough history to evaluate reliably

    train, test = train_test_split_series(series, test_days)

    ma_pred = forecast_moving_average(train, horizon=test_days)
    es_pred = forecast_exponential_smoothing(train, horizon=test_days)
    xgb_pred, xgb_index = forecast_xgboost(train, test)

    results = {
        "product_id": product_id,
        "Moving Average": evaluate_forecast(test.values, ma_pred),
        "Exponential Smoothing": evaluate_forecast(test.values, es_pred),
        "XGBoost": evaluate_forecast(test.reindex(xgb_index).values, xgb_pred),
    }
    return results