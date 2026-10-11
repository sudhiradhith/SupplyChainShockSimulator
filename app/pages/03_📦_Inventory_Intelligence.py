"""
app/pages/03_📦_Inventory_Intelligence.py
Inventory health, stockout exposure, Days of Inventory (DOI), and reorder policy intelligence.
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

try:
    from app.components.ui import inject_custom_css, render_metric_card, format_currency, format_number
    from app.data_loader import load_all_data
except ImportError:
    from components.ui import inject_custom_css, render_metric_card, format_currency, format_number
    from data_loader import load_all_data

st.set_page_config(page_title="Inventory Intelligence", page_icon="📦", layout="wide")
inject_custom_css()

data = load_all_data()
products_df = data["products"]
inv_summary_df = data["inventory_summary"]
inv_df = data["inventory"]
warehouses_df = data["warehouses"]

st.title("📦 Inventory Intelligence & Stockout Exposure")
st.markdown("Monitor inventory turns, days of inventory (DOI), safety stock buffers, and reorder point (ROP) compliance across the network.")

# Plain-English Guide Callout
low_stock_items = inv_summary_df[inv_summary_df["days_of_inventory"] < 14]["product_id"].tolist()
st.markdown(f"""
    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-left: 4px solid #2563EB; border-radius: 8px; padding: 12px 16px; margin-bottom: 20px;">
        <span style="font-weight: 700; color: #1E293B;">💡 Inventory Health Takeaway:</span>
        <span style="color: #475569; font-size: 0.92rem; margin-left: 6px;">
            The network holds an average buffer of <b>{inv_summary_df['days_of_inventory'].mean():.1f} days</b> of supply. 
            <b>{len(low_stock_items)} critical SKUs</b> hold less than 14 days of stock and are at imminent risk if supplier shipments face minor customs or transit delays.
        </span>
    </div>
""", unsafe_allow_html=True)

# Top KPIs
c1, c2, c3, c4 = st.columns(4)

avg_doi = inv_summary_df["days_of_inventory"].mean()
low_stock_count = len(inv_summary_df[inv_summary_df["days_of_inventory"] < 14])
turnover_col = "turnover_ratio" if "turnover_ratio" in inv_summary_df.columns else "inventory_turnover"
avg_turnover = inv_summary_df[turnover_col].mean() if turnover_col in inv_summary_df.columns else 5.2
total_safety_stock = inv_summary_df["safety_stock"].sum()

with c1:
    render_metric_card("Avg Stock Buffer", f"{avg_doi:.1f} Days", "Days before stockout")
with c2:
    render_metric_card("Low Buffer SKUs", f"{low_stock_count} SKUs", "Buffer < 14 days", delta_color="danger" if low_stock_count > 0 else "normal")
with c3:
    render_metric_card("Annual Inventory Turns", f"{avg_turnover:.1f}x", "Sales velocity")
with c4:
    render_metric_card("Network Safety Cushion", f"{total_safety_stock:,.0f} Units", "95% Service Level target")

st.markdown("---")

# Visualizations: DOI by Product & Stock Status
col_chart1, col_chart2 = st.columns([7, 5])

# Merge product details
inv_enriched = inv_summary_df.merge(products_df[["product_id", "product_name", "category"]], on="product_id", how="left")
inv_enriched = inv_enriched.sort_values("days_of_inventory", ascending=True)

with col_chart1:
    st.subheader("📊 Days of Inventory (DOI) per SKU")

    fig_bar = px.bar(
        inv_enriched,
        x="days_of_inventory",
        y="product_name",
        orientation="h",
        color="days_of_inventory",
        color_continuous_scale=["#EF4444", "#F59E0B", "#10B981"],
        labels={"days_of_inventory": "Days of Inventory (DOI)", "product_name": "Product"},
        template="plotly_white",
        height=450
    )
    fig_bar.add_vline(x=7, line_dash="dash", line_color="#EF4444", annotation_text="Critical Threshold (7d)")
    fig_bar.update_layout(margin=dict(l=20, r=20, t=20, b=20), coloraxis_showscale=False)
    st.plotly_chart(fig_bar, use_container_width=True)

with col_chart2:
    st.subheader("🏢 Stock Position vs Reorder Point (ROP)")
    st.caption("Benchmark inventory buffer against Reorder Point and Safety Stock threshold.")

    inv_val_col = "avg_inventory" if "avg_inventory" in inv_enriched.columns else "closing_inventory"

    fig_rop = go.Figure()
    fig_rop.add_trace(go.Bar(
        x=inv_enriched["product_id"],
        y=inv_enriched[inv_val_col],
        name="Average Stock",
        marker_color="#2563EB",
        hovertemplate="SKU: %{x}<br>Stock: %{y:,.0f} units<extra></extra>"
    ))
    fig_rop.add_trace(go.Bar(
        x=inv_enriched["product_id"],
        y=inv_enriched["reorder_point"],
        name="Reorder Point (ROP)",
        marker_color="#F59E0B",
        hovertemplate="SKU: %{x}<br>ROP: %{y:,.0f} units<extra></extra>"
    ))
    fig_rop.add_trace(go.Bar(
        x=inv_enriched["product_id"],
        y=inv_enriched["safety_stock"],
        name="Safety Stock (95%)",
        marker_color="#10B981",
        hovertemplate="SKU: %{x}<br>Safety Stock: %{y:,.0f} units<extra></extra>"
    ))
    fig_rop.update_layout(
        barmode="group",
        template="plotly_white",
        height=450,
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)),
        xaxis_title="Product SKU",
        yaxis_title="Units"
    )
    st.plotly_chart(fig_rop, use_container_width=True)

# Master Inventory Summary Table
st.subheader("📋 Master Inventory Intelligence Table")

display_cols = [c for c in [
    "product_id", "product_name", "category", inv_val_col,
    "avg_daily_demand", "days_of_inventory", "safety_stock", "reorder_point", turnover_col
] if c in inv_enriched.columns]

disp_table = inv_enriched[display_cols].rename(columns={
    "product_id": "SKU",
    "product_name": "Product Name",
    "category": "Category",
    inv_val_col: "Inventory Stock",
    "avg_daily_demand": "Avg Daily Demand",
    "days_of_inventory": "DOI (Days)",
    "safety_stock": "Safety Stock (95%)",
    "reorder_point": "ROP",
    turnover_col: "Turns / Yr"
})

st.dataframe(
    disp_table.style.format({
        "Inventory Stock": "{:,.0f}",
        "Avg Daily Demand": "{:,.1f}",
        "DOI (Days)": "{:.1f} d",
        "Safety Stock (95%)": "{:,.0f}",
        "ROP": "{:,.0f}",
        "Turns / Yr": "{:.2f}x"
    }),
    use_container_width=True,
    hide_index=True
)
