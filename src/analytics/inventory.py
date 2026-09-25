"""
Inventory Intelligence Module
Calculates turnover, days of inventory, safety stock, and reorder point
for the Supply Chain Resilience & Shock Intelligence Platform.
"""

import pandas as pd
import numpy as np
from scipy.stats import norm


def calculate_inventory_turnover(inventory_df: pd.DataFrame, group_cols=None) -> pd.DataFrame:
    """
    Inventory Turnover = Total Demand (proxy for COGS in units) / Average Inventory

    Higher turnover = inventory moves fast (efficient).
    Lower turnover = inventory sits idle (risk of obsolescence, tied-up capital).
    """
    if group_cols is None:
        group_cols = ["product_id"]

    grouped = inventory_df.groupby(group_cols).agg(
        total_demand=("demand_quantity", "sum"),
        avg_inventory=("closing_inventory", "mean")
    ).reset_index()

    grouped["turnover_ratio"] = grouped["total_demand"] / grouped["avg_inventory"].replace(0, np.nan)
    return grouped


def calculate_days_of_inventory(inventory_df: pd.DataFrame, group_cols=None) -> pd.DataFrame:
    """
    Days of Inventory = Average Inventory / Average Daily Demand

    Tells you how many days current stock will last at average consumption.
    """
    if group_cols is None:
        group_cols = ["product_id"]

    grouped = inventory_df.groupby(group_cols).agg(
        avg_inventory=("closing_inventory", "mean"),
        avg_daily_demand=("demand_quantity", "mean")
    ).reset_index()

    grouped["days_of_inventory"] = grouped["avg_inventory"] / grouped["avg_daily_demand"].replace(0, np.nan)
    return grouped


def calculate_safety_stock(
    demand_df: pd.DataFrame,
    lead_time_df: pd.DataFrame,
    service_level: float = 0.95,
    group_cols=None
) -> pd.DataFrame:
    """
    Safety Stock = Z * Demand_Std * sqrt(Lead Time)

    service_level: desired probability of not stocking out (0.95 = 95%)
    lead_time_df: must contain product_id (or join key) + avg_lead_time_days
    """
    if group_cols is None:
        group_cols = ["product_id"]

    z_score = norm.ppf(service_level)

    demand_std = demand_df.groupby(group_cols)["demand_quantity"].std().reset_index()
    demand_std.columns = group_cols + ["demand_std"]

    merged = demand_std.merge(lead_time_df, on=group_cols, how="left")
    merged["safety_stock"] = z_score * merged["demand_std"] * np.sqrt(merged["avg_lead_time_days"])

    return merged


def calculate_reorder_point(
    demand_df: pd.DataFrame,
    safety_stock_df: pd.DataFrame,
    lead_time_df: pd.DataFrame,
    group_cols=None
) -> pd.DataFrame:
    """
    Reorder Point = (Average Demand * Lead Time) + Safety Stock

    When inventory falls to this level, a new order should be placed.
    """
    if group_cols is None:
        group_cols = ["product_id"]

    avg_demand = demand_df.groupby(group_cols)["demand_quantity"].mean().reset_index()
    avg_demand.columns = group_cols + ["avg_demand"]

    merged = avg_demand.merge(lead_time_df, on=group_cols, how="left")
    merged = merged.merge(safety_stock_df[group_cols + ["safety_stock"]], on=group_cols, how="left")

    merged["reorder_point"] = (merged["avg_demand"] * merged["avg_lead_time_days"]) + merged["safety_stock"]

    return merged


def build_inventory_summary(
    inventory_df: pd.DataFrame,
    demand_df: pd.DataFrame,
    suppliers_df: pd.DataFrame,
    supplier_product_df: pd.DataFrame,
    service_level: float = 0.95
) -> pd.DataFrame:
    """
    Master function: runs all four calculations and merges into one summary table
    per product. This is what gets used by Streamlit and the shock simulator.
    """
    # Map each product to its (first/primary) supplier's lead time
    product_lead_time = supplier_product_df.merge(
        suppliers_df[["supplier_id", "avg_lead_time_days"]],
        on="supplier_id",
        how="left"
    ).groupby("product_id")["avg_lead_time_days"].mean().reset_index()

    turnover = calculate_inventory_turnover(inventory_df)
    days_inv = calculate_days_of_inventory(inventory_df)
    safety_stock = calculate_safety_stock(demand_df, product_lead_time, service_level)
    reorder = calculate_reorder_point(demand_df, safety_stock, product_lead_time)

    summary = turnover.merge(days_inv[["product_id", "days_of_inventory"]], on="product_id", how="left")
    summary = summary.merge(safety_stock[["product_id", "safety_stock"]], on="product_id", how="left")
    summary = summary.merge(reorder[["product_id", "reorder_point"]], on="product_id", how="left")

    return summary