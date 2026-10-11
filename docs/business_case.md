# Executive Business Case & Financial Impact

**Project:** Supply Chain Resilience & Shock Intelligence Platform  

---

## 1. Executive Summary

Unmitigated supply chain shocks result in millions in lost revenue, customer churn, and operational inefficiency. This platform provides executive decision-makers with the tools to predict, quantify, and mitigate disruptions before they impact customer fulfillment.

---

## 2. Quantitative ROI & Financial Analysis

### Representative Scenario: 14-Day Delivery Disruption on Primary Supplier (S001)
- **Unmitigated Revenue at Risk**: **₹1,391,515.26** across 4 critical SKUs.
- **Stockout Timing**: SKUs stock out within **2.9 to 5.1 days** without intervention.

### Strategic Mitigation Decision Matrix:
| Mitigation Option | Implementation Spend | Revenue Preserved | Net Financial Benefit | Recommendation |
| :--- | :---: | :---: | :---: | :---: |
| **Do Nothing** | ₹0.00 | ₹0.00 | -₹1,391,515.26 | ❌ High Loss |
| **Alternate Supplier** | ₹418,348.50 | ₹1,321,939.50 | **+₹903,591.00** | ⚠️ Viable |
| **Warehouse Transfer** | ₹11,009.10 | ₹1,391,515.26 | **+₹1,380,506.16** | 🏆 **Top Recommended Action** |
| **Expedited Air Freight** | ₹55,045.50 | ₹1,252,363.73 | **+₹1,197,318.23** | 🥈 Strong Alternative |

> **Key Financial Takeaway**: Implementing an automated inter-warehouse inventory rebalancing or expedited freight recovery preserves **over 95% of customer revenue**, generating **₹1.38M in net benefit** against a modest execution cost.

---

## 3. Portfolio Resume & Project Narrative Highlights

- **Supply Chain Resilience Engineering**: Designed and deployed an end-to-end resilience modeling platform answering critical financial and operational disruption questions.
- **High-Performance Monte Carlo Engine**: Architected a vectorized stochastic simulation engine executing **100,000 Monte Carlo iterations in $< 0.1$ seconds** across 20 global suppliers.
- **Machine Learning Demand Forecasting**: Benchmarked Moving Average, Holt-Winters Exponential Smoothing, and XGBoost regressors with lag and calendar feature engineering across a 30-day holdout horizon.
- **Modular Multi-Page Interactive Dashboard**: Built an enterprise 7-page Streamlit dashboard featuring 5-dimension radar scoring, what-if shock scenario controls, and ROI optimization decision matrices.
- **Microservice & REST API**: Engineered a modular FastAPI backend with Pydantic schemas, 30+ automated Pytest unit/integration tests, and Docker containerization.
