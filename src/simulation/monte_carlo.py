"""
src/simulation/monte_carlo.py
Runs probabilistic shock simulations by sampling from a delay distribution
thousands of times and aggregating the outcomes with vectorized high performance.
"""

import numpy as np
import pandas as pd

try:
    from simulation.supplier_shock import build_simulation_context
except ImportError:
    from src.simulation.supplier_shock import build_simulation_context


def sample_delay_distribution(n_samples: int, distribution: dict = None) -> np.ndarray:
    """
    distribution: dict mapping delay_days -> probability, e.g.
        {3: 0.15, 7: 0.20, 14: 0.25, 21: 0.20, 30: 0.15, 45: 0.05}
    """
    if distribution is None:
        distribution = {3: 0.15, 7: 0.20, 14: 0.25, 21: 0.20, 30: 0.15, 45: 0.05}

    days = np.array(list(distribution.keys()), dtype=int)
    probs = np.array(list(distribution.values()), dtype=float)

    # normalize in case probabilities don't sum exactly to 1 due to rounding
    probs = probs / np.sum(probs)

    return np.random.choice(days, size=n_samples, p=probs)


def run_monte_carlo_supplier_delay(
    supplier_id: str,
    n_iterations: int = 5000,
    inventory_df: pd.DataFrame = None,
    demand_df: pd.DataFrame = None,
    supplier_product_df: pd.DataFrame = None,
    products_df: pd.DataFrame = None,
    distribution: dict = None,
    random_seed: int = 42,
    context: dict = None
) -> dict:
    """
    Vectorized Monte Carlo engine.
    Executes 5,000+ iterations in milliseconds by operating over precomputed product state vectors.
    """
    if context is None:
        if inventory_df is None or demand_df is None or supplier_product_df is None or products_df is None:
            raise ValueError("Must provide either context or raw DataFrames")
        context = build_simulation_context(inventory_df, demand_df, supplier_product_df, products_df)

    supp_prods = context["supplier_products"]
    affected_products = supp_prods.get(supplier_id, np.array([]))

    if len(affected_products) == 0:
        return {
            "supplier_id": supplier_id,
            "n_iterations": n_iterations,
            "stockout_probability": 0.0,
            "expected_revenue_loss": 0.0,
            "median_revenue_loss": 0.0,
            "worst_case_revenue_loss": 0.0,
            "percentile_95": 0.0,
            "percentile_5": 0.0,
            "std_revenue_loss": 0.0,
            "raw_results": np.zeros(n_iterations),
            "sampled_delays": np.zeros(n_iterations, dtype=int),
        }

    product_state = context["product_state"]

    # Build vector arrays for affected products
    days_to_stockout_list = []
    revenue_rate_per_day_list = []

    for pid in affected_products:
        p_state = product_state.get(pid)
        if not p_state or p_state["avg_daily_demand"] <= 0:
            continue
        days_to_stockout_list.append(p_state["days_to_stockout"])
        revenue_rate_per_day_list.append(p_state["avg_daily_demand"] * p_state["avg_price"])

    if len(days_to_stockout_list) == 0:
        return {
            "supplier_id": supplier_id,
            "n_iterations": n_iterations,
            "stockout_probability": 0.0,
            "expected_revenue_loss": 0.0,
            "median_revenue_loss": 0.0,
            "worst_case_revenue_loss": 0.0,
            "percentile_95": 0.0,
            "percentile_5": 0.0,
            "std_revenue_loss": 0.0,
            "raw_results": np.zeros(n_iterations),
            "sampled_delays": np.zeros(n_iterations, dtype=int),
        }

    # Arrays of shape (P,)
    dts_arr = np.array(days_to_stockout_list)
    rev_rate_arr = np.array(revenue_rate_per_day_list)

    # Sample delays array of shape (N,)
    np.random.seed(random_seed)
    sampled_delays = sample_delay_distribution(n_iterations, distribution)

    # Broadcast: (N, 1) - (1, P) -> (N, P)
    days_out_of_stock_matrix = np.maximum(0.0, sampled_delays[:, None] - dts_arr[None, :])
    revenue_losses_matrix = days_out_of_stock_matrix * rev_rate_arr[None, :]

    # Aggregate across products: shape (N,)
    revenue_losses = np.sum(revenue_losses_matrix, axis=1)
    stockout_flags = (np.sum(days_out_of_stock_matrix > 0, axis=1) > 0).astype(int)

    summary = {
        "supplier_id": supplier_id,
        "n_iterations": n_iterations,
        "stockout_probability": round(float(stockout_flags.mean() * 100), 1),
        "expected_revenue_loss": round(float(revenue_losses.mean()), 2),
        "median_revenue_loss": round(float(np.median(revenue_losses)), 2),
        "worst_case_revenue_loss": round(float(revenue_losses.max()), 2),
        "percentile_95": round(float(np.percentile(revenue_losses, 95)), 2),
        "percentile_5": round(float(np.percentile(revenue_losses, 5)), 2),
        "std_revenue_loss": round(float(revenue_losses.std()), 2),
        "raw_results": revenue_losses,
        "sampled_delays": sampled_delays,
    }

    return summary


def run_batch_monte_carlo_all_suppliers(
    suppliers_df: pd.DataFrame,
    inventory_df: pd.DataFrame,
    demand_df: pd.DataFrame,
    supplier_product_df: pd.DataFrame,
    products_df: pd.DataFrame,
    n_iterations: int = 5000,
    distribution: dict = None
) -> pd.DataFrame:
    """
    Runs Monte Carlo simulation for all suppliers in batch and generates a summary DataFrame.
    """
    context = build_simulation_context(inventory_df, demand_df, supplier_product_df, products_df)
    results = []

    for sid in suppliers_df["supplier_id"].unique():
        mc = run_monte_carlo_supplier_delay(
            sid,
            n_iterations=n_iterations,
            distribution=distribution,
            context=context
        )
        results.append({
            "supplier_id": sid,
            "stockout_probability": mc["stockout_probability"],
            "expected_revenue_loss": mc["expected_revenue_loss"],
            "median_revenue_loss": mc["median_revenue_loss"],
            "worst_case_revenue_loss": mc["worst_case_revenue_loss"],
            "percentile_95": mc["percentile_95"],
            "percentile_5": mc["percentile_5"],
            "std_revenue_loss": mc["std_revenue_loss"],
        })

    return pd.DataFrame(results).sort_values("expected_revenue_loss", ascending=False).reset_index(drop=True)