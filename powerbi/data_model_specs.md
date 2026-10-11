# Power BI Data Model & Dashboard Specification

**Project:** Supply Chain Resilience & Shock Intelligence Platform  
**Target Tool:** Microsoft Power BI Desktop / Service  
**Architecture:** Relational Star Schema connected to PostgreSQL / Processed Parquet Views  

---

## 1. Data Model Relationships (Star Schema)

| From Table (Fact / Bridge) | Foreign Key | To Table (Dimension) | Primary Key | Cardinality | Cross-Filtering | Relationship State |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| `fact_inventory` | `date_id` | `dim_date` | `date_id` | Many-to-One ($* : 1$) | Single | **Active** |
| `fact_inventory` | `product_id` | `dim_product` | `product_id` | Many-to-One ($* : 1$) | Single | **Active** |
| `fact_inventory` | `warehouse_id` | `dim_warehouse` | `warehouse_id` | Many-to-One ($* : 1$) | Single | **Active** |
| `fact_demand` | `date_id` | `dim_date` | `date_id` | Many-to-One ($* : 1$) | Single | **Active** |
| `fact_demand` | `product_id` | `dim_product` | `product_id` | Many-to-One ($* : 1$) | Single | **Active** |
| `fact_demand` | `warehouse_id` | `dim_warehouse` | `warehouse_id` | Many-to-One ($* : 1$) | Single | **Active** |
| `fact_orders` | `date_id` | `dim_date` | `date_id` | Many-to-One ($* : 1$) | Single | **Active** |
| `fact_orders` | `product_id` | `dim_product` | `product_id` | Many-to-One ($* : 1$) | Single | **Active** |
| `fact_orders` | `warehouse_id` | `dim_warehouse` | `warehouse_id` | Many-to-One ($* : 1$) | Single | **Active** |
| `fact_shipments` | `shipment_date` | `dim_date` | `date_id` | Many-to-One ($* : 1$) | Single | **Active** |
| `fact_shipments` | `order_date` | `dim_date` | `date_id` | Many-to-One ($* : 1$) | Single | *Inactive (`USERELATIONSHIP`)* |
| `fact_shipments` | `expected_delivery` | `dim_date` | `date_id` | Many-to-One ($* : 1$) | Single | *Inactive (`USERELATIONSHIP`)* |
| `fact_shipments` | `actual_delivery` | `dim_date` | `date_id` | Many-to-One ($* : 1$) | Single | *Inactive (`USERELATIONSHIP`)* |
| `fact_shipments` | `supplier_id` | `dim_supplier` | `supplier_id` | Many-to-One ($* : 1$) | Single | **Active** |
| `fact_shipments` | `product_id` | `dim_product` | `product_id` | Many-to-One ($* : 1$) | Single | **Active** |
| `fact_supplier_product` | `supplier_id` | `dim_supplier` | `supplier_id` | Many-to-One ($* : 1$) | Single | **Active** |
| `fact_supplier_product` | `product_id` | `dim_product` | `product_id` | Many-to-One ($* : 1$) | Single | **Active** |

---

## 2. Core DAX Measures

```dax
// 1. Total Shipped Quantity
Total_Quantity_Shipped = SUM(fact_shipments[quantity])

// 2. Total Shipping Cost
Total_Shipping_Cost = SUM(fact_shipments[shipping_cost])

// 3. Average Shipment Delay (Days)
Avg_Shipment_Delay_Days = 
AVERAGEX(
    fact_shipments,
    DATEDIFF(fact_shipments[expected_delivery], fact_shipments[actual_delivery], DAY)
)

// 4. On-Time Delivery Rate (%)
On_Time_Delivery_Rate = 
DIVIDE(
    CALCULATE(COUNTROWS(fact_shipments), fact_shipments[actual_delivery] <= fact_shipments[expected_delivery]),
    COUNTROWS(fact_shipments),
    0
)

// 5. Total Demand Quantity
Total_Demand_Quantity = SUM(fact_demand[demand_quantity])

// 6. Total Revenue (Demand * Price)
Total_Demand_Revenue = 
SUMX(
    fact_demand,
    fact_demand[demand_quantity] * fact_demand[price]
)

// 7. Latest Closing Inventory Position
Current_Closing_Inventory = 
VAR LatestDate = MAX(dim_date[date_id])
RETURN
CALCULATE(
    SUM(fact_inventory[closing_inventory]),
    dim_date[date_id] = LatestDate
)

// 8. Days of Inventory (DOI)
Days_of_Inventory = 
VAR AvgDailyDemand = AVERAGEX(VALUES(dim_date[date_id]), [Total_Demand_Quantity])
RETURN
DIVIDE([Current_Closing_Inventory], AvgDailyDemand, 0)

// 9. Simulated Revenue at Risk (14-Day Delay)
Simulated_Revenue_at_Risk = 
SUMX(
    dim_product,
    VAR ProductAvgDemand = AVERAGEX(VALUES(dim_date[date_id]), [Total_Demand_Quantity])
    VAR ProductPrice = AVERAGE(fact_demand[price])
    VAR DaysToStockout = DIVIDE([Current_Closing_Inventory], ProductAvgDemand, 0)
    VAR DelayDays = 14
    VAR DaysOutOfStock = MAX(0, DelayDays - DaysToStockout)
    RETURN
    DaysOutOfStock * ProductAvgDemand * ProductPrice
)
```

---

## 3. Power BI 5-Page Dashboard Layout Specs

### Page 1: Executive Control Tower
- **Header KPIs**: Total Revenue, Total SKUs, Network Inventory Value, High-Risk Supplier Count.
- **Visuals**:
  - Global Fulfillment Map / Warehouse Inventory Distribution.
  - Monthly Demand vs Shipped Volume Trendline.
  - Top 5 Revenue-at-Risk Exposure Callout Table.

### Page 2: Supplier Risk & Performance
- **Visuals**:
  - 5-Dimension Radar Chart per Supplier (Delay, Reliability, Capacity, Quality, Dependency).
  - Delay Days vs On-Time Delivery Rate Scatter Plot.
  - Supplier Risk Band Slicer (CRITICAL, HIGH, MEDIUM, LOW).
  - Supplier Scorecard Matrix.

### Page 3: Inventory Intelligence & Health
- **Visuals**:
  - Days of Inventory (DOI) Horizontal Bar Chart with 7-day Alert Line.
  - Inventory Turns by Product Category.
  - Closing Inventory vs Reorder Point (ROP) Dual-Axis Chart.
  - Safety Stock Coverage Table.

### Page 4: Disruption Shock Impact Simulator
- **Visuals**:
  - What-If Parameter Slicers (Delay Days, Demand Surge %, Capacity Cut %).
  - Simulated Lost Units by SKU (Bar Chart).
  - Simulated Lost Revenue Waterfall Chart.
  - Monte Carlo P5 / P50 / P95 Risk Probability Density Area Chart.

### Page 5: Strategic Mitigation Decision Matrix
- **Visuals**:
  - Mitigation Strategy Comparison (Do Nothing, Expedite, Alternate Supplier, Transfer).
  - Net Benefit ROI Bar Chart ($Net\ Benefit = Revenue\ Saved - Cost$).
  - Cost Breakdown Donut Chart.
  - Recommended Action Strategy Card.
