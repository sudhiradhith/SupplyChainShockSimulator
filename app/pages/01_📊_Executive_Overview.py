"""
app/pages/01_📊_Executive_Overview.py
Strategic executive dashboard summarizing network health, supplier vulnerability, and disruption exposure.
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
    from app.components.ui import inject_custom_css, render_metric_card, format_currency, format_number, get_risk_badge
    from app.data_loader import load_all_data
except ImportError:
    from components.ui import inject_custom_css, render_metric_card, format_currency, format_number, get_risk_badge
    from data_loader import load_all_data

st.set_page_config(page_title="Executive Overview", page_icon="📊", layout="wide")
inject_custom_css()

data = load_all_data()
suppliers_df = data["suppliers"]
products_df = data["products"]
risk_df = data["supplier_risk"]
inv_summary_df = data["inventory_summary"]
mc_df = data["monte_carlo_summary"]
shipments_df = data["shipments"]

st.title("📊 Executive Control Tower")
st.markdown("High-level visibility into supply chain network vulnerability, supplier exposure, and operational readiness.")

# Calculate summary KPI variables
total_annual_shipments = len(shipments_df)
crit_count = len(risk_df[risk_df["risk_band"] == "CRITICAL"])
high_count = len(risk_df[risk_df["risk_band"] == "HIGH"])
worst_case_exposure = mc_df["worst_case_revenue_loss"].sum()
total_expected_exposure = mc_df["expected_revenue_loss"].sum()
crit_list = risk_df[risk_df["risk_band"] == "CRITICAL"]["supplier_name"].tolist()
high_list = risk_df[risk_df["risk_band"] == "HIGH"]["supplier_name"].tolist()

# Plain-English Executive Summary Callout
st.markdown(f"""
    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-left: 4px solid #2563EB; border-radius: 8px; padding: 12px 16px; margin-bottom: 20px;">
        <span style="font-weight: 700; color: #1E293B;">💡 Executive Takeaway:</span>
        <span style="color: #475569; font-size: 0.92rem; margin-left: 6px;">
            The platform monitors 20 global suppliers. Currently, <b>2 suppliers ({", ".join(crit_list)})</b> are in the <b>CRITICAL RISK</b> category due to frequent delays and single-sourced critical components. A major disruption could risk up to <b>{format_currency(worst_case_exposure)}</b> in extreme worst-case revenue loss.
        </span>
    </div>
""", unsafe_allow_html=True)

# Top KPIs
col1, col2, col3, col4 = st.columns(4)

with col1:
    render_metric_card("Network Suppliers", f"{len(suppliers_df)} Total", f"{crit_count} Critical | {high_count} High Risk", delta_color="danger" if crit_count > 0 else "normal")

with col2:
    render_metric_card("Tracked Shipments", f"{total_annual_shipments:,}", "Historical delivery log")

with col3:
    render_metric_card("Expected Revenue at Risk", format_currency(total_expected_exposure), "Average disruption loss")

with col4:
    render_metric_card("Worst-Case Shock Exposure", format_currency(worst_case_exposure), "95th Percentile severe crisis", delta_color="danger")

st.markdown("---")

# Row 2: Visualizations (Supplier Risk vs Exposure Scatter + Risk Distribution)
col_left, col_right = st.columns([7, 5])

# Merge risk score with MC expected loss
merged_risk_mc = risk_df.merge(mc_df, on="supplier_id", how="left")
avg_loss = merged_risk_mc["expected_revenue_loss"].mean()

with col_left:
    st.subheader("🎯 Disruption Vulnerability Matrix (Risk vs Revenue Loss)")
    st.caption("Suppliers in the upper-right quadrant represent priority strategic vulnerabilities.")

    fig_scatter = px.scatter(
        merged_risk_mc,
        x="supplier_risk_score",
        y="expected_revenue_loss",
        size="worst_case_revenue_loss",
        color="risk_band",
        hover_name="supplier_name",
        hover_data={"supplier_id": True, "stockout_probability": True, "supplier_risk_score": ":.1f", "expected_revenue_loss": ":.2f", "worst_case_revenue_loss": ":.2f"},
        color_discrete_map={"LOW": "#10B981", "MEDIUM": "#F59E0B", "HIGH": "#EA580C", "CRITICAL": "#DC2626"},
        labels={"supplier_risk_score": "Composite Risk Score (0-100)", "expected_revenue_loss": "Expected Revenue at Risk (₹)"},
        template="plotly_white",
        size_max=22,
        height=400
    )
    fig_scatter.update_traces(
        marker=dict(line=dict(width=1.5, color='#0F172A'), opacity=0.88),
        hovertemplate="<b>%{hovertext}</b> (%{customdata[0]})<br>" +
                      "Risk Band: %{marker.color}<br>" +
                      "Composite Risk: %{x:.1f} / 100<br>" +
                      "Stockout Probability: %{customdata[1]}%<br>" +
                      "Expected Revenue Loss: ₹%{y:,.0f}<br>" +
                      "Worst-Case P95 Shock: ₹%{customdata[4]:,.0f}<extra></extra>"
    )
    # Add quadrant reference lines
    fig_scatter.add_vline(x=50, line_dash="dash", line_color="#94A3B8", opacity=0.6, annotation_text="Median Risk (50)", annotation_position="top left")
    if avg_loss > 0:
        fig_scatter.add_hline(y=avg_loss, line_dash="dash", line_color="#94A3B8", opacity=0.6, annotation_text="Avg Exposure", annotation_position="bottom right")

    fig_scatter.update_layout(
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with col_right:
    st.subheader("🛡️ Supplier Risk Band Distribution")
    st.caption("Classification across LOW, MEDIUM, HIGH, CRITICAL bands.")

    band_counts = risk_df["risk_band"].value_counts().reset_index()
    band_counts.columns = ["risk_band", "count"]

    fig_pie = px.pie(
        band_counts,
        names="risk_band",
        values="count",
        color="risk_band",
        color_discrete_map={"LOW": "#10B981", "MEDIUM": "#F59E0B", "HIGH": "#EA580C", "CRITICAL": "#DC2626"},
        hole=0.50,
        template="plotly_white",
        height=400
    )
    fig_pie.update_traces(
        textposition="inside",
        textinfo="percent+label",
        marker=dict(line=dict(color="#FFFFFF", width=2))
    )
    fig_pie.update_layout(
        margin=dict(l=20, r=20, t=30, b=20),
        showlegend=False
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# Row 3: Top 5 Strategic Exposure Suppliers
st.subheader("🚨 Top Vulnerable Suppliers Requiring Mitigation")

top_vulnerable = merged_risk_mc.sort_values(by=["expected_revenue_loss", "supplier_risk_score"], ascending=False).head(5)

formatted_top = top_vulnerable[[
    "supplier_id", "supplier_name", "risk_band", "supplier_risk_score", 
    "stockout_probability", "expected_revenue_loss", "worst_case_revenue_loss"
]].rename(columns={
    "supplier_id": "Supplier ID",
    "supplier_name": "Supplier Name",
    "risk_band": "Risk Band",
    "supplier_risk_score": "Risk Score",
    "stockout_probability": "Stockout Prob (%)",
    "expected_revenue_loss": "Expected Loss (₹)",
    "worst_case_revenue_loss": "Worst-Case Loss (₹)"
})

st.dataframe(
    formatted_top.style.format({
        "Risk Score": "{:.1f}",
        "Stockout Prob (%)": "{:.1f}%",
        "Expected Loss (₹)": "₹{:,.2f}",
        "Worst-Case Loss (₹)": "₹{:,.2f}"
    }),
    use_container_width=True,
    hide_index=True
)
