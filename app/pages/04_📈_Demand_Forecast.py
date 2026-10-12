"""
app/pages/04_📈_Demand_Forecast.py
Machine Learning and statistical demand forecasting engine with multi-model comparison.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
APP_DIR = PROJECT_ROOT / "app"

for p in [str(PROJECT_ROOT), str(SRC_DIR), str(APP_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

try:
    from app.components.ui import inject_custom_css, render_metric_card, format_number
    from app.data_loader import load_all_data
except ImportError:
    from components.ui import inject_custom_css, render_metric_card, format_number
    from data_loader import load_all_data

from forecasting.models import prepare_daily_series, train_test_split_series, forecast_moving_average, forecast_exponential_smoothing, forecast_xgboost, evaluate_forecast

st.set_page_config(page_title="Demand Forecast", page_icon="📈", layout="wide")
inject_custom_css()

data = load_all_data()
products_df = data["products"]
demand_df = data["demand"]
forecast_comp_df = data["forecast_comparison"]
best_forecast_df = data["best_forecast"]

st.title("📈 Machine Learning Demand Forecasting")
st.markdown("Compare baseline moving averages, Holt-Winters exponential smoothing, and gradient-boosted trees (XGBoost) across a 30-day holdout evaluation horizon.")

# Plain-English User Guide Callout
st.markdown("""
    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-left: 4px solid #2563EB; border-radius: 8px; padding: 12px 16px; margin-bottom: 20px;">
        <span style="font-weight: 700; color: #1E293B;">💡 How to Use This Forecast:</span>
        <span style="color: #475569; font-size: 0.92rem; margin-left: 6px;">
            The solid dark line shows actual historical customer demand. The <b>vibrant blue line</b> shows AI predicted orders for the next 30 days. The <b>light blue shaded band</b> indicates the 90% confidence range to help inventory planners set realistic safety buffers.
        </span>
    </div>
""", unsafe_allow_html=True)

# Product Selector
prod_options = products_df["product_id"].tolist()
selected_pid = st.selectbox(
    "Select Product to Forecast:",
    prod_options,
    format_func=lambda pid: f"{pid} - {products_df.loc[products_df['product_id']==pid, 'product_name'].values[0]} ({products_df.loc[products_df['product_id']==pid, 'category'].values[0]})"
)

@st.cache_data(show_spinner="Fitting moving average, Holt-Winters & XGBoost models...")
def compute_product_forecast(pid: str):
    daily_s = prepare_daily_series(demand_df, pid)
    train_s, test_s = train_test_split_series(daily_s, test_days=30)
    h = len(test_s)
    ma_p = forecast_moving_average(train_s, horizon=h)
    es_p = forecast_exponential_smoothing(train_s, horizon=h)
    xgb_p, xgb_i = forecast_xgboost(train_s, test_s)
    ma_e = evaluate_forecast(test_s.values, ma_p)
    es_e = evaluate_forecast(test_s.values, es_p)
    xgb_e = evaluate_forecast(test_s.loc[xgb_i].values, xgb_p)
    return train_s, test_s, ma_p, es_p, xgb_p, xgb_i, ma_e, es_e, xgb_e

# Run cached interactive forecast generation for selected product
train_series, test_series, ma_preds, es_preds, xgb_preds, xgb_idx, ma_eval, es_eval, xgb_eval = compute_product_forecast(selected_pid)

# Best model for this product from processed comparison
best_model_name = "XGBoost"
if selected_pid in best_forecast_df["product_id"].values:
    best_row = best_forecast_df[best_forecast_df["product_id"] == selected_pid].iloc[0]
    best_model_name = best_row.get("best_model", best_row.get("model", "XGBoost"))

# Top KPI comparison cards for selected product
c1, c2, c3, c4 = st.columns(4)

best_accuracy = 100.0 - min(xgb_eval["MAPE"], es_eval["MAPE"], ma_eval["MAPE"])
total_forecast_30d = (xgb_preds.sum() if best_model_name == "XGBoost" else es_preds.sum())

with c1:
    render_metric_card("Recommended AI Model", f"{best_model_name}", "Lowest error on holdout data")
with c2:
    render_metric_card("Forecast Accuracy", f"{best_accuracy:.1f}%", f"Error rate: {100-best_accuracy:.1f}%")
with c3:
    render_metric_card("Expected 30-Day Demand", f"{total_forecast_30d:,.0f} Units", "Total predicted customer sales")
with c4:
    render_metric_card("Avg Daily Sales Pace", f"{test_series.mean():,.0f} Units/day", f"Max peak: {test_series.max():,.0f} units")

st.markdown("---")

# Forecast Time Series Visualizer
st.subheader(f"📊 30-Day Forecast Trajectory vs Actual Demand ({selected_pid})")

# Tail history of last 60 days for clean chart
history_tail = train_series.tail(60)

fig_fc = go.Figure()

# Actual History
fig_fc.add_trace(go.Scatter(
    x=history_tail.index,
    y=history_tail.values,
    mode="lines",
    name="Historical Demand (Train)",
    line=dict(color="#64748B", width=1.8),
    hovertemplate="Date: %{x|%Y-%m-%d}<br>Demand: %{y:,.0f} units<extra></extra>"
))

# Test Actuals
fig_fc.add_trace(go.Scatter(
    x=test_series.index,
    y=test_series.values,
    mode="lines+markers",
    name="Actual Demand (Holdout)",
    line=dict(color="#0F172A", width=2.5),
    marker=dict(size=4, color="#0F172A"),
    hovertemplate="Date: %{x|%Y-%m-%d}<br>Actual: %{y:,.0f} units<extra></extra>"
))

# Confidence Interval for Recommended Model
ci_rmse = xgb_eval["RMSE"] if best_model_name == "XGBoost" else es_eval["RMSE"]
ci_center = xgb_preds if best_model_name == "XGBoost" else es_preds
ci_dates = xgb_idx if best_model_name == "XGBoost" else test_series.index
ci_upper = ci_center + 1.645 * ci_rmse
ci_lower = np.maximum(0, ci_center - 1.645 * ci_rmse)

fig_fc.add_trace(go.Scatter(
    x=ci_dates,
    y=ci_upper,
    mode="lines",
    line=dict(width=0),
    showlegend=False,
    hoverinfo="skip"
))
fig_fc.add_trace(go.Scatter(
    x=ci_dates,
    y=ci_lower,
    mode="lines",
    line=dict(width=0),
    fill="tonexty",
    fillcolor="rgba(37, 99, 235, 0.15)",
    name="90% Forecast Confidence Band",
    hoverinfo="skip"
))

# XGBoost
fig_fc.add_trace(go.Scatter(
    x=xgb_idx,
    y=xgb_preds,
    mode="lines+markers",
    name="XGBoost (ML Lags + Trends)",
    line=dict(color="#2563EB", width=2.5),
    marker=dict(size=4),
    hovertemplate="Date: %{x|%Y-%m-%d}<br>XGBoost Forecast: %{y:,.1f} units<extra></extra>"
))

# Exponential Smoothing
fig_fc.add_trace(go.Scatter(
    x=test_series.index,
    y=es_preds,
    mode="lines",
    name="Holt-Winters Exp Smoothing",
    line=dict(color="#8B5CF6", width=2, dash="dash"),
    hovertemplate="Date: %{x|%Y-%m-%d}<br>Exp Smoothing: %{y:,.1f} units<extra></extra>"
))

# Moving Average
fig_fc.add_trace(go.Scatter(
    x=test_series.index,
    y=ma_preds,
    mode="lines",
    name="Moving Average (7-day)",
    line=dict(color="#F59E0B", width=1.8, dash="dot"),
    hovertemplate="Date: %{x|%Y-%m-%d}<br>Moving Avg: %{y:,.1f} units<extra></extra>"
))

# Cutoff line
split_date = test_series.index[0]
fig_fc.add_vline(x=split_date, line_dash="dash", line_color="#EF4444", opacity=0.7, annotation_text="Forecast Horizon Start", annotation_position="top left")

fig_fc.update_layout(
    template="plotly_white",
    height=450,
    margin=dict(l=20, r=20, t=30, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)),
    xaxis_title="Timeline",
    yaxis_title="Daily Network Demand (Units)"
)
st.plotly_chart(fig_fc, use_container_width=True)

# Performance Comparison Table for Product & Overall Summary
col_t1, col_t2 = st.columns([5, 7])

with col_t1:
    st.subheader("🎯 Model Error Comparison (Holdout)")
    eval_table = pd.DataFrame([
        {"Model": "XGBoost", "MAE": xgb_eval["MAE"], "RMSE": xgb_eval["RMSE"], "MAPE (%)": xgb_eval["MAPE"]},
        {"Model": "Exponential Smoothing", "MAE": es_eval["MAE"], "RMSE": es_eval["RMSE"], "MAPE (%)": es_eval["MAPE"]},
        {"Model": "Moving Average (7-day)", "MAE": ma_eval["MAE"], "RMSE": ma_eval["RMSE"], "MAPE (%)": ma_eval["MAPE"]},
    ]).sort_values("MAPE (%)")
    st.dataframe(eval_table.style.format({"MAE": "{:.2f}", "RMSE": "{:.2f}", "MAPE (%)": "{:.2f}%"}), use_container_width=True, hide_index=True)

with col_t2:
    st.subheader("🏆 Network-Wide Average Model Leaderboard")
    
    # Check column casing in forecast_comp_df
    fc_cols = {col.lower(): col for col in forecast_comp_df.columns}
    mae_c = fc_cols.get("mae", "MAE")
    rmse_c = fc_cols.get("rmse", "RMSE")
    mape_c = fc_cols.get("mape", "MAPE")
    
    overall_board = forecast_comp_df.groupby("model")[[mae_c, rmse_c, mape_c]].mean().reset_index()
    overall_board.columns = ["Model", "Avg MAE", "Avg RMSE", "Avg MAPE (%)"]
    overall_board = overall_board.sort_values("Avg MAPE (%)")
    st.dataframe(overall_board.style.format({"Avg MAE": "{:.2f}", "Avg RMSE": "{:.2f}", "Avg MAPE (%)": "{:.2f}%"}), use_container_width=True, hide_index=True)
