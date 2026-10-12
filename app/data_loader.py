"""
app/data_loader.py
Cached data loading routines for the Streamlit dashboard.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import os
import sys

# Ensure src/ is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from simulation.supplier_shock import build_simulation_context, build_simulation_context_from_summary


@st.cache_data(show_spinner="⚡ Initializing Supply Chain Network Intelligence...")
def load_all_data():
    """Loads all dataset parquet files and dimension tables with high-speed caching."""
    raw_dir = PROJECT_ROOT / "data" / "raw"
    proc_dir = PROJECT_ROOT / "data" / "processed"

    # Load fast pre-packaged local datasets directly (<1.2s total)
    suppliers_df = pd.read_csv(raw_dir / "suppliers.csv")
    products_df = pd.read_csv(raw_dir / "products.csv")
    warehouses_df = pd.read_csv(raw_dir / "warehouses.csv")
    supplier_product_df = pd.read_csv(raw_dir / "supplier_products.csv")

    inventory_summary_df = pd.read_parquet(proc_dir / "inventory_summary.parquet")
    supplier_risk_df = pd.read_parquet(proc_dir / "supplier_risk.parquet")
    forecast_comp_df = pd.read_parquet(proc_dir / "forecast_comparison.parquet")
    best_forecast_df = pd.read_parquet(proc_dir / "best_forecast_model_per_product.parquet")
    monte_carlo_df = pd.read_parquet(proc_dir / "monte_carlo_summary.parquet")
    shipments_df = pd.read_parquet(proc_dir / "shipments_enriched.parquet")
    demand_df = pd.read_parquet(proc_dir / "demand_enriched.parquet")
    inventory_df = pd.read_parquet(proc_dir / "inventory_enriched.parquet")

    # Optional: override with online database only if explicitly enabled
    use_online_db = False
    if os.getenv("ENABLE_CLOUD_DB", "").lower() in ("true", "1", "yes"):
        try:
            from db.database import is_db_available, load_table
            if is_db_available():
                cloud_risk = load_table("supplier_risk")
                if cloud_risk is not None and not cloud_risk.empty:
                    supplier_risk_df = cloud_risk
                    use_online_db = True
        except Exception:
            use_online_db = False

    # Ensure standardized column aliases for inventory_summary
    if "turnover_ratio" in inventory_summary_df.columns:
        inventory_summary_df["inventory_turnover"] = inventory_summary_df["turnover_ratio"]
    elif "inventory_turnover" in inventory_summary_df.columns:
        inventory_summary_df["turnover_ratio"] = inventory_summary_df["inventory_turnover"]

    if "avg_inventory" in inventory_summary_df.columns:
        inventory_summary_df["closing_inventory"] = inventory_summary_df["avg_inventory"]
    elif "closing_inventory" in inventory_summary_df.columns:
        inventory_summary_df["avg_inventory"] = inventory_summary_df["closing_inventory"]

    if "avg_daily_demand" not in inventory_summary_df.columns and "total_demand" in inventory_summary_df.columns:
        inventory_summary_df["avg_daily_demand"] = inventory_summary_df["total_demand"] / 730.0

    # Instant precomputed simulation context (<1ms)
    sim_context = build_simulation_context_from_summary(inventory_summary_df, products_df, supplier_product_df)

    return {
        # Base names
        "suppliers": suppliers_df,
        "products": products_df,
        "warehouses": warehouses_df,
        "supplier_products": supplier_product_df,
        "demand": demand_df,
        "inventory": inventory_df,
        "shipments": shipments_df,
        "inventory_summary": inventory_summary_df,
        "supplier_risk": supplier_risk_df,
        "forecast_comparison": forecast_comp_df,
        "best_forecast": best_forecast_df,
        "monte_carlo_summary": monte_carlo_df,
        "sim_context": sim_context,
        "is_online_db": use_online_db,
        # Suffix aliases for complete compatibility
        "suppliers_df": suppliers_df,
        "products_df": products_df,
        "warehouses_df": warehouses_df,
        "supplier_product_df": supplier_product_df,
        "demand_df": demand_df,
        "inventory_df": inventory_df,
        "shipments_df": shipments_df,
        "inventory_summary_df": inventory_summary_df,
    }
