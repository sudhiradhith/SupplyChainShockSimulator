# Product Requirements Document (PRD)

**Project:** Supply Chain Resilience & Shock Intelligence Platform (`SupplyChainShockSimulator`)  
**Owner:** Sudhir  
**Target Roles:** Data Analyst / Data Scientist / AI Engineer  
**Status:** Production Ready  

---

## 1. Executive Summary & Problem Statement

Global supply chains face constant vulnerability from single-point supplier disruptions, sudden consumer demand spikes, logistics corridor blockages, and capacity shortfalls. When a disruption occurs, enterprise leaders face critical questions:
1. **Financial Impact**: How much revenue is at risk, and when will stockouts occur across the network?
2. **Vulnerability Identification**: Which suppliers, SKUs, and distribution centers are most vulnerable?
3. **Probabilistic Exposure**: What is the probability of stockouts across stochastic lead time variations?
4. **Actionable Mitigation**: What operational action (Expedited Air Freight, Alternate Sourcing, Inter-Warehouse Transfers) yields the maximum net financial benefit?

The **Supply Chain Resilience & Shock Intelligence Platform** is an enterprise-grade analytical and simulation platform answering these exact questions through data analytics, machine learning demand forecasting, vectorized Monte Carlo stress-testing, and algorithmic mitigation optimization.

---

## 2. Target Personas & Use Cases

| Persona | Primary Needs & Workflow | Relevant Module |
| :--- | :--- | :--- |
| **VP of Supply Chain** | Strategic portfolio risk, high-risk supplier concentration, network health KPIs. | `01 Executive Overview`, `02 Supplier Intelligence` |
| **Operations Manager** | Days of Inventory (DOI), safety stock compliance, reorder points, stockout timing. | `03 Inventory Intelligence`, `05 Shock Simulator` |
| **Demand Planner** | 30-day forward demand forecasting, model error comparisons (MAE, RMSE, MAPE). | `04 Demand Forecast` |
| **Chief Financial Officer (CFO)** | Revenue at risk, Monte Carlo worst-case losses, mitigation cost vs ROI. | `06 Scenario Comparison`, `07 Recommendations` |

---

## 3. System Architecture & Tech Stack

- **Database**: PostgreSQL Star Schema (Managed in DBeaver / SQLAlchemy).
- **Core Engine**: Python 3.12, Pandas 2.x, NumPy, SciPy, Statsmodels, Scikit-learn, XGBoost.
- **Frontend Dashboard**: Streamlit multi-page application with custom CSS and Plotly visuals.
- **API Services**: FastAPI RESTful microservice with Pydantic validation.
- **Testing & Quality**: Pytest automated testing suite with 30+ unit & integration tests.
- **DevOps & Containers**: Docker & Docker Compose multi-service architecture.

---

## 4. Feature Specifications

### 4.1 Supplier Risk Engine (5-Dimension Composite)
Suppliers are scored from 0 to 100 based on a weighted composite formula:
$$\text{Risk Score} = 0.30 \times \text{Delay} + 0.25 \times \text{Reliability} + 0.20 \times \text{Capacity} + 0.15 \times \text{Quality} + 0.10 \times \text{Dependency}$$
- **LOW**: $\le 30$
- **MEDIUM**: $31 - 60$
- **HIGH**: $61 - 80$
- **CRITICAL**: $> 80$

### 4.2 Inventory Intelligence & Reorder Policies
- **Inventory Turnover**: $\text{Turns} = \frac{\text{Total Demand}}{\text{Average Inventory}}$
- **Days of Inventory (DOI)**: $\text{DOI} = \frac{\text{Current Inventory}}{\text{Average Daily Demand}}$
- **Safety Stock**: $\text{SS} = Z \times \sigma_{\text{demand}} \times \sqrt{\text{Lead Time}}$ ($Z = 1.645$ for 95% service level)
- **Reorder Point**: $\text{ROP} = (\mu_{\text{demand}} \times \text{Lead Time}) + \text{SS}$

### 4.3 Demand Forecasting (Multi-Model Horizon)
- **Moving Average**: 7-day rolling window baseline.
- **Exponential Smoothing**: Holt-Winters with additive weekly seasonality (period = 7).
- **XGBoost Regressor**: Supervised gradient-boosted trees utilizing lag features (1, 2, 3, 7, 14 days), rolling statistics, and calendar features.

### 4.4 Disruption Shock Simulation
Simulates single or combined multi-vector shocks:
1. **Supplier Delivery Delay**: Projects stockout timing, lost units, and revenue at risk.
2. **Demand Surge**: Accelerates stockout dates under sudden % demand surges.
3. **Capacity Cut**: Quantifies daily supply shortfalls.
4. **Transport Route Delay**: Inbound transit delay and demurrage holding penalties.
5. **Combined Shock**: Simultaneous disruption simulation.

### 4.5 Vectorized Monte Carlo Probabilistic Stress-Testing
Samples 5,000+ stochastic lead time delay iterations in $< 0.1$ seconds over empirical delay probability distributions, generating probability of stockout, Expected Loss (P50), Severe Tail Risk (P95), and Worst-Case Loss.

### 4.6 Mitigation Decision Matrix
Evaluates four response strategies:
$$\text{Net Benefit} = \text{Revenue Saved} - \text{Mitigation Cost}$$
1. **Do Nothing**: Baseline unmitigated loss.
2. **Expedited Air Freight**: Recovers 90% revenue at per-unit expedite cost.
3. **Alternate Supplier**: Recovers 95% revenue with one-time switching cost + unit premium.
4. **Warehouse Transfer**: Transfers stock from network hubs at per-unit transit cost.
