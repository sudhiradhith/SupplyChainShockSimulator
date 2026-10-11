"""
src/simulation/transport_shock.py
Simulates the impact of freight transit / logistics lane disruptions (e.g. port delays, route blockages).
"""

import pandas as pd
import numpy as np


def simulate_transport_shock(
    transit_delay_days: int,
    shipments_df: pd.DataFrame,
    demand_df: pd.DataFrame,
    products_df: pd.DataFrame,
    affected_warehouse_id: str = None,
    demurrage_cost_per_unit_day: float = 0.50
) -> dict:
    """
    Simulates inbound transport lane delays.
    Quantifies delayed shipment volume, delayed inventory value, demurrage/holding penalty,
    and revenue exposure from inbound replenishment blockage.
    """
    if shipments_df.empty:
        return {
            "transit_delay_days": transit_delay_days,
            "affected_shipments_count": 0,
            "total_delayed_units": 0.0,
            "total_delayed_value": 0.0,
            "demurrage_cost": 0.0,
            "total_revenue_at_risk": 0.0,
            "detail": pd.DataFrame()
        }

    # Filter shipments by target warehouse if specified
    active_shipments = shipments_df.copy()
    if affected_warehouse_id:
        active_shipments = active_shipments[active_shipments["warehouse_id"] == affected_warehouse_id]

    # Precompute average product prices
    product_prices = demand_df.groupby("product_id")["price"].mean().to_dict()
    product_names = dict(zip(products_df["product_id"], products_df["product_name"]))

    # Group by product
    summary_by_product = active_shipments.groupby("product_id").agg(
        shipment_count=("shipment_id", "count"),
        total_quantity=("quantity", "sum"),
        avg_shipping_cost=("shipping_cost", "mean")
    ).reset_index()

    results = []
    for _, row in summary_by_product.iterrows():
        pid = row["product_id"]
        qty = float(row["total_quantity"])
        price = product_prices.get(pid, 50.0)
        delayed_value = qty * price

        # Disruption penalty: holding cost + lost revenue potential from stock depletion
        holding_penalty = qty * demurrage_cost_per_unit_day * transit_delay_days
        revenue_at_risk = delayed_value * min(1.0, (transit_delay_days / 30.0)) + holding_penalty

        results.append({
            "product_id": pid,
            "product_name": product_names.get(pid, pid),
            "shipment_count": int(row["shipment_count"]),
            "delayed_units": round(qty, 1),
            "unit_price": round(price, 2),
            "delayed_inventory_value": round(delayed_value, 2),
            "demurrage_holding_cost": round(holding_penalty, 2),
            "revenue_at_risk": round(revenue_at_risk, 2),
        })

    results_df = pd.DataFrame(results)

    total_delayed_units = float(results_df["delayed_units"].sum()) if not results_df.empty else 0.0
    total_delayed_value = float(results_df["delayed_inventory_value"].sum()) if not results_df.empty else 0.0
    total_demurrage = float(results_df["demurrage_holding_cost"].sum()) if not results_df.empty else 0.0
    total_rev_risk = float(results_df["revenue_at_risk"].sum()) if not results_df.empty else 0.0

    return {
        "transit_delay_days": transit_delay_days,
        "affected_warehouse_id": affected_warehouse_id or "ALL_WAREHOUSES",
        "affected_shipments_count": len(active_shipments),
        "total_delayed_units": round(total_delayed_units, 1),
        "total_delayed_value": round(total_delayed_value, 2),
        "demurrage_cost": round(total_demurrage, 2),
        "total_revenue_at_risk": round(total_rev_risk, 2),
        "detail": results_df
    }
