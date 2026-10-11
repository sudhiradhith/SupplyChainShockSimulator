"""
tests/test_api.py
Integration tests for FastAPI REST API endpoints using TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_get_suppliers():
    response = client.get("/api/v1/suppliers")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert len(json_data["data"]) == 20


def test_get_products():
    response = client.get("/api/v1/products")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert len(json_data["data"]) == 20


def test_get_supplier_risk():
    response = client.get("/api/v1/risk/suppliers")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert len(json_data["data"]) == 20


def test_simulate_supplier_delay_endpoint():
    payload = {"supplier_id": "S001", "delay_days": 14}
    response = client.post("/api/v1/simulate/supplier-delay", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    data = json_data["data"]
    assert "total_revenue_at_risk" in data
    assert data["supplier_id"] == "S001"


def test_simulate_monte_carlo_endpoint():
    payload = {"supplier_id": "S001", "n_iterations": 500, "random_seed": 42}
    response = client.post("/api/v1/simulate/monte-carlo", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    data = json_data["data"]
    assert "stockout_probability" in data
    assert "expected_revenue_loss" in data


def test_recommendations_endpoint():
    payload = {
        "supplier_id": "S001",
        "delay_days": 14,
        "expedite_cost_per_unit": 15.0,
        "switching_cost": 400000.0,
        "alt_supplier_unit_cost_premium": 5.0,
        "transfer_cost_per_unit": 3.0
    }
    response = client.post("/api/v1/recommendations", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    data = json_data["data"]
    assert "recommendation" in data
    assert "net_benefit" in data
