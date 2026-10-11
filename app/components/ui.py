"""
app/components/ui.py
Reusable UI components, custom styling, Plotly chart templates, and data formatting for Streamlit.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


# Custom CSS Theme
def inject_custom_css():
    st.markdown("""
        <style>
        /* Import clean modern font */
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
        }

        /* Metric card styling */
        .metric-card {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 16px;
            padding: 20px 24px;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px -4px rgba(0, 0, 0, 0.08);
        }
        .metric-label {
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #6B7280;
            margin-bottom: 4px;
        }
        .metric-value {
            font-size: 1.75rem;
            font-weight: 800;
            color: #111827;
            line-height: 1.2;
        }
        .metric-delta {
            font-size: 0.75rem;
            font-weight: 600;
            margin-top: 6px;
        }

        /* Risk Badge styling */
        .badge {
            display: inline-flex;
            align-items: center;
            padding: 3px 10px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
        }
        .badge-critical { background: #FEE2E2; color: #DC2626; border: 1px solid #FCA5A5; }
        .badge-high { background: #FFEDD5; color: #EA580C; border: 1px solid #FDBA74; }
        .badge-medium { background: #FEF3C7; color: #D97706; border: 1px solid #FCD34D; }
        .badge-low { background: #D1FAE5; color: #059669; border: 1px solid #6EE7B7; }

        /* Banner callout */
        .callout-banner {
            background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
            border-radius: 16px;
            padding: 24px;
            color: #FFFFFF;
            margin-bottom: 24px;
            border: 1px solid #334155;
        }
        </style>
    """, unsafe_allow_html=True)


def render_metric_card(label: str, value: str, delta: str = None, delta_color: str = "normal"):
    delta_html = ""
    if delta:
        color = "#10B981" if delta_color == "normal" else "#EF4444"
        delta_html = f'<div class="metric-delta" style="color: {color};">{delta}</div>'
    
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            {delta_html}
        </div>
    """, unsafe_allow_html=True)


def get_risk_badge(band: str) -> str:
    b = str(band).upper()
    if b == "CRITICAL":
        return '<span class="badge badge-critical">CRITICAL</span>'
    elif b == "HIGH":
        return '<span class="badge badge-high">HIGH RISK</span>'
    elif b == "MEDIUM":
        return '<span class="badge badge-medium">MEDIUM</span>'
    else:
        return '<span class="badge badge-low">LOW RISK</span>'


def format_currency(val: float) -> str:
    """Format currency values in INR / standard currency."""
    if val >= 10_000_000:
        return f"₹{val/10_000_000:.2f} Cr"
    elif val >= 100_000:
        return f"₹{val/100_000:.2f} L"
    elif val >= 1_000:
        return f"₹{val:,.0f}"
    else:
        return f"₹{val:.2f}"


def format_number(val: float) -> str:
    return f"{val:,.1f}" if isinstance(val, float) else f"{val:,}"


# Plotly Custom Theme
PLOTLY_TEMPLATE = "plotly_white"
PLOTLY_COLORWAY = ["#2563EB", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#06B6D4", "#EC4899"]


def apply_chart_theme(fig, title: str = None, height: int = 400, show_legend: bool = True):
    """Applies a clean, modern corporate theme to Plotly figures."""
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        height=height,
        title=dict(
            text=f"<b>{title}</b>" if title else "",
            font=dict(size=14, color="#1E293B", family="Plus Jakarta Sans, sans-serif"),
            x=0.01,
            xanchor="left"
        ) if title else None,
        font=dict(family="Plus Jakarta Sans, -apple-system, sans-serif", color="#334155"),
        margin=dict(l=24, r=24, t=40 if title else 24, b=24),
        showlegend=show_legend,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11)
        ) if show_legend else None,
        hoverlabel=dict(
            bgcolor="#1E293B",
            font_size=12,
            font_family="Plus Jakarta Sans, sans-serif",
            font_color="#FFFFFF"
        ),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="#F1F5F9",
        zeroline=True,
        zerolinewidth=1,
        zerolinecolor="#E2E8F0"
    )
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="#F1F5F9",
        zeroline=True,
        zerolinewidth=1,
        zerolinecolor="#E2E8F0"
    )
    return fig
