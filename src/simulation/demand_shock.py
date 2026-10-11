"""
src/simulation/demand_shock.py
Simulates the impact of a sudden demand increase.
"""

import pandas as pd
import numpy as np


def simulate_demand_shock(
    demand_increase_pct: float,
    inventory_df: pd.DataFrame = None,
    demand_df: pd.DataFrame = None,
    products_df: pd.DataFrame = None,
    product_id: str = None,
    as_of_date: str = None,
    context: dict = None
) -> dict:
    """
    demand_increase_pct: e.g. 0.40 for a 40% increase.
    If product_id is None, applies to all products.
    """
    if context is None:
        if inventory_df is None or demand_df is None or products_df is None:
            raise ValueError("Must provide either context or inventory_df, demand_df, products_df")
        from simulation.supplier_shock import build_simulation_context
        # Use a dummy supplier_product_df if not provided
        supp_prod_dummy = pd.DataFrame(columns=["supplier_id", "product_id"])
        context = build_simulation_context(inventory_df, demand_df, supp_prod_dummy, products_df, as_of_date)

    product_state = context["product_state"]
    target_products = [product_id] if product_id else list(product_state.keys())
    results = []

    for pid in target_products:
        p_state = product_state.get(pid)
        if not p_state or p_state["avg_daily_demand"] <= 0:
            continue

        current_inventory = p_state["current_inventory"]
        normal_demand = p_state["avg_daily_demand"]
        avg_price = p_state["avg_price"]

        shocked_demand = normal_demand * (1 + demand_increase_pct)
        days_to_stockout_normal = current_inventory / normal_demand
        days_to_stockout_shocked = current_inventory / shocked_demand

        days_advanced = days_to_stockout_normal - days_to_stockout_shocked
        extra_units_needed = (shocked_demand - normal_demand) * days_to_stockout_shocked
        revenue_at_risk = extra_units_needed * avg_price

        results.append({
            "product_id": pid,
            "product_name": p_state["product_name"],
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
        "total_revenue_at_risk": round(float(results_df["revenue_at_risk"].sum()), 2) if not results_df.empty else 0.0,
        "detail": results_df
    }