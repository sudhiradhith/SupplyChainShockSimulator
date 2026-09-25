"""
src/simulation/monte_carlo.py
Runs probabilistic shock simulations by sampling from a delay distribution
thousands of times and aggregating the outcomes.
"""

import numpy as np
import pandas as pd
from simulation.supplier_shock import simulate_supplier_delay


def sample_delay_distribution(n_samples: int, distribution: dict = None) -> np.ndarray:
    """
    distribution: dict mapping delay_days -> probability, e.g.
        {2: 0.10, 5: 0.20, 7: 0.30, 10: 0.25, 14: 0.10, 21: 0.05}
    If None, uses the default distribution from your project plan.
    """
    if distribution is None:
        distribution = {2: 0.10, 5: 0.20, 7: 0.30, 10: 0.25, 14: 0.10, 21: 0.05}

    days = list(distribution.keys())
    probs = list(distribution.values())

    # normalize in case probabilities don't sum exactly to 1 due to rounding
    probs = np.array(probs) / np.sum(probs)

    return np.random.choice(days, size=n_samples, p=probs)


def run_monte_carlo_supplier_delay(
    supplier_id: str,
    n_iterations: int,
    inventory_df: pd.DataFrame,
    demand_df: pd.DataFrame,
    supplier_product_df: pd.DataFrame,
    products_df: pd.DataFrame,
    distribution: dict = None,
    random_seed: int = 42
) -> dict:
    """
    Runs simulate_supplier_delay() n_iterations times, sampling delay_days
    from the given distribution each time. Returns the full distribution
    of outcomes plus summary statistics.
    """
    np.random.seed(random_seed)
    sampled_delays = sample_delay_distribution(n_iterations, distribution)

    revenue_losses = []
    stockout_flags = []

    for delay in sampled_delays:
        result = simulate_supplier_delay(
            supplier_id, int(delay), inventory_df, demand_df, supplier_product_df, products_df
        )
        revenue_losses.append(result.get("total_revenue_at_risk", 0))
        stockout_flags.append(1 if result.get("products_stocked_out", 0) > 0 else 0)

    revenue_losses = np.array(revenue_losses)
    stockout_flags = np.array(stockout_flags)

    summary = {
        "supplier_id": supplier_id,
        "n_iterations": n_iterations,
        "stockout_probability": round(stockout_flags.mean() * 100, 1),
        "expected_revenue_loss": round(revenue_losses.mean(), 2),
        "median_revenue_loss": round(np.median(revenue_losses), 2),
        "worst_case_revenue_loss": round(revenue_losses.max(), 2),
        "percentile_95": round(np.percentile(revenue_losses, 95), 2),
        "percentile_5": round(np.percentile(revenue_losses, 5), 2),
        "std_revenue_loss": round(revenue_losses.std(), 2),
        "raw_results": revenue_losses,
        "sampled_delays": sampled_delays,
    }

    return summary