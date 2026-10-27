"""
app/pages/05_⚡_Shock_Simulator.py
Interactive operational disruption simulation console and probabilistic Monte Carlo engine.
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
    from app.components.ui import inject_custom_css, render_metric_card, format_currency, format_number
    from app.data_loader import load_all_data
except ImportError:
    from components.ui import inject_custom_css, render_metric_card, format_currency, format_number
    from data_loader import load_all_data

from simulation.supplier_shock import simulate_supplier_delay
from simulation.demand_shock import simulate_demand_shock
from simulation.capacity_shock import simulate_capacity_shock
from simulation.transport_shock import simulate_transport_shock
from simulation.combined_shock import simulate_combined_shock
from simulation.monte_carlo import run_monte_carlo_supplier_delay

st.set_page_config(page_title="Shock Simulator", page_icon="⚡", layout="wide")
inject_custom_css()

data = load_all_data()
suppliers_df = data["suppliers"]
products_df = data["products"]
warehouses_df = data["warehouses"]
supp_prod_df = data["supplier_products"]
sim_context = data["sim_context"]

st.title("⚡ Operational Shock & Disruption Simulator")
st.markdown("Quantify financial and inventory exposure under deterministic disruption vectors or probabilistic Monte Carlo stress testing.")

# Plain-English User Guide Callout
st.markdown("""
    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-left: 4px solid #2563EB; border-radius: 8px; padding: 12px 16px; margin-bottom: 20px;">
        <span style="font-weight: 700; color: #1E293B;">💡 How the Disruption Sandbox Works:</span>
        <span style="color: #475569; font-size: 0.92rem; margin-left: 6px;">
            Choose a disruption scenario on the left sidebar (e.g. <b>Supplier Delivery Delay of 14 days</b>). The engine immediately recalculates your inventory buffers, projects exact stockout dates, and computes the gross revenue at risk.
        </span>
    </div>
""", unsafe_allow_html=True)

# Sidebar Simulation Controls
with st.sidebar:
    st.markdown("### 🎛️ **Disruption Controls**")
    
    shock_mode = st.radio(
        "Select Shock Mode:",
        ["Supplier Delivery Delay", "Demand Surge", "Supplier Capacity Cut", "Transport Route Delay", "Combined Multi-Vector Shock"]
    )
    
    st.divider()
    
    # Mode-specific inputs
    selected_supplier = "S001"
    delay_days = 14
    demand_surge_pct = 0.25
    capacity_cut_pct = 0.30
    transit_delay_days = 7
    target_wh = "ALL"

    if shock_mode in ["Supplier Delivery Delay", "Supplier Capacity Cut", "Combined Multi-Vector Shock"]:
        supplier_list = suppliers_df["supplier_id"].tolist()
        selected_supplier = st.selectbox(
            "Target Supplier:",
            supplier_list,
            index=0,
            format_func=lambda sid: f"{sid} - {suppliers_df.loc[suppliers_df['supplier_id']==sid, 'supplier_name'].values[0]}"
        )

    if shock_mode in ["Supplier Delivery Delay", "Combined Multi-Vector Shock"]:
        delay_days = st.slider("Supplier Delivery Delay (Days):", min_value=1, max_value=60, value=14, step=1)

    if shock_mode in ["Demand Surge", "Combined Multi-Vector Shock"]:
        demand_surge_pct = st.slider("Demand Surge (% Increase):", min_value=5, max_value=100, value=30, step=5) / 100.0

    if shock_mode in ["Supplier Capacity Cut", "Combined Multi-Vector Shock"]:
        capacity_cut_pct = st.slider("Capacity Reduction (% Cut):", min_value=10, max_value=90, value=40, step=5) / 100.0

    if shock_mode in ["Transport Route Delay", "Combined Multi-Vector Shock"]:
        transit_delay_days = st.slider("Inbound Transit Delay (Days):", min_value=1, max_value=30, value=7, step=1)
        wh_options = ["ALL"] + warehouses_df["warehouse_id"].tolist()
        target_wh = st.selectbox("Target Warehouse:", wh_options)

    st.divider()
    run_mc = st.checkbox("Run 5,000-Iteration Monte Carlo", value=True)

# Run Selected Simulation
if shock_mode == "Supplier Delivery Delay":
    sim_result = simulate_supplier_delay(
        selected_supplier, delay_days, context=sim_context
    )
    total_rev_at_risk = sim_result.get("total_revenue_at_risk", 0.0)
    total_units_lost = sim_result.get("total_lost_units", 0.0)
    detail_df = sim_result.get("detail", pd.DataFrame())
    stocked_out_count = sim_result.get("products_stocked_out", 0)

elif shock_mode == "Demand Surge":
    sim_result = simulate_demand_shock(
        demand_surge_pct, context=sim_context
    )
    total_rev_at_risk = sim_result.get("total_revenue_at_risk", 0.0)
    detail_df = sim_result.get("detail", pd.DataFrame())
    total_units_lost = detail_df["normal_demand"].sum() * demand_surge_pct if not detail_df.empty else 0.0
    stocked_out_count = len(detail_df[detail_df["stockout_date_moved_up_by_days"] > 5]) if not detail_df.empty else 0

elif shock_mode == "Supplier Capacity Cut":
    sim_result = simulate_capacity_shock(
        selected_supplier, capacity_cut_pct, supp_prod_df, suppliers_df, demand_df, products_df
    )
    detail_df = sim_result.get("detail", pd.DataFrame())
    total_rev_at_risk = sim_result.get("total_revenue_at_risk_per_day", 0.0) * 14 # 14-day horizon
    total_units_lost = sim_result.get("capacity_lost_per_day", 0.0) * 14
    stocked_out_count = sim_result.get("affected_products", 0)

elif shock_mode == "Transport Route Delay":
    wh_param = None if target_wh == "ALL" else target_wh
    sim_result = simulate_transport_shock(
        transit_delay_days, shipments_df, demand_df, products_df, affected_warehouse_id=wh_param
    )
    total_rev_at_risk = sim_result.get("total_revenue_at_risk", 0.0)
    total_units_lost = sim_result.get("total_delayed_units", 0.0)
    detail_df = sim_result.get("detail", pd.DataFrame())
    stocked_out_count = sim_result.get("affected_shipments_count", 0)

else: # Combined Shock
    wh_param = None if target_wh == "ALL" else target_wh
    sim_result = simulate_combined_shock(
        selected_supplier, delay_days, demand_surge_pct, capacity_cut_pct,
        transit_delay_days=transit_delay_days,
        inventory_df=inventory_df, demand_df=demand_df, supplier_product_df=supp_prod_df,
        suppliers_df=suppliers_df, products_df=products_df, shipments_df=shipments_df,
        context=sim_context
    )
    total_rev_at_risk = sim_result.get("total_revenue_at_risk", 0.0)
    delay_imp = sim_result.get("supplier_delay_impact", {})
    total_units_lost = delay_imp.get("total_lost_units", 0.0)
    detail_df = delay_imp.get("detail", pd.DataFrame())
    stocked_out_count = delay_imp.get("products_stocked_out", 0)

# Display Top KPI Metric Cards
c1, c2, c3, c4 = st.columns(4)

with c1:
    render_metric_card("Total Revenue at Risk", format_currency(total_rev_at_risk), f"Mode: {shock_mode[:18]}...", delta_color="danger" if total_rev_at_risk > 0 else "normal")

with c2:
    render_metric_card("Disrupted Inventory Units", f"{total_units_lost:,.1f} Units", "Direct stockout volume")

with c3:
    render_metric_card("Impacted Catalog Items", f"{stocked_out_count} Items", "Stockout or delayed")

with c4:
    supplier_name = suppliers_df.loc[suppliers_df["supplier_id"]==selected_supplier, "supplier_name"].values[0] if selected_supplier in suppliers_df["supplier_id"].values else "Network"
    render_metric_card("Primary Entity", f"{selected_supplier}", f"{supplier_name[:18]}")

st.markdown("---")

# Impact Detail Section
col_left, col_right = st.columns([7, 5])

with col_left:
    st.subheader("📋 Disrupted SKU Impact Breakdown")
    if not detail_df.empty:
        # Format table
        disp_detail = detail_df.copy()
        fmt_map = {}
        for c in ["lost_revenue", "revenue_at_risk", "revenue_at_risk_per_day"]:
            if c in disp_detail.columns:
                fmt_map[c] = "₹{:,.2f}"
        for c in ["lost_units", "current_inventory", "avg_daily_demand", "shortfall_units_per_day", "delayed_quantity"]:
            if c in disp_detail.columns:
                fmt_map[c] = "{:,.1f}"
        for c in ["days_to_stockout", "days_out_of_stock", "stockout_date_moved_up_by_days"]:
            if c in disp_detail.columns:
                fmt_map[c] = "{:.1f} d"
                
        st.dataframe(disp_detail.style.format(fmt_map), height=360, use_container_width=True, hide_index=True)
    else:
        st.info("No SKU-level stockouts triggered under current parameters.")

with col_right:
    st.subheader("💰 Revenue Loss Distribution by SKU")
    loss_col = "lost_revenue" if "lost_revenue" in detail_df.columns else ("revenue_at_risk" if "revenue_at_risk" in detail_df.columns else None)
    
    if not detail_df.empty and loss_col is not None:
        fig_loss_bar = px.bar(
            detail_df,
            x="product_name",
            y=loss_col,
            color=loss_col,
            color_continuous_scale="Reds",
            labels={loss_col: "Revenue at Risk (₹)", "product_name": "Product"},
            template="plotly_white",
            height=360
        )
        fig_loss_bar.update_traces(
            hovertemplate="<b>%{x}</b><br>Revenue Loss: ₹%{y:,.2f}<extra></extra>"
        )
        fig_loss_bar.update_layout(margin=dict(l=20, r=20, t=20, b=20), coloraxis_showscale=False)
        st.plotly_chart(fig_loss_bar, use_container_width=True)
    else:
        st.info("No revenue loss breakdown available for current parameters.")

# Monte Carlo Probabilistic Stress Test Section
if run_mc and selected_supplier:
    st.markdown("---")
    st.subheader(f"🎲 Monte Carlo Probabilistic Disruption Profile: {selected_supplier}")
    st.caption("5,000 stochastic iterations sampling real-world lead time delay distributions.")

    @st.cache_data(show_spinner="Running 5,000 Monte Carlo stochastic iterations...")
    def get_cached_monte_carlo(sid: str):
        return run_monte_carlo_supplier_delay(sid, n_iterations=5000, context=sim_context)

    mc_res = get_cached_monte_carlo(selected_supplier)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_metric_card("Stockout Probability", f"{mc_res['stockout_probability']:.1f}%", "Likelihood of disruption")
    with m2:
        render_metric_card("Expected Loss (P50)", format_currency(mc_res["expected_revenue_loss"]), "Mean simulated impact")
    with m3:
        render_metric_card("95th Percentile Loss (P95)", format_currency(mc_res["percentile_95"]), "Severe tail risk")
    with m4:
        render_metric_card("Worst-Case Scenario", format_currency(mc_res["worst_case_revenue_loss"]), "Max simulated loss")

    # Monte Carlo Histogram
    raw_losses = mc_res["raw_results"]
    fig_hist = px.histogram(
        raw_losses,
        nbins=40,
        title=f"Probabilistic Loss Distribution (5,000 Iterations) - {selected_supplier}",
        labels={"value": "Simulated Revenue Loss (₹)", "count": "Frequency"},
        template="plotly_white",
        color_discrete_sequence=["#2563EB"],
        height=380
    )
    fig_hist.update_traces(
        hovertemplate="Loss Range: ₹%{x:,.0f}<br>Simulated Runs: %{y}<extra></extra>"
    )
    fig_hist.add_vline(x=mc_res["expected_revenue_loss"], line_dash="dash", line_color="#F59E0B", annotation_text="Expected (P50)", annotation_position="top left")
    fig_hist.add_vline(x=mc_res["percentile_95"], line_dash="dash", line_color="#EF4444", annotation_text="95th Percentile (P95 VaR)", annotation_position="top right")
    fig_hist.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_hist, use_container_width=True)
