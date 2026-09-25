"""
src/simulation/combined_shock.py
Runs supplier delay + demand increase + capacity reduction together
and aggregates the total impact.
"""

import pandas as pd
from simulation.supplier_shock import simulate_supplier_delay
from simulation.demand_shock import simulate_demand_shock
from simulation.capacity_shock import simulate_capacity_shock


def simulate_combined_shock(
    supplier_id: str,
    delay_days: int,
    demand_increase_pct: float,
    capacity_reduction_pct: float,
    inventory_df: pd.DataFrame,
    demand_df: pd.DataFrame,
    supplier_product_df: pd.DataFrame,
    suppliers_df: pd.DataFrame,
    products_df: pd.DataFrame
) -> dict:
    delay_result = simulate_supplier_delay(
        supplier_id, delay_days, inventory_df, demand_df, supplier_product_df, products_df
    )
    demand_result = simulate_demand_shock(
        demand_increase_pct, inventory_df, demand_df, products_df
    )
    capacity_result = simulate_capacity_shock(
        supplier_id, capacity_reduction_pct, supplier_product_df, suppliers_df, demand_df, products_df
    )

    total_revenue_at_risk = (
        delay_result.get("total_revenue_at_risk", 0) +
        demand_result.get("total_revenue_at_risk", 0) +
        capacity_result.get("total_revenue_at_risk_per_day", 0) * delay_days  # scale capacity loss over the delay window
    )

    return {
        "supplier_id": supplier_id,
        "delay_days": delay_days,
        "demand_increase_pct": demand_increase_pct,
        "capacity_reduction_pct": capacity_reduction_pct,
        "supplier_delay_impact": delay_result,
        "demand_shock_impact": demand_result,
        "capacity_shock_impact": capacity_result,
        "total_revenue_at_risk": round(total_revenue_at_risk, 2)
    }