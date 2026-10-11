"""
src/api/schemas.py
Pydantic data schemas for FastAPI REST API endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any


class SupplierDelayRequest(BaseModel):
    supplier_id: str = Field(..., examples=["S001"])
    delay_days: int = Field(14, ge=1, le=120, examples=[14])
    as_of_date: Optional[str] = None


class DemandShockRequest(BaseModel):
    demand_increase_pct: float = Field(0.30, ge=0.01, le=5.0, examples=[0.30])
    product_id: Optional[str] = Field(None, examples=["P001"])
    as_of_date: Optional[str] = None


class CapacityShockRequest(BaseModel):
    supplier_id: str = Field(..., examples=["S001"])
    capacity_reduction_pct: float = Field(0.40, ge=0.01, le=1.0, examples=[0.40])


class TransportShockRequest(BaseModel):
    transit_delay_days: int = Field(7, ge=1, le=60, examples=[7])
    affected_warehouse_id: Optional[str] = Field(None, examples=["WH001"])


class CombinedShockRequest(BaseModel):
    supplier_id: str = Field(..., examples=["S001"])
    delay_days: int = Field(14, ge=1, le=120, examples=[14])
    demand_increase_pct: float = Field(0.25, ge=0.0, le=5.0, examples=[0.25])
    capacity_reduction_pct: float = Field(0.30, ge=0.0, le=1.0, examples=[0.30])
    transit_delay_days: int = Field(0, ge=0, le=60, examples=[7])


class MonteCarloRequest(BaseModel):
    supplier_id: str = Field(..., examples=["S001"])
    n_iterations: int = Field(5000, ge=10, le=50000, examples=[5000])
    random_seed: int = Field(42, examples=[42])


class StrategyOptimizationRequest(BaseModel):
    supplier_id: str = Field(..., examples=["S001"])
    delay_days: int = Field(14, ge=1, le=120, examples=[14])
    expedite_cost_per_unit: Optional[float] = Field(15.0, examples=[15.0])
    switching_cost: Optional[float] = Field(400000.0, examples=[400000.0])
    alt_supplier_unit_cost_premium: Optional[float] = Field(5.0, examples=[5.0])
    transfer_cost_per_unit: Optional[float] = Field(3.0, examples=[3.0])


class GenericResponse(BaseModel):
    success: bool
    data: Any
    message: Optional[str] = None
