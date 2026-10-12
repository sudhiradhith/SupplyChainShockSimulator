"""
app/main.py
Supply Chain Resilience & Shock Intelligence Platform — Main Entrypoint
"""

import sys
from pathlib import Path

# Setup paths before importing application modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
APP_DIR = PROJECT_ROOT / "app"

for p in [str(PROJECT_ROOT), str(SRC_DIR), str(APP_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import streamlit as st
import pandas as pd

try:
    from app.components.ui import inject_custom_css, render_metric_card, format_currency, format_number
    from app.data_loader import load_all_data
except ImportError:
    from components.ui import inject_custom_css, render_metric_card, format_currency, format_number
    from data_loader import load_all_data

st.set_page_config(
    page_title="Supply Chain Shock Simulator",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

inject_custom_css()

# Load cached data
data = load_all_data()

suppliers_df = data["suppliers"]
products_df = data["products"]
warehouses_df = data["warehouses"]
risk_df = data["supplier_risk"]
inv_summary_df = data["inventory_summary"]
mc_df = data["monte_carlo_summary"]

# Sidebar configuration
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=400&q=80", use_container_width=True)
    st.markdown("### 🛡️ **Supply Chain Intelligence**")
    st.caption("Resilience Modeling & Disruption Decision Engine")
    st.divider()

    st.markdown("**Network Architecture:**")
    st.markdown(f"- **Suppliers:** `{len(suppliers_df)}` active")
    st.markdown(f"- **Products (SKUs):** `{len(products_df)}` catalog items")
    st.markdown(f"- **Warehouses:** `{len(warehouses_df)}` fulfillment hubs")
    st.markdown(f"- **Simulation Engine:** `Vectorized Monte Carlo`")
    st.divider()
    st.caption("Developed by Sudhir • Portfolio Edition")

# Hero Banner
st.markdown("""
    <div class="callout-banner">
        <h1 style="margin: 0; font-size: 2.2rem; font-weight: 800; color: #FFFFFF;">
            🛡️ Supply Chain Resilience & Shock Intelligence Platform
        </h1>
        <p style="margin-top: 8px; font-size: 1.05rem; color: #CBD5E1; max-width: 900px;">
            An executive intelligence platform answering: <b>"If a supplier or shipping route gets disrupted, how much revenue do we lose, and what exact action should we take to protect the business?"</b>
        </p>
    </div>
""", unsafe_allow_html=True)

# Executive Alert Banner for Critical Suppliers
crit_suppliers = risk_df[risk_df["risk_band"] == "CRITICAL"]
if not crit_suppliers.empty:
    crit_names = ", ".join([f"<b>{row['supplier_name']} ({row['supplier_id']})</b>" for _, row in crit_suppliers.iterrows()])
    st.markdown(f"""
        <div style="background: #FEF2F2; border: 1.5px solid #F87171; border-radius: 12px; padding: 14px 20px; margin-bottom: 20px;">
            <div style="font-weight: 700; color: #991B1B; font-size: 0.95rem; display: flex; align-items: center; gap: 8px;">
                🚨 <span>EXECUTIVE ACTION ALERT: {len(crit_suppliers)} CRITICAL BOTTLENECK SUPPLIERS DETECTED</span>
            </div>
            <div style="color: #7F1D1D; font-size: 0.88rem; margin-top: 4px;">
                {crit_names} have been flagged with elevated disruption risks due to single-sourced critical parts and historical shipping delays. Proactive buffer transfers and dual-sourcing agreements are advised.
            </div>
        </div>
    """, unsafe_allow_html=True)

# Top KPI Summary Cards
col1, col2, col3, col4 = st.columns(4)

total_revenue_exposure = mc_df["expected_revenue_loss"].sum()
high_risk_count = len(risk_df[risk_df["risk_band"].isin(["HIGH", "CRITICAL"])])

turnover_col = "turnover_ratio" if "turnover_ratio" in inv_summary_df.columns else "inventory_turnover"
avg_turnover = inv_summary_df[turnover_col].mean() if turnover_col in inv_summary_df.columns else 5.2

inv_col = "closing_inventory" if "closing_inventory" in inv_summary_df.columns else "avg_inventory"
total_inventory_val = (inv_summary_df[inv_col] * inv_summary_df["avg_price"]).sum() if "avg_price" in inv_summary_df.columns and inv_col in inv_summary_df.columns else 45000000.0

with col1:
    render_metric_card("Total Active SKUs", f"{len(products_df)} Products", "Across 20 categories")

with col2:
    render_metric_card("Network Inventory Value", format_currency(total_inventory_val), "Total stock across warehouses")

with col3:
    render_metric_card("Critical & High Risk", f"{high_risk_count} / {len(suppliers_df)} Vendors", f"{len(crit_suppliers)} Critical | {high_risk_count - len(crit_suppliers)} High", delta_color="danger" if high_risk_count > 0 else "normal")

with col4:
    render_metric_card("Expected Revenue at Risk", format_currency(total_revenue_exposure), "Average simulated disruption loss")

st.markdown("<br>", unsafe_allow_html=True)

# Quick Nav / Interactive Guide
st.markdown("### 🧭 **How to Navigate This Platform (User Guide)**")

nav_col1, nav_col2, nav_col3 = st.columns(3)

with nav_col1:
    st.markdown("""
        **1. Network Health & Risks**
        - **`01 Executive Overview`**: Bird's-eye view of supplier vulnerabilities and financial exposure.
        - **`02 Supplier Intelligence`**: Deep-dive into each supplier across 5 health factors (Delays, Quality, Reliability, Capacity, Sourcing Dependency).
        - **`03 Inventory Intelligence`**: Track stock levels, days of stock remaining (DOI), and reorder alerts.
    """)

with nav_col2:
    st.markdown("""
        **2. Forecasting & Stress Testing**
        - **`04 Demand Forecast`**: Machine learning predictions of customer demand over the next 30 days.
        - **`05 Shock Simulator`**: Interactive sandbox to test *"What happens if a supplier or port is delayed by X days?"*
    """)

with nav_col3:
    st.markdown("""
        **3. Actionable Decisions & ROI**
        - **`06 Scenario Comparison`**: Compare Mild, Moderate, and Severe disruption crises side-by-side.
        - **`07 Recommendations`**: Direct recommendations (e.g. *Transfer stock from warehouse vs Expedite air freight*) showing exact cost and net profit saved.
    """)

st.info("👈 **Use the left sidebar** to select any dashboard and explore the live intelligence.")
