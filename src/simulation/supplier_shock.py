"""
src/simulation/supplier_shock.py
Simulates the impact of a supplier delivery delay on inventory, stockouts, and revenue.
"""

import pandas as pd
import numpy as np


def simulate_supplier_delay(
    supplier_id: str,
    delay_days: int,
    inventory_df: pd.DataFrame,
    demand_df: pd.DataFrame,
    supplier_product_df: pd.DataFrame,
    products_df: pd.DataFrame,
    as_of_date: str = None
) -> dict:
    """
    Given a supplier delay, estimate affected products, expected stockout dates,
    lost units, and lost revenue.
    """
    # which products does this supplier provide?
    affected_products = supplier_product_df[
        supplier_product_df["supplier_id"] == supplier_id
    ]["product_id"].unique()

    if len(affected_products) == 0:
        return {"error": f"No products found for supplier {supplier_id}"}

    if as_of_date is None:
        as_of_date = inventory_df["date_id"].max()
    as_of_date = pd.to_datetime(as_of_date)

    results = []

    for product_id in affected_products:
        # current inventory position (most recent snapshot as of the shock date)
        product_inv = inventory_df[
            (inventory_df["product_id"] == product_id) &
            (pd.to_datetime(inventory_df["date_id"]) <= as_of_date)
        ].sort_values("date_id")

        if product_inv.empty:
            continue

        current_inventory = product_inv["closing_inventory"].iloc[-1]

        # average daily demand for this product, across warehouses
        product_demand = demand_df[demand_df["product_id"] == product_id]
        avg_daily_demand = product_demand["demand_quantity"].mean()
        avg_price = product_demand["price"].mean()

        if avg_daily_demand <= 0 or pd.isna(avg_daily_demand):
            continue

        # days until stockout at current consumption rate, with no new supply
        days_to_stockout = current_inventory / avg_daily_demand

        # is the delay long enough to cause a stockout before replenishment?
        stockout_occurs = delay_days > days_to_stockout

        if stockout_occurs:
            days_out_of_stock = delay_days - days_to_stockout
            lost_units = days_out_of_stock * avg_daily_demand
            lost_revenue = lost_units * avg_price
        else:
            days_out_of_stock = 0
            lost_units = 0
            lost_revenue = 0

        product_name = products_df.loc[products_df["product_id"] == product_id, "product_name"]
        product_name = product_name.values[0] if len(product_name) > 0 else product_id

        results.append({
            "product_id": product_id,
            "product_name": product_name,
            "current_inventory": current_inventory,
            "avg_daily_demand": round(avg_daily_demand, 2),
            "days_to_stockout": round(days_to_stockout, 1),
            "stockout_occurs": stockout_occurs,
            "days_out_of_stock": round(days_out_of_stock, 1),
            "lost_units": round(lost_units, 1),
            "lost_revenue": round(lost_revenue, 2),
        })

    results_df = pd.DataFrame(results)

    summary = {
        "supplier_id": supplier_id,
        "delay_days": delay_days,
        "affected_products": len(results_df),
        "products_stocked_out": int(results_df["stockout_occurs"].sum()) if not results_df.empty else 0,
        "total_lost_units": round(results_df["lost_units"].sum(), 1) if not results_df.empty else 0,
        "total_revenue_at_risk": round(results_df["lost_revenue"].sum(), 2) if not results_df.empty else 0,
        "detail": results_df
    }

    return summary