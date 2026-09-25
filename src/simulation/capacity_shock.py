"""
src/simulation/capacity_shock.py
Simulates a supplier capacity reduction.
"""

import pandas as pd


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
        return {"error": f"Supplier {supplier_id} not found"}

    normal_capacity = supplier_row["capacity_per_day"].values[0]
    new_capacity = normal_capacity * (1 - capacity_reduction_pct)
    capacity_lost = normal_capacity - new_capacity

    affected_products = supplier_product_df[
        supplier_product_df["supplier_id"] == supplier_id
    ]["product_id"].unique()

    results = []
    for pid in affected_products:
        product_demand = demand_df[demand_df["product_id"] == pid]
        avg_daily_demand = product_demand["demand_quantity"].mean()
        avg_price = product_demand["price"].mean()

        product_name = products_df.loc[products_df["product_id"] == pid, "product_name"]
        product_name = product_name.values[0] if len(product_name) > 0 else pid

        # proportional share of capacity loss allocated per product (simple even split)
        shortfall_units_per_day = capacity_lost / len(affected_products)
        revenue_at_risk_per_day = shortfall_units_per_day * avg_price

        results.append({
            "product_id": pid,
            "product_name": product_name,
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
        "total_revenue_at_risk_per_day": round(results_df["revenue_at_risk_per_day"].sum(), 2) if not results_df.empty else 0,
        "detail": results_df
    }