"""
src/simulation/demand_shock.py
Simulates the impact of a sudden demand increase.
"""

import pandas as pd


def simulate_demand_shock(
    demand_increase_pct: float,
    inventory_df: pd.DataFrame,
    demand_df: pd.DataFrame,
    products_df: pd.DataFrame,
    product_id: str = None,
    as_of_date: str = None
) -> dict:
    """
    demand_increase_pct: e.g. 0.40 for a 40% increase.
    If product_id is None, applies to all products.
    """
    if as_of_date is None:
        as_of_date = inventory_df["date_id"].max()
    as_of_date = pd.to_datetime(as_of_date)

    target_products = [product_id] if product_id else demand_df["product_id"].unique()
    results = []

    for pid in target_products:
        product_inv = inventory_df[
            (inventory_df["product_id"] == pid) &
            (pd.to_datetime(inventory_df["date_id"]) <= as_of_date)
        ].sort_values("date_id")

        if product_inv.empty:
            continue

        current_inventory = product_inv["closing_inventory"].iloc[-1]

        product_demand = demand_df[demand_df["product_id"] == pid]
        normal_demand = product_demand["demand_quantity"].mean()
        avg_price = product_demand["price"].mean()

        if normal_demand <= 0 or pd.isna(normal_demand):
            continue

        shocked_demand = normal_demand * (1 + demand_increase_pct)
        days_to_stockout_normal = current_inventory / normal_demand
        days_to_stockout_shocked = current_inventory / shocked_demand

        days_advanced = days_to_stockout_normal - days_to_stockout_shocked
        extra_units_needed = (shocked_demand - normal_demand) * days_to_stockout_shocked
        revenue_at_risk = extra_units_needed * avg_price

        product_name = products_df.loc[products_df["product_id"] == pid, "product_name"]
        product_name = product_name.values[0] if len(product_name) > 0 else pid

        results.append({
            "product_id": pid,
            "product_name": product_name,
            "normal_demand": round(normal_demand, 2),
            "shocked_demand": round(shocked_demand, 2),
            "days_to_stockout_normal": round(days_to_stockout_normal, 1),
            "days_to_stockout_shocked": round(days_to_stockout_shocked, 1),
            "stockout_date_moved_up_by_days": round(days_advanced, 1),
            "revenue_at_risk": round(revenue_at_risk, 2),
        })

    results_df = pd.DataFrame(results)

    return {
        "demand_increase_pct": demand_increase_pct,
        "affected_products": len(results_df),
        "total_revenue_at_risk": round(results_df["revenue_at_risk"].sum(), 2) if not results_df.empty else 0,
        "detail": results_df
    }