"""
app/pages/06_🔄_Scenario_Comparison.py
Multi-scenario sensitivity analysis and disruption severity benchmarking.
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

from simulation.supplier_shock import simulate_supplier_delay
from simulation.combined_shock import simulate_combined_shock

st.set_page_config(page_title="Scenario Comparison", page_icon="🔄", layout="wide")
inject_custom_css()

data = load_all_data()
suppliers_df = data["suppliers"]
products_df = data["products"]
supp_prod_df = data["supplier_products"]
demand_df = data["demand"]
inventory_df = data["inventory"]
sim_context = data["sim_context"]

st.title("🔄 Multi-Scenario Disruption Sensitivity Analysis")
st.markdown("Stress test supply chain resilience across predefined and custom operational disruption scenarios.")

# Select Supplier
selected_sid = st.selectbox(
    "Select Benchmark Supplier:",
    suppliers_df["supplier_id"].tolist(),
    format_func=lambda sid: f"{sid} - {suppliers_df.loc[suppliers_df['supplier_id']==sid, 'supplier_name'].values[0]}"
)

# Scenario Definition Tabs
st.subheader("⚙️ Scenario Parameter Tuning")
c_scen1, c_scen2, c_scen3 = st.columns(3)

with c_scen1:
    st.markdown("### 🟢 **Scenario 1: Mild Shock**")
    s1_delay = st.slider("S1 Delay (Days):", 1, 30, 5, key="s1_del")
    s1_demand = st.slider("S1 Demand Surge (%):", 0, 50, 10, key="s1_dem") / 100.0
    s1_cap = st.slider("S1 Capacity Cut (%):", 0, 50, 10, key="s1_cap") / 100.0

with c_scen2:
    st.markdown("### 🟡 **Scenario 2: Moderate Shock**")
    s2_delay = st.slider("S2 Delay (Days):", 1, 45, 14, key="s2_del")
    s2_demand = st.slider("S2 Demand Surge (%):", 0, 75, 25, key="s2_dem") / 100.0
    s2_cap = st.slider("S2 Capacity Cut (%):", 0, 75, 30, key="s2_cap") / 100.0

with c_scen3:
    st.markdown("### 🔴 **Scenario 3: Severe Disruption**")
    s3_delay = st.slider("S3 Delay (Days):", 1, 60, 30, key="s3_del")
    s3_demand = st.slider("S3 Demand Surge (%):", 0, 100, 50, key="s3_dem") / 100.0
    s3_cap = st.slider("S3 Capacity Cut (%):", 0, 90, 50, key="s3_cap") / 100.0

# Execute simulations
s1_res = simulate_combined_shock(
    selected_sid, s1_delay, s1_demand, s1_cap,
    inventory_df=inventory_df, demand_df=demand_df, supplier_product_df=supp_prod_df,
    suppliers_df=suppliers_df, products_df=products_df, context=sim_context
)
s2_res = simulate_combined_shock(
    selected_sid, s2_delay, s2_demand, s2_cap,
    inventory_df=inventory_df, demand_df=demand_df, supplier_product_df=supp_prod_df,
    suppliers_df=suppliers_df, products_df=products_df, context=sim_context
)
s3_res = simulate_combined_shock(
    selected_sid, s3_delay, s3_demand, s3_cap,
    inventory_df=inventory_df, demand_df=demand_df, supplier_product_df=supp_prod_df,
    suppliers_df=suppliers_df, products_df=products_df, context=sim_context
)

st.markdown("---")

# Comparative Cards
st.subheader("📊 Comparative Exposure Summary")
col1, col2, col3 = st.columns(3)

with col1:
    render_metric_card("Scenario 1 Exposure", format_currency(s1_res["total_revenue_at_risk"]), f"Delay: {s1_delay}d | Surge: {int(s1_demand*100)}%")

with col2:
    render_metric_card("Scenario 2 Exposure", format_currency(s2_res["total_revenue_at_risk"]), f"Delay: {s2_delay}d | Surge: {int(s2_demand*100)}%", delta_color="danger" if s2_res["total_revenue_at_risk"]>s1_res["total_revenue_at_risk"] else "normal")

with col3:
    render_metric_card("Scenario 3 Exposure", format_currency(s3_res["total_revenue_at_risk"]), f"Delay: {s3_delay}d | Surge: {int(s3_demand*100)}%", delta_color="danger")

# Comparative Chart
col_ch1, col_ch2 = st.columns([7, 5])

comparison_df = pd.DataFrame([
    {
        "Scenario": "Scenario 1 (Mild)", 
        "Supplier Delay Loss": s1_res["supplier_delay_impact"]["total_revenue_at_risk"], 
        "Demand Shock Loss": s1_res["demand_shock_impact"]["total_revenue_at_risk"],
        "Total Revenue at Risk": s1_res["total_revenue_at_risk"]
    },
    {
        "Scenario": "Scenario 2 (Moderate)", 
        "Supplier Delay Loss": s2_res["supplier_delay_impact"]["total_revenue_at_risk"], 
        "Demand Shock Loss": s2_res["demand_shock_impact"]["total_revenue_at_risk"],
        "Total Revenue at Risk": s2_res["total_revenue_at_risk"]
    },
    {
        "Scenario": "Scenario 3 (Severe)", 
        "Supplier Delay Loss": s3_res["supplier_delay_impact"]["total_revenue_at_risk"], 
        "Demand Shock Loss": s3_res["demand_shock_impact"]["total_revenue_at_risk"],
        "Total Revenue at Risk": s3_res["total_revenue_at_risk"]
    },
])

with col_ch1:
    fig_comp = px.bar(
        comparison_df,
        x="Scenario",
        y=["Supplier Delay Loss", "Demand Shock Loss"],
        title="Financial Exposure Breakdown Across Scenarios",
        labels={"value": "Disruption Loss (₹)", "variable": "Disruption Vector"},
        barmode="stack",
        template="plotly_white",
        color_discrete_sequence=["#2563EB", "#F59E0B"],
        height=380
    )
    fig_comp.update_traces(
        hovertemplate="<b>%{x}</b><br>%{data.name}: ₹%{y:,.2f}<extra></extra>"
    )
    fig_comp.update_layout(
        margin=dict(l=20, r=20, t=40, b=20), 
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10))
    )
    st.plotly_chart(fig_comp, use_container_width=True)

with col_ch2:
    st.markdown("### 📋 **Scenario Metrics Matrix**")
    scen_matrix = pd.DataFrame([
        {"Scenario": "Scenario 1 (Mild)", "Delay": f"{s1_delay} Days", "Demand Surge": f"+{int(s1_demand*100)}%", "Capacity Cut": f"-{int(s1_cap*100)}%", "Total Exposure": s1_res["total_revenue_at_risk"]},
        {"Scenario": "Scenario 2 (Moderate)", "Delay": f"{s2_delay} Days", "Demand Surge": f"+{int(s2_demand*100)}%", "Capacity Cut": f"-{int(s2_cap*100)}%", "Total Exposure": s2_res["total_revenue_at_risk"]},
        {"Scenario": "Scenario 3 (Severe)", "Delay": f"{s3_delay} Days", "Demand Surge": f"+{int(s3_demand*100)}%", "Capacity Cut": f"-{int(s3_cap*100)}%", "Total Exposure": s3_res["total_revenue_at_risk"]},
    ])
    st.dataframe(
        scen_matrix.style.format({"Total Exposure": "₹{:,.2f}"}),
        use_container_width=True,
        hide_index=True
    )
