"""
src/optimization/strategies.py
Evaluates mitigation strategies for a given shock scenario and
recommends the one with the highest net benefit.
"""

import pandas as pd
import numpy as np


def evaluate_do_nothing(revenue_at_risk: float) -> dict:
    """Baseline: no mitigation action taken. Cost = 0, but full revenue is lost."""
    return {
        "strategy": "Do Nothing",
        "cost": 0.0,
        "revenue_saved": 0.0,
        "net_benefit": 0.0
    }


def evaluate_expedite_shipment(
    revenue_at_risk: float,
    expedite_cost_per_unit: float,
    units_at_risk: float,
    recovery_fraction: float = 0.90
) -> dict:
    """
    Expediting a shipment (air freight, priority carrier) recovers most
    of the at-risk revenue but costs extra per unit shipped faster.
    """
    cost = units_at_risk * expedite_cost_per_unit
    revenue_saved = revenue_at_risk * recovery_fraction
    net_benefit = revenue_saved - cost
    return {
        "strategy": "Expedite Shipment",
        "cost": round(float(cost), 2),
        "revenue_saved": round(float(revenue_saved), 2),
        "net_benefit": round(float(net_benefit), 2)
    }


def evaluate_alternate_supplier(
    revenue_at_risk: float,
    switching_cost: float,
    alt_supplier_unit_cost_premium: float,
    units_at_risk: float,
    recovery_fraction: float = 0.95
) -> dict:
    """
    Switching to an alternate supplier recovers most of the revenue but
    incurs a one-time switching cost plus a per-unit cost premium.
    """
    cost = switching_cost + (units_at_risk * alt_supplier_unit_cost_premium)
    revenue_saved = revenue_at_risk * recovery_fraction
    net_benefit = revenue_saved - cost
    return {
        "strategy": "Alternate Supplier",
        "cost": round(float(cost), 2),
        "revenue_saved": round(float(revenue_saved), 2),
        "net_benefit": round(float(net_benefit), 2)
    }


def evaluate_warehouse_transfer(
    revenue_at_risk: float,
    transfer_cost_per_unit: float,
    units_available_elsewhere: float,
    avg_price: float,
    units_at_risk: float
) -> dict:
    """
    Moving inventory from another warehouse. Capped by available inventory elsewhere.
    """
    units_transferable = min(units_available_elsewhere, units_at_risk)
    cost = units_transferable * transfer_cost_per_unit
    revenue_saved = units_transferable * avg_price
    net_benefit = revenue_saved - cost
    return {
        "strategy": "Warehouse Transfer",
        "cost": round(float(cost), 2),
        "revenue_saved": round(float(revenue_saved), 2),
        "net_benefit": round(float(net_benefit), 2)
    }


def recommend_strategy(
    shock_result: dict,
    inventory_df: pd.DataFrame,
    cost_assumptions: dict = None
) -> dict:
    """
    Takes the output of simulate_supplier_delay() (or a Monte Carlo summary)
    and evaluates all four strategies, returning a comparison table plus
    the recommended one.
    """
    defaults = {
        "expedite_cost_per_unit": 15.0,
        "switching_cost": 400000.0,
        "alt_supplier_unit_cost_premium": 5.0,
        "transfer_cost_per_unit": 3.0,
    }
    if cost_assumptions:
        defaults.update(cost_assumptions)

    revenue_at_risk = float(shock_result.get("total_revenue_at_risk", 0.0))
    units_at_risk = float(shock_result.get("total_lost_units", 0.0))

    detail = shock_result.get("detail", pd.DataFrame())
    if isinstance(detail, pd.DataFrame) and not detail.empty and "product_id" in detail.columns:
        affected_ids = detail["product_id"].unique()
        if inventory_df is not None and not inventory_df.empty and "date_id" in inventory_df.columns:
            latest_date = inventory_df["date_id"].max()
            matching = inventory_df[
                (inventory_df["product_id"].isin(affected_ids)) &
                (inventory_df["date_id"] == latest_date)
            ]
            col = "closing_inventory" if "closing_inventory" in matching.columns else "avg_inventory"
            network_stock = float(matching[col].sum()) if (not matching.empty and col in matching.columns) else 0.0
        elif inventory_df is not None and not inventory_df.empty and "product_id" in inventory_df.columns:
            matching = inventory_df[inventory_df["product_id"].isin(affected_ids)]
            col = "closing_inventory" if "closing_inventory" in matching.columns else "avg_inventory"
            network_stock = float(matching[col].sum()) if (not matching.empty and col in matching.columns) else 0.0
        else:
            network_stock = 0.0
    else:
        network_stock = 0.0

    avg_price = (revenue_at_risk / units_at_risk) if units_at_risk > 0 else 0.0

    strategies = [
        evaluate_do_nothing(revenue_at_risk),
        evaluate_expedite_shipment(
            revenue_at_risk, defaults["expedite_cost_per_unit"], units_at_risk
        ),
        evaluate_alternate_supplier(
            revenue_at_risk, defaults["switching_cost"],
            defaults["alt_supplier_unit_cost_premium"], units_at_risk
        ),
        evaluate_warehouse_transfer(
            revenue_at_risk, defaults["transfer_cost_per_unit"],
            network_stock, avg_price, units_at_risk
        ),
    ]

    strategies_df = pd.DataFrame(strategies).sort_values("net_benefit", ascending=False).reset_index(drop=True)
    best = strategies_df.iloc[0]

    return {
        "recommendation": best["strategy"],
        "expected_cost": float(best["cost"]),
        "revenue_saved": float(best["revenue_saved"]),
        "net_benefit": float(best["net_benefit"]),
        "strategies": strategies_df
    }