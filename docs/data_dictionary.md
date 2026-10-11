# Data Dictionary

**Project:** Supply Chain Resilience & Shock Intelligence Platform  

---

## 1. Table: `dim_supplier`
| Column Name | Data Type | Description | Sample Value |
| :--- | :--- | :--- | :--- |
| `supplier_id` | VARCHAR(10) | Primary Key for suppliers | `S001` |
| `supplier_name` | VARCHAR(100) | Name of supplier enterprise | `Global Components` |
| `country` | VARCHAR(50) | Country of origin | `India` |
| `capacity_per_day` | INT | Maximum daily production capacity | `1500` |
| `quality_score` | FLOAT | Historical quality inspection rate ($0.0 - 1.0$) | `0.96` |
| `on_time_delivery_rate` | FLOAT | Historical on-time delivery rate ($0.0 - 1.0$) | `0.92` |
| `avg_lead_time_days` | FLOAT | Historical average shipment lead time in days | `5.2` |

---

## 2. Table: `dim_product`
| Column Name | Data Type | Description | Sample Value |
| :--- | :--- | :--- | :--- |
| `product_id` | VARCHAR(10) | Primary Key for products (SKUs) | `P001` |
| `product_name` | VARCHAR(100) | Commercial SKU title | `Precision Steel Fastener` |
| `category` | VARCHAR(50) | Product category classification | `Hardware` |
| `unit_cost` | FLOAT | Direct manufacturing / purchase cost (₹) | `85.00` |
| `price` | FLOAT | Customer selling price (₹) | `120.00` |
| `criticality` | VARCHAR(20) | Operational criticality (`Low`, `Medium`, `High`, `Critical`) | `High` |

---

## 3. Table: `dim_warehouse`
| Column Name | Data Type | Description | Sample Value |
| :--- | :--- | :--- | :--- |
| `warehouse_id` | VARCHAR(10) | Primary Key for fulfillment centers | `WH001` |
| `warehouse_name` | VARCHAR(100) | Facility name | `North Regional Hub` |
| `city` | VARCHAR(50) | Location city | `Delhi` |
| `capacity` | INT | Pallet storage capacity | `50000` |
| `latitude` | FLOAT | Geographic latitude | `28.6139` |
| `longitude` | FLOAT | Geographic longitude | `77.2090` |

---

## 4. Table: `dim_date`
| Column Name | Data Type | Description | Sample Value |
| :--- | :--- | :--- | :--- |
| `date_id` | DATE | Primary Key (Calendar Date) | `2026-01-15` |
| `year` | INT | Calendar Year | `2026` |
| `quarter` | INT | Calendar Quarter ($1 - 4$) | `1` |
| `month` | INT | Month Number ($1 - 12$) | `1` |
| `month_name` | VARCHAR(20) | Full Month Name | `January` |
| `week` | INT | ISO Week Number ($1 - 52$) | `3` |
| `day` | INT | Day of Month ($1 - 31$) | `15` |
| `day_name` | VARCHAR(20) | Day of Week | `Thursday` |

---

## 5. Table: `fact_inventory`
| Column Name | Data Type | Description | Sample Value |
| :--- | :--- | :--- | :--- |
| `inventory_id` | VARCHAR(20) | Primary Key | `INV0001` |
| `date_id` | DATE | FK to `dim_date` | `2026-01-15` |
| `warehouse_id` | VARCHAR(10) | FK to `dim_warehouse` | `WH001` |
| `product_id` | VARCHAR(10) | FK to `dim_product` | `P001` |
| `opening_inventory` | FLOAT | Starting day inventory balance | `340.0` |
| `received_quantity` | FLOAT | Inbound shipments received | `50.0` |
| `demand_quantity` | FLOAT | Day's outbound fulfillment | `40.0` |
| `closing_inventory` | FLOAT | Ending day inventory balance | `350.0` |

---

## 6. Table: `fact_shipments`
| Column Name | Data Type | Description | Sample Value |
| :--- | :--- | :--- | :--- |
| `shipment_id` | VARCHAR(20) | Primary Key | `SH0001` |
| `supplier_id` | VARCHAR(10) | FK to `dim_supplier` | `S001` |
| `product_id` | VARCHAR(10) | FK to `dim_product` | `P001` |
| `warehouse_id` | VARCHAR(10) | FK to `dim_warehouse` | `WH001` |
| `shipment_date` | DATE | Dispatch date (FK to `dim_date`) | `2026-01-05` |
| `expected_delivery`| DATE | SLA Expected delivery date | `2026-01-10` |
| `actual_delivery` | DATE | Physical arrival date | `2026-01-14` |
| `quantity` | FLOAT | Units shipped | `500.0` |
| `shipping_cost` | FLOAT | Total freight cost (₹) | `2500.00` |
| `calculated_delay_days` | INT | Calculated days late: `actual - expected` | `4` |
