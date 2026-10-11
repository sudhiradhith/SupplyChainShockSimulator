# Mathematical & Simulation Methodology

**Project:** Supply Chain Resilience & Shock Intelligence Platform  

---

## 1. Inventory Policy Formulas

### A. Days of Inventory (DOI)
$$\text{DOI}_p = \frac{I_p^{\text{closing}}}{\bar{D}_p}$$
Where $I_p^{\text{closing}}$ is the latest aggregate closing inventory for product $p$, and $\bar{D}_p$ is the historical average daily demand.

### B. Safety Stock (SS)
$$\text{SS}_p = Z \times \sigma_{D, p} \times \sqrt{\bar{L}_p}$$
- $Z$: Normal distribution critical value for desired service level ($Z = 1.645$ for 95% service level).
- $\sigma_{D, p}$: Standard deviation of daily demand for product $p$.
- $\bar{L}_p$: Mean supplier lead time in days.

### C. Reorder Point (ROP)
$$\text{ROP}_p = (\bar{D}_p \times \bar{L}_p) + \text{SS}_p$$

---

## 2. Supplier Composite Risk Formulation

Each dimension is normalized onto a $0 - 100$ scale:
$$\text{Normalized Score} = \frac{x - x_{\min}}{x_{\max} - x_{\min}} \times 100$$
Where higher values indicate greater risk.

$$\text{Composite Score} = 0.30 \cdot R_{\text{delay}} + 0.25 \cdot R_{\text{reliability}} + 0.20 \cdot R_{\text{capacity}} + 0.15 \cdot R_{\text{quality}} + 0.10 \cdot R_{\text{dependency}}$$

---

## 3. Disruption Shock Mathematical Models

### A. Supplier Delivery Delay Model
Given supplier $s$ delayed by $\Delta t$ days:
1. Days until stockout without replenishment:
   $$t_{\text{stockout}, p} = \frac{I_p^{\text{closing}}}{\bar{D}_p}$$
2. Stockout condition:
   $$\text{Stockout} = \Delta t > t_{\text{stockout}, p}$$
3. Days out of stock:
   $$t_{\text{out}, p} = \max(0, \Delta t - t_{\text{stockout}, p})$$
4. Lost units & lost revenue:
   $$U_{\text{lost}, p} = t_{\text{out}, p} \times \bar{D}_p$$
   $$\text{Revenue at Risk} = \sum_{p \in \mathcal{P}_s} \left( U_{\text{lost}, p} \times P_p \right)$$

### B. Probabilistic Monte Carlo Formulation
Given stochastic delay distribution $\mathcal{D}$:
$$\mathbb{P}(\text{Delay} = d_k) = w_k, \quad \sum w_k = 1$$
For $N = 5,000$ iterations:
1. Sample vector $\mathbf{d} = [d_1, d_2, \dots, d_N]^T \sim \mathcal{D}$.
2. Compute matrix of out-of-stock days $\mathbf{T} \in \mathbb{R}^{N \times |\mathcal{P}_s|}$:
   $$T_{i, p} = \max(0, d_i - t_{\text{stockout}, p})$$
3. Compute simulated revenue loss vector $\mathbf{L} \in \mathbb{R}^N$:
   $$L_i = \sum_{p} T_{i, p} \times \bar{D}_p \times P_p$$
4. Compute probabilistic metrics:
   $$\mathbb{E}[\text{Loss}] = \frac{1}{N} \sum_{i=1}^N L_i, \quad P_{95} = \text{Percentile}(\mathbf{L}, 95), \quad P_{\text{stockout}} = \frac{1}{N} \sum_{i=1}^N \mathbb{I}(L_i > 0) \times 100\%$$

---

## 4. Mitigation Strategy Optimization Formulations

$$\text{Net Benefit} = \text{Revenue Saved} - \text{Mitigation Cost}$$

| Strategy | Revenue Saved Formulation | Mitigation Cost Formulation |
| :--- | :--- | :--- |
| **Do Nothing** | ₹0.00 | ₹0.00 |
| **Expedite Shipment** | $0.90 \times \text{Revenue at Risk}$ | $U_{\text{lost}} \times C_{\text{expedite}}$ |
| **Alternate Supplier** | $0.95 \times \text{Revenue at Risk}$ | $C_{\text{switch}} + (U_{\text{lost}} \times C_{\text{premium}})$ |
| **Warehouse Transfer** | $\min(I_{\text{network}}, U_{\text{lost}}) \times \bar{P}$ | $\min(I_{\text{network}}, U_{\text{lost}}) \times C_{\text{transfer}}$ |
