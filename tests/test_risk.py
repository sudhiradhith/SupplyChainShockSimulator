"""
tests/test_risk.py
Unit tests for 5-dimension supplier risk scoring and band classifications.
"""

import pytest
import pandas as pd
import numpy as np
from src.analytics.risk import (
    normalize_0_100,
    calculate_delay_risk,
    calculate_reliability_risk,
    calculate_capacity_risk,
    calculate_quality_risk,
    calculate_dependency_risk,
    calculate_supplier_risk
)


def test_normalize_0_100():
    s = pd.Series([10, 20, 30])
    # Higher is riskier
    norm_high = normalize_0_100(s, higher_is_riskier=True)
    assert norm_high.iloc[0] == 0.0
    assert norm_high.iloc[2] == 100.0

    # Higher is safer (inverted)
    norm_low = normalize_0_100(s, higher_is_riskier=False)
    assert norm_low.iloc[0] == 100.0
    assert norm_low.iloc[2] == 0.0

    # No variance
    s_const = pd.Series([10, 10, 10])
    assert (normalize_0_100(s_const) == 0.0).all()


def test_calculate_supplier_risk_composite():
    supp_df = pd.DataFrame({
        "supplier_id": ["S001", "S002"],
        "supplier_name": ["Supplier 1", "Supplier 2"],
        "on_time_delivery_rate": [0.95, 0.70],
        "capacity_per_day": [1000, 200],
        "quality_score": [0.98, 0.80]
    })
    ship_df = pd.DataFrame({
        "supplier_id": ["S001", "S002"],
        "calculated_delay_days": [1.0, 8.0]
    })
    supp_prod_df = pd.DataFrame({
        "supplier_id": ["S001", "S002"],
        "product_id": ["P001", "P002"]
    })
    prod_df = pd.DataFrame({
        "product_id": ["P001", "P002"],
        "criticality": ["High", "Low"]
    })

    risk_df = calculate_supplier_risk(supp_df, ship_df, supp_prod_df, prod_df)
    assert not risk_df.empty
    assert "supplier_risk_score" in risk_df.columns
    assert "risk_band" in risk_df.columns

    # S002 has higher delay, lower on-time, lower capacity -> must have higher risk score
    s1_score = risk_df.loc[risk_df["supplier_id"] == "S001", "supplier_risk_score"].values[0]
    s2_score = risk_df.loc[risk_df["supplier_id"] == "S002", "supplier_risk_score"].values[0]
    assert s2_score > s1_score
