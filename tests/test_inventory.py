"""
tests/test_inventory.py
Unit tests for inventory intelligence and reorder policy formulas.
"""

import pytest
import pandas as pd
import numpy as np
from src.analytics.inventory import (
    calculate_inventory_turnover,
    calculate_days_of_inventory,
    calculate_safety_stock,
    calculate_reorder_point,
    build_inventory_summary
)


def test_calculate_inventory_turnover():
    inv_df = pd.DataFrame({
        "product_id": ["P001", "P001"],
        "demand_quantity": [50.0, 50.0],
        "closing_inventory": [20.0, 20.0]
    })
    res = calculate_inventory_turnover(inv_df)
    assert not res.empty
    assert res.iloc[0]["turnover_ratio"] == 5.0 # 100 / 20 = 5.0


def test_calculate_days_of_inventory():
    inv_df = pd.DataFrame({
        "product_id": ["P001", "P001"],
        "demand_quantity": [30.0, 30.0],
        "closing_inventory": [300.0, 300.0]
    })
    res = calculate_days_of_inventory(inv_df)
    assert not res.empty
    assert res.iloc[0]["days_of_inventory"] == 10.0 # 300 / 30 = 10.0


def test_calculate_safety_stock():
    dem_df = pd.DataFrame({
        "product_id": ["P001", "P001", "P001"],
        "demand_quantity": [10.0, 20.0, 30.0]
    })
    lead_time_df = pd.DataFrame({
        "product_id": ["P001"],
        "avg_lead_time_days": [4.0]
    })
    res = calculate_safety_stock(dem_df, lead_time_df, service_level=0.95)
    assert not res.empty
    assert "safety_stock" in res.columns
    assert res.iloc[0]["safety_stock"] > 0


def test_calculate_reorder_point():
    dem_df = pd.DataFrame({
        "product_id": ["P001"],
        "demand_quantity": [50.0]
    })
    lead_time_df = pd.DataFrame({
        "product_id": ["P001"],
        "avg_lead_time_days": [5.0]
    })
    safety_stock_df = pd.DataFrame({
        "product_id": ["P001"],
        "safety_stock": [25.0]
    })
    res = calculate_reorder_point(dem_df, safety_stock_df, lead_time_df)
    assert not res.empty
    assert res.iloc[0]["reorder_point"] == 275.0 # 50*5 + 25 = 275


def test_build_inventory_summary():
    inv_df = pd.DataFrame({
        "product_id": ["P001", "P001"],
        "demand_quantity": [20.0, 30.0],
        "closing_inventory": [100.0, 150.0]
    })
    dem_df = pd.DataFrame({
        "product_id": ["P001", "P001"],
        "demand_quantity": [20.0, 30.0]
    })
    supp_df = pd.DataFrame({
        "supplier_id": ["S001"],
        "avg_lead_time_days": [4.0]
    })
    supp_prod_df = pd.DataFrame({
        "supplier_id": ["S001"],
        "product_id": ["P001"]
    })

    summary = build_inventory_summary(inv_df, dem_df, supp_df, supp_prod_df)
    assert not summary.empty
    assert summary.iloc[0]["product_id"] == "P001"
    assert "days_of_inventory" in summary.columns
    assert "safety_stock" in summary.columns
    assert "reorder_point" in summary.columns
