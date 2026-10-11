"""
app/pages/07_💡_Recommendations.py
Mitigation strategy optimization engine and strategic decision support matrix.
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
from optimization.strategies import recommend_strategy

st.set_page_config(page_title="Mitigation Strategies", page_icon="💡", layout="wide")
inject_custom_css()

data = load_all_data()
suppliers_df = data["suppliers"]
products_df = data["products"]
inventory_df = data["inventory"]
sim_context = data["sim_context"]

st.title("💡 Strategic Mitigation & Decision Matrix")
st.markdown("Algorithmic optimization comparing mitigation strategies (Do Nothing, Expedited Freight, Alternate Supplier, Warehouse Transfer) ranked by net financial benefit.")

# Disruption Input & Cost Assumptions
col_input1, col_input2 = st.columns([5, 7])

with col_input1:
    st.subheader("⚠️ Active Disruption Scenario")
    target_sid = st.selectbox(
        "Disrupted Supplier:",
        suppliers_df["supplier_id"].tolist(),
        index=0,
        format_func=lambda sid: f"{sid} - {suppliers_df.loc[suppliers_df['supplier_id']==sid, 'supplier_name'].values[0]}"
    )
    delay_input = st.slider("Disruption Duration (Days):", 1, 45, 14)

with col_input2:
    st.subheader("💵 Cost Assumptions (₹)")
    c_cost1, c_cost2 = st.columns(2)
    with c_cost1:
        expedite_cost = st.number_input("Expedited Air Freight (₹/unit):", value=15.0, step=1.0)
        switching_cost = st.number_input("Supplier Switching Setup (₹):", value=400000.0, step=50000.0)
    with c_cost2:
        alt_premium = st.number_input("Alternate Unit Cost Premium (₹/unit):", value=5.0, step=1.0)
        transfer_cost = st.number_input("Inter-Warehouse Transfer (₹/unit):", value=3.0, step=0.5)

cost_assumptions = {
    "expedite_cost_per_unit": expedite_cost,
    "switching_cost": switching_cost,
    "alt_supplier_unit_cost_premium": alt_premium,
    "transfer_cost_per_unit": transfer_cost
}

# Run Shock Simulation
shock_res = simulate_supplier_delay(target_sid, delay_input, context=sim_context)
rev_at_risk = shock_res.get("total_revenue_at_risk", 0.0)

# Run Optimization
opt_res = recommend_strategy(shock_res, inventory_df, cost_assumptions)
strategies_df = opt_res["strategies"]
best_strat = opt_res["recommendation"]

st.markdown("---")

# Recommended Strategy Banner
st.markdown(f"""
    <div style="background: #F0FDF4; border: 2px solid #86EFAC; border-radius: 16px; padding: 20px 24px; margin-bottom: 24px;">
        <div style="font-size: 0.85rem; font-weight: 700; color: #166534; text-transform: uppercase; letter-spacing: 0.05em;">
            RECOMMENDED MITIGATION ACTION
        </div>
        <div style="font-size: 1.6rem; font-weight: 800; color: #14532D; margin-top: 4px;">
            ✦ {best_strat}
        </div>
        <div style="font-size: 0.95rem; color: #15803D; margin-top: 6px;">
            Generates <b>{format_currency(opt_res['net_benefit'])}</b> in net financial benefit by recovering 
            <b>{format_currency(opt_res['revenue_saved'])}</b> in revenue at an execution cost of <b>{format_currency(opt_res['expected_cost'])}</b>.
        </div>
    </div>
""", unsafe_allow_html=True)

# Top KPI Summary Cards
c1, c2, c3, c4 = st.columns(4)
with c1:
    render_metric_card("Gross Revenue at Risk", format_currency(rev_at_risk), "Baseline unmitigated")
with c2:
    render_metric_card("Protected Revenue", format_currency(opt_res["revenue_saved"]), "Via best strategy")
with c3:
    render_metric_card("Mitigation Cost", format_currency(opt_res["expected_cost"]), "Implementation spend")
with c4:
    render_metric_card("Net Benefit", format_currency(opt_res["net_benefit"]), "Net P&L gain", delta_color="normal" if opt_res["net_benefit"]>0 else "danger")

st.markdown("---")

# Strategy Decision Matrix Table & Visual Comparison
col_tbl, col_chart = st.columns([6, 6])

with col_tbl:
    st.subheader("📋 Mitigation Strategy Decision Matrix")
    
    formatted_strategies = strategies_df.copy()
    formatted_strategies = formatted_strategies.rename(columns={
        "strategy": "Mitigation Strategy",
        "cost": "Implementation Cost (₹)",
        "revenue_saved": "Revenue Saved (₹)",
        "net_benefit": "Net Benefit (₹)"
    })
    
    st.dataframe(
        formatted_strategies.style.format({
            "Implementation Cost (₹)": "₹{:,.2f}",
            "Revenue Saved (₹)": "₹{:,.2f}",
            "Net Benefit (₹)": "₹{:,.2f}"
        }),
        height=240,
        use_container_width=True,
        hide_index=True
    )
    
    # Plain-English Strategy Legend
    st.markdown("""
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 14px; font-size: 0.82rem; color: #475569; margin-top: 10px;">
            <b>Mitigation Options Explained:</b><br>
            • <b>Warehouse Transfer:</b> Shift surplus safety stock from nearby hubs with available buffer.<br>
            • <b>Expedite Shipment:</b> Pay priority freight surcharge to compress transit lead times.<br>
            • <b>Alternate Supplier:</b> Activate pre-qualified secondary vendor (requires tooling setup).<br>
            • <b>Do Nothing:</b> Accept stockout if fixing it costs more than the lost sales.
        </div>
    """, unsafe_allow_html=True)

with col_chart:
    st.subheader("📊 Financial Impact by Strategy")
    st.caption("Protected revenue, execution cost, and net P&L benefit comparison.")
    
    fig_strat = go.Figure()
    fig_strat.add_trace(go.Bar(
        x=strategies_df["strategy"],
        y=strategies_df["revenue_saved"],
        name="Revenue Protected",
        marker_color="#2563EB",
        hovertemplate="Strategy: %{x}<br>Protected: ₹%{y:,.2f}<extra></extra>"
    ))
    fig_strat.add_trace(go.Bar(
        x=strategies_df["strategy"],
        y=strategies_df["cost"],
        name="Execution Cost",
        marker_color="#EF4444",
        hovertemplate="Strategy: %{x}<br>Cost: ₹%{y:,.2f}<extra></extra>"
    ))
    fig_strat.add_trace(go.Bar(
        x=strategies_df["strategy"],
        y=strategies_df["net_benefit"],
        name="Net Benefit",
        marker_color="#10B981",
        hovertemplate="Strategy: %{x}<br>Net Benefit: ₹%{y:,.2f}<extra></extra>"
    ))
    fig_strat.update_layout(
        template="plotly_white",
        barmode="group",
        height=340,
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)),
        xaxis_title="Mitigation Option",
        yaxis_title="Financial Value (₹)"
    )
    st.plotly_chart(fig_strat, use_container_width=True)
