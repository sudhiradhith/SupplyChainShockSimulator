"""
src/simulation/capacity_shock.py
Simulates a supplier capacity reduction.
"""

import pandas as pd
import numpy as np


def simulate_capacity_shock(
    supplier_id: str,
    capacity_reduction_pct: float,
    supplier_product_df: pd.DataFrame,
    suppliers_df: pd.DataFrame,
    demand_df: pd.DataFrame,
    products_df: pd.DataFrame
) -> dict:
    """
    capacity_reduction_pct: e.g. 0.50 for a 50% capacity cut.
    Estimates the supply shortfall against demand for products this supplier serves.
    """
    supplier_row = suppliers_df[suppliers_df["supplier_id"] == supplier_id]
    if supplier_row.empty:
        return {
            "supplier_id": supplier_id,
            "normal_capacity": 0.0,
            "new_capacity": 0.0,
            "capacity_lost_per_day": 0.0,
            "affected_products": 0,
            "total_revenue_at_risk_per_day": 0.0,
            "detail": pd.DataFrame(),
            "error": f"Supplier {supplier_id} not found"
        }

    normal_capacity = float(supplier_row["capacity_per_day"].values[0])
    new_capacity = normal_capacity * (1 - capacity_reduction_pct)
    capacity_lost = normal_capacity - new_capacity

    affected_products = supplier_product_df[
        supplier_product_df["supplier_id"] == supplier_id
    ]["product_id"].unique()

    if len(affected_products) == 0:
        return {
            "supplier_id": supplier_id,
            "normal_capacity": normal_capacity,
            "new_capacity": new_capacity,
            "capacity_lost_per_day": round(capacity_lost, 2),
            "affected_products": 0,
            "total_revenue_at_risk_per_day": 0.0,
            "detail": pd.DataFrame()
        }

    # Demand and price lookup
    demand_stats = demand_df.groupby("product_id").agg(
        avg_daily_demand=("demand_quantity", "mean"),
        avg_price=("price", "mean")
    )
    prod_names = dict(zip(products_df["product_id"], products_df["product_name"]))

    results = []
    shortfall_units_per_day = capacity_lost / len(affected_products)

    for pid in affected_products:
        d_stat = demand_stats.loc[pid] if pid in demand_stats.index else None
        avg_daily_demand = float(d_stat["avg_daily_demand"]) if d_stat is not None else 0.0
        avg_price = float(d_stat["avg_price"]) if d_stat is not None else 0.0
        revenue_at_risk_per_day = shortfall_units_per_day * avg_price

        results.append({
            "product_id": pid,
            "product_name": prod_names.get(pid, pid),
            "avg_daily_demand": round(avg_daily_demand, 2),
            "shortfall_units_per_day": round(shortfall_units_per_day, 2),
            "revenue_at_risk_per_day": round(revenue_at_risk_per_day, 2),
        })

    results_df = pd.DataFrame(results)

    return {
        "supplier_id": supplier_id,
        "normal_capacity": normal_capacity,
        "new_capacity": new_capacity,
        "capacity_lost_per_day": round(capacity_lost, 2),
        "affected_products": len(results_df),
        "total_revenue_at_risk_per_day": round(float(results_df["revenue_at_risk_per_day"].sum()), 2) if not results_df.empty else 0.0,
        "detail": results_df
    }