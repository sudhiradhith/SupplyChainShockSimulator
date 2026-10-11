"""
tests/test_simulation.py
Unit tests for all operational shock models, boundary tests, and Monte Carlo convergence.
"""

import pytest
import pandas as pd
import numpy as np
from src.simulation.supplier_shock import simulate_supplier_delay, build_simulation_context
from src.simulation.demand_shock import simulate_demand_shock
from src.simulation.capacity_shock import simulate_capacity_shock
from src.simulation.transport_shock import simulate_transport_shock
from src.simulation.combined_shock import simulate_combined_shock
from src.simulation.monte_carlo import run_monte_carlo_supplier_delay


@pytest.fixture
def mock_sc_data():
    inv_df = pd.DataFrame({
        "inventory_id": ["I1", "I2"],
        "date_id": ["2026-01-01", "2026-01-02"],
        "product_id": ["P001", "P001"],
        "closing_inventory": [100.0, 100.0]
    })
    dem_df = pd.DataFrame({
        "demand_id": ["D1", "D2"],
        "date_id": ["2026-01-01", "2026-01-02"],
        "product_id": ["P001", "P001"],
        "demand_quantity": [10.0, 10.0],
        "price": [50.0, 50.0]
    })
    supp_prod_df = pd.DataFrame({
        "supplier_id": ["S001"],
        "product_id": ["P001"]
    })
    prod_df = pd.DataFrame({
        "product_id": ["P001"],
        "product_name": ["Widget A"]
    })
    supp_df = pd.DataFrame({
        "supplier_id": ["S001"],
        "supplier_name": ["Supplier 1"],
        "capacity_per_day": [500.0]
    })
    ship_df = pd.DataFrame({
        "shipment_id": ["SH1"],
        "supplier_id": ["S001"],
        "product_id": ["P001"],
        "warehouse_id": ["WH001"],
        "quantity": [200.0],
        "shipping_cost": [1000.0]
    })
    return {
        "inv": inv_df, "dem": dem_df, "supp_prod": supp_prod_df,
        "prod": prod_df, "supp": supp_df, "ship": ship_df
    }


def test_supplier_delay_shock(mock_sc_data):
    # Days to stockout = 100 / 10 = 10 days
    # Delay = 14 days -> Out of stock = 4 days -> Lost units = 4 * 10 = 40 -> Lost rev = 40 * 50 = 2000
    res = simulate_supplier_delay(
        "S001", 14,
        inventory_df=mock_sc_data["inv"],
        demand_df=mock_sc_data["dem"],
        supplier_product_df=mock_sc_data["supp_prod"],
        products_df=mock_sc_data["prod"]
    )
    assert res["affected_products"] == 1
    assert res["products_stocked_out"] == 1
    assert res["total_lost_units"] == 40.0
    assert res["total_revenue_at_risk"] == 2000.0


def test_supplier_zero_delay_boundary(mock_sc_data):
    # Zero delay -> No revenue loss
    res = simulate_supplier_delay(
        "S001", 0,
        inventory_df=mock_sc_data["inv"],
        demand_df=mock_sc_data["dem"],
        supplier_product_df=mock_sc_data["supp_prod"],
        products_df=mock_sc_data["prod"]
    )
    assert res["total_revenue_at_risk"] == 0.0
    assert res["total_lost_units"] == 0.0


def test_demand_shock(mock_sc_data):
    # Demand surge 50%
    res = simulate_demand_shock(
        0.50,
        inventory_df=mock_sc_data["inv"],
        demand_df=mock_sc_data["dem"],
        products_df=mock_sc_data["prod"]
    )
    assert res["affected_products"] == 1
    assert res["total_revenue_at_risk"] > 0


def test_capacity_shock(mock_sc_data):
    res = simulate_capacity_shock(
        "S001", 0.50,
        mock_sc_data["supp_prod"], mock_sc_data["supp"],
        mock_sc_data["dem"], mock_sc_data["prod"]
    )
    assert res["affected_products"] == 1
    assert res["capacity_lost_per_day"] == 250.0


def test_transport_shock(mock_sc_data):
    res = simulate_transport_shock(
        7, mock_sc_data["ship"], mock_sc_data["dem"], mock_sc_data["prod"]
    )
    assert res["affected_shipments_count"] == 1
    assert res["total_delayed_units"] == 200.0
    assert res["total_revenue_at_risk"] > 0


def test_monte_carlo_fast_convergence(mock_sc_data):
    res = run_monte_carlo_supplier_delay(
        "S001", n_iterations=500,
        inventory_df=mock_sc_data["inv"],
        demand_df=mock_sc_data["dem"],
        supplier_product_df=mock_sc_data["supp_prod"],
        products_df=mock_sc_data["prod"]
    )
    assert res["n_iterations"] == 500
    assert "stockout_probability" in res
    assert "expected_revenue_loss" in res
    assert res["worst_case_revenue_loss"] >= res["expected_revenue_loss"]
