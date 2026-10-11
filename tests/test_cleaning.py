"""
tests/test_cleaning.py
Unit tests for data cleaning and validation functions.
"""

import pytest
import pandas as pd
import numpy as np
from src.cleaning.clean_data import clean_shipments_data, clean_inventory_data, clean_demand_data


def test_clean_shipments_data():
    raw_data = pd.DataFrame({
        "shipment_id": ["SH001", "SH002"],
        "order_date": ["2026-01-01", "2026-01-02"],
        "shipment_date": ["2026-01-03", "2026-01-04"],
        "expected_delivery": ["2026-01-08", "2026-01-10"],
        "actual_delivery": ["2026-01-12", "2026-01-09"],
        "quantity": ["100", "250"],
        "shipping_cost": ["500.5", "1200.0"]
    })

    cleaned = clean_shipments_data(raw_data)
    assert "calculated_delay_days" in cleaned.columns
    assert cleaned["calculated_delay_days"].iloc[0] == 4  # 12 - 8
    assert cleaned["calculated_delay_days"].iloc[1] == -1 # 9 - 10 (early)
    assert cleaned["quantity"].dtype in [np.float64, np.int64]
    assert cleaned["shipping_cost"].iloc[0] == 500.5


def test_clean_inventory_data():
    raw_data = pd.DataFrame({
        "inventory_id": ["INV001", "INV002"],
        "date_id": ["2026-01-01", "2026-01-02"],
        "opening_inventory": [500, -20],
        "received_quantity": [100, "invalid"],
        "demand_quantity": [50, 60],
        "closing_inventory": [550, 100]
    })

    cleaned = clean_inventory_data(raw_data)
    assert cleaned["opening_inventory"].iloc[1] == 0 # negative clipped
    assert cleaned["received_quantity"].iloc[1] == 0 # invalid parsed to 0
    assert pd.api.types.is_datetime64_any_dtype(cleaned["date_id"])


def test_clean_demand_data():
    raw_data = pd.DataFrame({
        "demand_id": ["D001"],
        "date_id": ["2026-01-01"],
        "demand_quantity": [-10],
        "price": [120.5]
    })

    cleaned = clean_demand_data(raw_data)
    assert cleaned["demand_quantity"].iloc[0] == 0
    assert cleaned["price"].iloc[0] == 120.5
