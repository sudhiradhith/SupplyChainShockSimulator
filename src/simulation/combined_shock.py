"""
src/simulation/combined_shock.py
Runs supplier delay + demand increase + capacity reduction + transport shock together
and aggregates the total combined impact.
"""

import pandas as pd

try:
    from simulation.supplier_shock import simulate_supplier_delay, build_simulation_context
    from simulation.demand_shock import simulate_demand_shock
    from simulation.capacity_shock import simulate_capacity_shock
    from simulation.transport_shock import simulate_transport_shock
except ImportError:
    from src.simulation.supplier_shock import simulate_supplier_delay, build_simulation_context
    from src.simulation.demand_shock import simulate_demand_shock
    from src.simulation.capacity_shock import simulate_capacity_shock
    from src.simulation.transport_shock import simulate_transport_shock


def simulate_combined_shock(
    supplier_id: str,
    delay_days: int,
    demand_increase_pct: float,
    capacity_reduction_pct: float,
    transit_delay_days: int = 0,
    inventory_df: pd.DataFrame = None,
    demand_df: pd.DataFrame = None,
    supplier_product_df: pd.DataFrame = None,
    suppliers_df: pd.DataFrame = None,
    products_df: pd.DataFrame = None,
    shipments_df: pd.DataFrame = None,
    context: dict = None
) -> dict:
    if context is None and inventory_df is not None and demand_df is not None and supplier_product_df is not None and products_df is not None:
        context = build_simulation_context(inventory_df, demand_df, supplier_product_df, products_df)

    delay_result = simulate_supplier_delay(
        supplier_id, delay_days, inventory_df, demand_df, supplier_product_df, products_df, context=context
    )
    demand_result = simulate_demand_shock(
        demand_increase_pct, inventory_df, demand_df, products_df, context=context
    )
    capacity_result = simulate_capacity_shock(
        supplier_id, capacity_reduction_pct, supplier_product_df, suppliers_df, demand_df, products_df
    )

    transport_result = None
    transport_rev_risk = 0.0
    if transit_delay_days > 0 and shipments_df is not None:
        transport_result = simulate_transport_shock(
            transit_delay_days, shipments_df, demand_df, products_df
        )
        transport_rev_risk = transport_result.get("total_revenue_at_risk", 0.0)

    total_revenue_at_risk = (
        delay_result.get("total_revenue_at_risk", 0.0) +
        demand_result.get("total_revenue_at_risk", 0.0) +
        capacity_result.get("total_revenue_at_risk_per_day", 0.0) * delay_days +
        transport_rev_risk
    )

    return {
        "supplier_id": supplier_id,
        "delay_days": delay_days,
        "demand_increase_pct": demand_increase_pct,
        "capacity_reduction_pct": capacity_reduction_pct,
        "transit_delay_days": transit_delay_days,
        "supplier_delay_impact": delay_result,
        "demand_shock_impact": demand_result,
        "capacity_shock_impact": capacity_result,
        "transport_shock_impact": transport_result,
        "total_revenue_at_risk": round(total_revenue_at_risk, 2)
    }