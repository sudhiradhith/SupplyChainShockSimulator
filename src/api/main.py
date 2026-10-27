"""
src/api/main.py
FastAPI REST microservice for the Supply Chain Resilience & Shock Intelligence Platform.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from pathlib import Path
import sys
import os

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

try:
    from src.api.schemas import (
        SupplierDelayRequest,
        DemandShockRequest,
        CapacityShockRequest,
        TransportShockRequest,
        CombinedShockRequest,
        MonteCarloRequest,
        StrategyOptimizationRequest,
        GenericResponse
    )
    from src.simulation.supplier_shock import simulate_supplier_delay, build_simulation_context, build_simulation_context_from_summary
    from src.simulation.demand_shock import simulate_demand_shock
    from src.simulation.capacity_shock import simulate_capacity_shock
    from src.simulation.transport_shock import simulate_transport_shock
    from src.simulation.combined_shock import simulate_combined_shock
    from src.simulation.monte_carlo import run_monte_carlo_supplier_delay
    from src.optimization.strategies import recommend_strategy
except ImportError:
    from api.schemas import (
        SupplierDelayRequest,
        DemandShockRequest,
        CapacityShockRequest,
        TransportShockRequest,
        CombinedShockRequest,
        MonteCarloRequest,
        StrategyOptimizationRequest,
        GenericResponse
    )
    from simulation.supplier_shock import simulate_supplier_delay, build_simulation_context, build_simulation_context_from_summary
    from simulation.demand_shock import simulate_demand_shock
    from simulation.capacity_shock import simulate_capacity_shock
    from simulation.transport_shock import simulate_transport_shock
    from simulation.combined_shock import simulate_combined_shock
    from simulation.monte_carlo import run_monte_carlo_supplier_delay
    from optimization.strategies import recommend_strategy

from fastapi.responses import RedirectResponse

app = FastAPI(
    title="Supply Chain Resilience & Shock Intelligence API",
    description="REST API for disruption modeling, Monte Carlo risk simulation, and mitigation optimization.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load data at startup
DATA_DIR = PROJECT_ROOT / "data" / "processed"
RAW_DIR = PROJECT_ROOT / "data" / "raw"

suppliers_df = pd.read_csv(RAW_DIR / "suppliers.csv")
products_df = pd.read_csv(RAW_DIR / "products.csv")
warehouses_df = pd.read_csv(RAW_DIR / "warehouses.csv")
supplier_product_df = pd.read_csv(RAW_DIR / "supplier_products.csv")

inventory_summary_df = pd.read_parquet(DATA_DIR / "inventory_summary.parquet")
supplier_risk_df = pd.read_parquet(DATA_DIR / "supplier_risk.parquet")
forecast_comp_df = pd.read_parquet(DATA_DIR / "forecast_comparison.parquet")
best_forecast_df = pd.read_parquet(DATA_DIR / "best_forecast_model_per_product.parquet")

# Ultra-fast microsecond simulation context (<1ms)
sim_context = build_simulation_context_from_summary(inventory_summary_df, products_df, supplier_product_df)


@app.get("/", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "service": "SupplyChainShockSimulator API", "version": "1.0.0"}


@app.get("/api/v1/suppliers", tags=["Metadata"])
def get_suppliers():
    return GenericResponse(success=True, data=suppliers_df.to_dict(orient="records"))


@app.get("/api/v1/products", tags=["Metadata"])
def get_products():
    return GenericResponse(success=True, data=products_df.to_dict(orient="records"))


@app.get("/api/v1/inventory/summary", tags=["Inventory"])
def get_inventory_summary():
    return GenericResponse(success=True, data=inventory_summary_df.to_dict(orient="records"))


@app.get("/api/v1/risk/suppliers", tags=["Supplier Risk"])
def get_supplier_risk():
    return GenericResponse(success=True, data=supplier_risk_df.to_dict(orient="records"))


@app.get("/api/v1/forecast/{product_id}", tags=["Forecasting"])
def get_product_forecast(product_id: str):
    product_evals = forecast_comp_df[forecast_comp_df["product_id"] == product_id]
    best = best_forecast_df[best_forecast_df["product_id"] == product_id]
    if product_evals.empty:
        raise HTTPException(status_code=404, detail=f"No forecast records found for product {product_id}")
    return GenericResponse(success=True, data={
        "product_id": product_id,
        "evaluations": product_evals.to_dict(orient="records"),
        "best_model": best.to_dict(orient="records") if not best.empty else None
    })


@app.post("/api/v1/simulate/supplier-delay", tags=["Simulation"])
def api_simulate_supplier_delay(req: SupplierDelayRequest):
    res = simulate_supplier_delay(req.supplier_id, req.delay_days, context=sim_context, as_of_date=req.as_of_date)
    if "detail" in res and isinstance(res["detail"], pd.DataFrame):
        res["detail"] = res["detail"].to_dict(orient="records")
    return GenericResponse(success=True, data=res)


@app.post("/api/v1/simulate/demand-shock", tags=["Simulation"])
def api_simulate_demand_shock(req: DemandShockRequest):
    res = simulate_demand_shock(req.demand_increase_pct, product_id=req.product_id, context=sim_context, as_of_date=req.as_of_date)
    if "detail" in res and isinstance(res["detail"], pd.DataFrame):
        res["detail"] = res["detail"].to_dict(orient="records")
    return GenericResponse(success=True, data=res)


@app.post("/api/v1/simulate/capacity-shock", tags=["Simulation"])
def api_simulate_capacity_shock(req: CapacityShockRequest):
    res = simulate_capacity_shock(req.supplier_id, req.capacity_reduction_pct, supplier_product_df, suppliers_df, demand_df, products_df)
    if "detail" in res and isinstance(res["detail"], pd.DataFrame):
        res["detail"] = res["detail"].to_dict(orient="records")
    return GenericResponse(success=True, data=res)


@app.post("/api/v1/simulate/transport-shock", tags=["Simulation"])
def api_simulate_transport_shock(req: TransportShockRequest):
    res = simulate_transport_shock(req.transit_delay_days, shipments_df, demand_df, products_df, affected_warehouse_id=req.affected_warehouse_id)
    if "detail" in res and isinstance(res["detail"], pd.DataFrame):
        res["detail"] = res["detail"].to_dict(orient="records")
    return GenericResponse(success=True, data=res)


@app.post("/api/v1/simulate/combined-shock", tags=["Simulation"])
def api_simulate_combined_shock(req: CombinedShockRequest):
    res = simulate_combined_shock(
        req.supplier_id, req.delay_days, req.demand_increase_pct, req.capacity_reduction_pct,
        transit_delay_days=req.transit_delay_days,
        inventory_df=inventory_df, demand_df=demand_df, supplier_product_df=supplier_product_df,
        suppliers_df=suppliers_df, products_df=products_df, shipments_df=shipments_df,
        context=sim_context
    )
    if "supplier_delay_impact" in res and "detail" in res["supplier_delay_impact"] and isinstance(res["supplier_delay_impact"]["detail"], pd.DataFrame):
        res["supplier_delay_impact"]["detail"] = res["supplier_delay_impact"]["detail"].to_dict(orient="records")
    return GenericResponse(success=True, data=res)


@app.post("/api/v1/simulate/monte-carlo", tags=["Simulation"])
def api_simulate_monte_carlo(req: MonteCarloRequest):
    res = run_monte_carlo_supplier_delay(req.supplier_id, n_iterations=req.n_iterations, random_seed=req.random_seed, context=sim_context)
    # Convert numpy arrays for JSON serialization
    res["raw_results"] = res["raw_results"][:100].tolist() # sample head for response size
    res["sampled_delays"] = res["sampled_delays"][:100].tolist()
    return GenericResponse(success=True, data=res)


@app.post("/api/v1/recommendations", tags=["Optimization"])
def api_recommend_strategy(req: StrategyOptimizationRequest):
    shock_res = simulate_supplier_delay(req.supplier_id, req.delay_days, context=sim_context)
    cost_assumptions = {
        "expedite_cost_per_unit": req.expedite_cost_per_unit,
        "switching_cost": req.switching_cost,
        "alt_supplier_unit_cost_premium": req.alt_supplier_unit_cost_premium,
        "transfer_cost_per_unit": req.transfer_cost_per_unit
    }
    opt_res = recommend_strategy(shock_res, inventory_df, cost_assumptions)
    if "strategies" in opt_res and isinstance(opt_res["strategies"], pd.DataFrame):
        opt_res["strategies"] = opt_res["strategies"].to_dict(orient="records")
    return GenericResponse(success=True, data=opt_res)
