"""
src/simulation/supplier_shock.py
Simulates the impact of a supplier delivery delay on inventory, stockouts, and revenue.
Optimized for high performance and high-iteration Monte Carlo simulations.
"""

import pandas as pd
import numpy as np


def build_simulation_context(
    inventory_df: pd.DataFrame,
    demand_df: pd.DataFrame,
    supplier_product_df: pd.DataFrame,
    products_df: pd.DataFrame,
    as_of_date: str = None
) -> dict:
    """
    Precomputes latest inventory positions, consumption rates, and prices per product.
    Allows thousands of simulation iterations to run in milliseconds.
    """
    if as_of_date is None:
        as_of_date = inventory_df["date_id"].max()

    # Filter inventory up to as_of_date
    if pd.api.types.is_datetime64_any_dtype(inventory_df["date_id"]):
        inv_filtered = inventory_df[inventory_df["date_id"] <= pd.to_datetime(as_of_date)]
    else:
        inv_filtered = inventory_df[inventory_df["date_id"].astype(str) <= str(as_of_date)]

    # Get the latest closing inventory per product (summed across warehouses)
    latest_date = inv_filtered["date_id"].max()
    latest_inv = inv_filtered[inv_filtered["date_id"] == latest_date].groupby("product_id")["closing_inventory"].sum()

    # Precompute average daily demand across the network and average unit price per product
    date_col = "date" if "date" in demand_df.columns else "date_id"
    if date_col in demand_df.columns:
        daily_totals = demand_df.groupby(["product_id", date_col])["demand_quantity"].sum().reset_index()
        avg_daily_demand_series = daily_totals.groupby("product_id")["demand_quantity"].mean()
    else:
        avg_daily_demand_series = demand_df.groupby("product_id")["demand_quantity"].mean()

    avg_price_series = demand_df.groupby("product_id")["price"].mean()

    # Calculate Days of Inventory (DOI) buffer per SKU
    inv_per_wh = inv_filtered.groupby("product_id")["closing_inventory"].mean()
    dem_per_wh = demand_df.groupby("product_id")["demand_quantity"].mean()
    doi_series = (inv_per_wh / dem_per_wh.replace(0, np.nan)).fillna(14.0)

    # Product names mapping
    prod_names = dict(zip(products_df["product_id"], products_df["product_name"]))

    # Supplier to products mapping
    supp_prods = supplier_product_df.groupby("supplier_id")["product_id"].unique().to_dict()

    # Build per-product master state dict
    product_state = {}
    for pid in products_df["product_id"].unique():
        dts = float(doi_series.get(pid, 14.0))
        avg_dem = float(avg_daily_demand_series.get(pid, 0.0))
        avg_prc = float(avg_price_series.get(pid, 0.0))
        curr_inv = dts * avg_dem

        product_state[pid] = {
            "product_id": pid,
            "product_name": prod_names.get(pid, pid),
            "current_inventory": curr_inv,
            "avg_daily_demand": avg_dem,
            "avg_price": avg_prc,
            "days_to_stockout": dts,
        }

    return {
        "as_of_date": as_of_date,
        "product_state": product_state,
        "supplier_products": supp_prods,
    }


def build_simulation_context_from_summary(
    inventory_summary_df: pd.DataFrame,
    products_df: pd.DataFrame,
    supplier_product_df: pd.DataFrame,
    as_of_date: str = "2024-12-31"
) -> dict:
    """
    Instantly builds simulation context from precomputed summary tables in microseconds (<1ms)
    without needing to query or scan heavy historical raw tables.
    """
    prod_names = dict(zip(products_df["product_id"], products_df["product_name"]))
    price_col = "selling_price" if "selling_price" in products_df.columns else ("price" if "price" in products_df.columns else "unit_cost")
    prod_prices = dict(zip(products_df["product_id"], products_df[price_col]))
    supp_prods = supplier_product_df.groupby("supplier_id")["product_id"].unique().to_dict()

    inv_sum = inventory_summary_df.set_index("product_id")
    product_state = {}

    for pid in products_df["product_id"].unique():
        if pid in inv_sum.index:
            row = inv_sum.loc[pid]
            dts = float(row.get("days_of_inventory", 14.0))
            if "avg_daily_demand" in row:
                avg_dem = float(row["avg_daily_demand"])
            elif "total_demand" in row:
                avg_dem = float(row["total_demand"]) / 730.0
            else:
                avg_dem = 50.0
            curr_inv = float(row.get("avg_inventory", row.get("closing_inventory", dts * avg_dem)))
        else:
            dts = 14.0
            avg_dem = 50.0
            curr_inv = dts * avg_dem

        avg_prc = float(prod_prices.get(pid, 100.0))

        product_state[pid] = {
            "product_id": pid,
            "product_name": prod_names.get(pid, pid),
            "current_inventory": curr_inv,
            "avg_daily_demand": avg_dem,
            "avg_price": avg_prc,
            "days_to_stockout": dts,
        }

    return {
        "as_of_date": as_of_date,
        "product_state": product_state,
        "supplier_products": supp_prods,
    }


def simulate_supplier_delay(
    supplier_id: str,
    delay_days: int,
    inventory_df: pd.DataFrame = None,
    demand_df: pd.DataFrame = None,
    supplier_product_df: pd.DataFrame = None,
    products_df: pd.DataFrame = None,
    as_of_date: str = None,
    context: dict = None
) -> dict:
    """
    Given a supplier delay, estimate affected products, expected stockout dates,
    lost units, and lost revenue.
    """
    if context is None:
        if inventory_df is None or demand_df is None or supplier_product_df is None or products_df is None:
            raise ValueError("Must provide either context or all raw DataFrames.")
        context = build_simulation_context(inventory_df, demand_df, supplier_product_df, products_df, as_of_date)

    supp_prods = context["supplier_products"]
    affected_products = supp_prods.get(supplier_id, np.array([]))

    if len(affected_products) == 0:
        return {
            "supplier_id": supplier_id,
            "delay_days": delay_days,
            "affected_products": 0,
            "products_stocked_out": 0,
            "total_lost_units": 0.0,
            "total_revenue_at_risk": 0.0,
            "detail": pd.DataFrame(),
            "error": f"No products found for supplier {supplier_id}"
        }

    product_state = context["product_state"]
    results = []

    for product_id in affected_products:
        p_state = product_state.get(product_id)
        if not p_state or p_state["avg_daily_demand"] <= 0:
            continue

        current_inventory = p_state["current_inventory"]
        avg_daily_demand = p_state["avg_daily_demand"]
        avg_price = p_state["avg_price"]
        days_to_stockout = p_state["days_to_stockout"]

        stockout_occurs = delay_days > days_to_stockout

        if stockout_occurs:
            days_out_of_stock = delay_days - days_to_stockout
            lost_units = days_out_of_stock * avg_daily_demand
            lost_revenue = lost_units * avg_price
        else:
            days_out_of_stock = 0.0
            lost_units = 0.0
            lost_revenue = 0.0

        results.append({
            "product_id": product_id,
            "product_name": p_state["product_name"],
            "current_inventory": round(current_inventory, 1),
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
        "total_lost_units": round(float(results_df["lost_units"].sum()), 1) if not results_df.empty else 0.0,
        "total_revenue_at_risk": round(float(results_df["lost_revenue"].sum()), 2) if not results_df.empty else 0.0,
        "detail": results_df
    }

    return summary