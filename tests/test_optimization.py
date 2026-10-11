"""
tests/test_optimization.py
Unit tests for mitigation strategy evaluation, cost calculations, and ranking.
"""

import pytest
import pandas as pd
from src.optimization.strategies import (
    evaluate_do_nothing,
    evaluate_expedite_shipment,
    evaluate_alternate_supplier,
    evaluate_warehouse_transfer,
    recommend_strategy
)


def test_evaluate_do_nothing():
    res = evaluate_do_nothing(50000.0)
    assert res["strategy"] == "Do Nothing"
    assert res["cost"] == 0.0
    assert res["revenue_saved"] == 0.0
    assert res["net_benefit"] == 0.0


def test_evaluate_expedite_shipment():
    # Rev at risk = 100k, Units = 1000, Expedite cost = 15/unit -> Cost = 15k, Saved = 90k -> Net = 75k
    res = evaluate_expedite_shipment(100000.0, 15.0, 1000.0, recovery_fraction=0.90)
    assert res["strategy"] == "Expedite Shipment"
    assert res["cost"] == 15000.0
    assert res["revenue_saved"] == 90000.0
    assert res["net_benefit"] == 75000.0


def test_evaluate_alternate_supplier():
    # Switching cost = 10k, Premium = 5/unit, Units = 1000 -> Cost = 15k, Saved = 95k -> Net = 80k
    res = evaluate_alternate_supplier(100000.0, 10000.0, 5.0, 1000.0, recovery_fraction=0.95)
    assert res["strategy"] == "Alternate Supplier"
    assert res["cost"] == 15000.0
    assert res["revenue_saved"] == 95000.0
    assert res["net_benefit"] == 80000.0


def test_recommend_strategy():
    shock_result = {
        "total_revenue_at_risk": 150000.0,
        "total_lost_units": 1500.0,
        "detail": pd.DataFrame({"product_id": ["P001"]})
    }
    inv_df = pd.DataFrame({
        "product_id": ["P001"],
        "date_id": ["2026-01-01"],
        "closing_inventory": [5000.0]
    })

    rec = recommend_strategy(shock_result, inv_df)
    assert "recommendation" in rec
    assert "net_benefit" in rec
    assert isinstance(rec["strategies"], pd.DataFrame)
    assert len(rec["strategies"]) == 4
    # Highest net benefit must be the top recommendation
    assert rec["recommendation"] == rec["strategies"].iloc[0]["strategy"]
