"""
app/pages/02_🏢_Supplier_Intelligence.py
Supplier risk analysis, 5-dimension scorecard, and portfolio exposure breakdown.
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
    from app.components.ui import inject_custom_css, render_metric_card, get_risk_badge, format_number
    from app.data_loader import load_all_data
except ImportError:
    from components.ui import inject_custom_css, render_metric_card, get_risk_badge, format_number
    from data_loader import load_all_data

st.set_page_config(page_title="Supplier Intelligence", page_icon="🏢", layout="wide")
inject_custom_css()

data = load_all_data()
suppliers_df = data["suppliers"]
products_df = data["products"]
risk_df = data["supplier_risk"]
supp_prod_df = data["supplier_product_df"]

st.title("🏢 Supplier Risk & Intelligence Engine")
st.markdown("Multi-dimensional risk scoring combining historical shipment delays, delivery reliability, capacity constraints, quality scores, and single-source dependencies.")

# Filters Bar
col_filter1, col_filter2 = st.columns([4, 4])
with col_filter1:
    selected_band = st.selectbox("Filter by Risk Band:", ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
with col_filter2:
    search_supplier = st.text_input("Search Supplier Name or ID:", placeholder="e.g. S001 or Global Components")

filtered_risk = risk_df.copy()
if selected_band != "ALL":
    filtered_risk = filtered_risk[filtered_risk["risk_band"] == selected_band]
if search_supplier.strip():
    q = search_supplier.strip().lower()
    filtered_risk = filtered_risk[
        filtered_risk["supplier_name"].str.lower().str.contains(q) | 
        filtered_risk["supplier_id"].str.lower().str.contains(q)
    ]

# Summary Cards
c1, c2, c3, c4 = st.columns(4)
with c1:
    render_metric_card("Filtered Suppliers", f"{len(filtered_risk)}", f"Out of {len(risk_df)} total")
with c2:
    render_metric_card("Avg Composite Risk", f"{filtered_risk['supplier_risk_score'].mean():.1f} / 100")
with c3:
    render_metric_card("Avg Delay Risk", f"{filtered_risk['delay_risk'].mean():.1f} / 100", "Weight: 30%")
with c4:
    render_metric_card("Avg Reliability Risk", f"{filtered_risk['reliability_risk'].mean():.1f} / 100", "Weight: 25%")

st.markdown("---")

# Supplier Deep-Dive Section
col_left, col_right = st.columns([6, 6])

with col_left:
    st.subheader("📋 Supplier Risk Rankings")
    
    # Styled table
    display_df = filtered_risk[[
        "supplier_id", "supplier_name", "risk_band", "supplier_risk_score",
        "delay_risk", "reliability_risk", "capacity_risk", "quality_risk", "dependency_risk"
    ]].rename(columns={
        "supplier_id": "ID",
        "supplier_name": "Supplier",
        "risk_band": "Band",
        "supplier_risk_score": "Composite",
        "delay_risk": "Delay (30%)",
        "reliability_risk": "Reliability (25%)",
        "capacity_risk": "Capacity (20%)",
        "quality_risk": "Quality (15%)",
        "dependency_risk": "Dependency (10%)"
    })
    
    st.dataframe(
        display_df.style.format({
            "Composite": "{:.1f}",
            "Delay (30%)": "{:.1f}",
            "Reliability (25%)": "{:.1f}",
            "Capacity (20%)": "{:.1f}",
            "Quality (15%)": "{:.1f}",
            "Dependency (10%)": "{:.1f}"
        }),
        height=420,
        use_container_width=True,
        hide_index=True
    )

with col_right:
    st.subheader("🎯 5-Dimension Radar Profiler")
    
    supplier_options = filtered_risk["supplier_id"].tolist() if not filtered_risk.empty else risk_df["supplier_id"].tolist()
    chosen_supplier_id = st.selectbox(
        "Select Supplier to Profile:", 
        supplier_options, 
        format_func=lambda sid: f"{sid} - {risk_df.loc[risk_df['supplier_id']==sid, 'supplier_name'].values[0]}"
    )

    chosen_row = risk_df[risk_df["supplier_id"] == chosen_supplier_id].iloc[0]
    
    categories = ["Delay Risk", "Reliability Risk", "Capacity Risk", "Quality Risk", "Dependency Risk"]
    scores = [
        chosen_row["delay_risk"],
        chosen_row["reliability_risk"],
        chosen_row["capacity_risk"],
        chosen_row["quality_risk"],
        chosen_row["dependency_risk"],
    ]

    # Benchmark average
    avg_scores = [
        risk_df["delay_risk"].mean(),
        risk_df["reliability_risk"].mean(),
        risk_df["capacity_risk"].mean(),
        risk_df["quality_risk"].mean(),
        risk_df["dependency_risk"].mean(),
    ]

    fig_radar = go.Figure()
    
    # Network benchmark trace
    fig_radar.add_trace(go.Scatterpolar(
        r=avg_scores + [avg_scores[0]],
        theta=categories + [categories[0]],
        mode="lines",
        line=dict(color="#94A3B8", width=2, dash="dash"),
        name="Network Peer Benchmark"
    ))

    # Supplier trace
    band_color = "#DC2626" if chosen_row["risk_band"] == "CRITICAL" else ("#EA580C" if chosen_row["risk_band"] == "HIGH" else "#2563EB")
    fill_color = "rgba(220, 38, 38, 0.2)" if chosen_row["risk_band"] == "CRITICAL" else ("rgba(234, 88, 12, 0.2)" if chosen_row["risk_band"] == "HIGH" else "rgba(37, 99, 235, 0.2)")
    
    fig_radar.add_trace(go.Scatterpolar(
        r=scores + [scores[0]],
        theta=categories + [categories[0]],
        fill="toself",
        fillcolor=fill_color,
        line=dict(color=band_color, width=2.5),
        name=chosen_row["supplier_name"]
    ))

    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=10, color="#64748B")),
            angularaxis=dict(tickfont=dict(size=11, color="#1E293B"))
        ),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1, font=dict(size=10)),
        template="plotly_white",
        height=380,
        margin=dict(l=40, r=40, t=30, b=20)
    )
    st.plotly_chart(fig_radar, use_container_width=True)

# Plain-English Supplier Risk Assessment Banner
if chosen_row["risk_band"] == "CRITICAL":
    st.markdown(f"""
        <div style="background: #FEF2F2; border-left: 5px solid #DC2626; border-radius: 8px; padding: 12px 16px; margin: 12px 0 20px 0;">
            <div style="font-weight: 700; color: #991B1B; font-size: 0.95rem;">🔴 Critical Vulnerability Assessment for {chosen_row['supplier_name']}</div>
            <div style="color: #7F1D1D; font-size: 0.88rem; margin-top: 4px;">
                <b>Why this supplier is critical:</b> High reliance on single-sourced critical parts (Dependency Risk: {chosen_row['dependency_risk']:.1f}/100) paired with frequent shipping delays ({chosen_row['delay_risk']:.1f}/100).
                <br><b>Recommended Next Step:</b> Immediately negotiate secondary supplier volume allocations and maintain an extra 7-day inventory buffer in regional hubs.
            </div>
        </div>
    """, unsafe_allow_html=True)
elif chosen_row["risk_band"] == "HIGH":
    st.markdown(f"""
        <div style="background: #FFF7ED; border-left: 5px solid #EA580C; border-radius: 8px; padding: 12px 16px; margin: 12px 0 20px 0;">
            <div style="font-weight: 700; color: #9A3412; font-size: 0.95rem;">🟠 High Risk Monitoring for {chosen_row['supplier_name']}</div>
            <div style="color: #7C2D12; font-size: 0.88rem; margin-top: 4px;">
                <b>Risk Drivers:</b> Overall health score is {chosen_row['supplier_risk_score']:.1f}/100.
                <br><b>Recommended Next Step:</b> Set weekly shipment tracking checkpoints and verify capacity commitments.
            </div>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
        <div style="background: #F0FDF4; border-left: 5px solid #16A34A; border-radius: 8px; padding: 12px 16px; margin: 12px 0 20px 0;">
            <div style="font-weight: 700; color: #166534; font-size: 0.95rem;">🟢 Stable Supplier Status: {chosen_row['supplier_name']} ({chosen_row['risk_band']})</div>
            <div style="color: #14532D; font-size: 0.88rem; margin-top: 4px;">
                Healthy operational performance with on-time delivery rate above network average. Maintain standard quarterly vendor reviews.
            </div>
        </div>
    """, unsafe_allow_html=True)

# Supplier Products & Shipment History Drill-down
st.subheader(f"📦 Product Portfolio & Sourcing for {chosen_row['supplier_name']} ({chosen_supplier_id})")

prod_meta_cols = [c for c in ["product_id", "product_name", "category", "criticality"] if c in products_df.columns]
supp_products = supp_prod_df[supp_prod_df["supplier_id"] == chosen_supplier_id].merge(products_df[prod_meta_cols], on="product_id", how="left")

if not supp_products.empty:
    cols_to_show = [c for c in ["product_id", "product_name", "category", "unit_cost", "criticality", "lead_time_days"] if c in supp_products.columns]
    supp_disp = supp_products[cols_to_show].rename(columns={
        "product_id": "Product ID",
        "product_name": "Product Name",
        "category": "Category",
        "unit_cost": "Unit Cost (₹)",
        "criticality": "Criticality",
        "lead_time_days": "Contracted Lead Time (Days)"
    })
    
    fmt_dict = {}
    if "Unit Cost (₹)" in supp_disp.columns:
        fmt_dict["Unit Cost (₹)"] = "₹{:,.2f}"
    if "Contracted Lead Time (Days)" in supp_disp.columns:
        fmt_dict["Contracted Lead Time (Days)"] = "{:.0f} Days"
        
    st.dataframe(
        supp_disp.style.format(fmt_dict),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No mapped products for this supplier.")
