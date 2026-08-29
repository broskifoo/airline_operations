# Power BI Quick Start Guide
## Airline Operations & Revenue Intelligence Platform

---

## Prerequisites

- Power BI Desktop (latest)
- Data files in `data/processed/` (Parquet format)
- DAX measures from `powerbi/dax_measures.md`

---

## Step 1: Load Data

### Option A: Direct Parquet Import (Recommended)
1. Open Power BI Desktop
2. **Get Data** → **Parquet**
3. Navigate to `data/processed/`
4. Select all `.parquet` files:
   - `dim_date.parquet`
   - `dim_airline.parquet`
   - `dim_airport.parquet`
   - `dim_route.parquet`
   - `fact_flights.parquet` (partitioned folder)
   - `fact_revenue.parquet`
5. Click **Load**

### Option B: Folder Connector (for partitioned fact_flights)
1. **Get Data** → **Folder**
2. Path: `data/processed/fact_flights.parquet/`
3. Combine files → Parquet
4. This automatically reads all partitions

---

## Step 2: Configure Relationships

### Model View
1. Go to **Model** view (left sidebar)
2. Verify relationships exist:

| From | To | Cardinality | Direction |
|------|----|-------------|-----------|
| dim_date[date_id] | fact_flights[date_id] | 1:* | Single |
| dim_airline[airline_id] | fact_flights[airline_id] | 1:* | Single |
| dim_airport[airport_id] | fact_flights[origin_airport_id] | 1:* | Single |
| dim_airport[airport_id] | fact_flights[dest_airport_id] | 1:* | Single |
| dim_route[route_id] | fact_flights[route_id] | 1:* | Single |
| dim_date[date_id] | fact_revenue[date_id] | 1:* | Single |
| dim_airline[airline_id] | fact_revenue[airline_id] | 1:* | Single |
| dim_route[route_id] | fact_revenue[route_id] | 1:* | Single |

### Fix Missing Relationships
If any missing:
1. Drag from dimension PK to fact FK
2. Set **Cardinality**: One-to-Many (1:*)
3. Set **Cross filter direction**: Single (Dimension → Fact)
4. ✅ **Make this relationship active**

---

## Step 3: Mark Date Table

1. Select **dim_date** in Fields pane
2. **Table tools** → **Mark as Date Table**
2. Date column: **date**
3. Click **OK**

This enables time intelligence (YTD, YoY, etc.)

---

## Step 4: Hide Surrogate Keys

Right-click each column → **Hide in report view**:

| Table | Columns to Hide |
|-------|-----------------|
| dim_date | date_id |
| dim_airline | airline_id |
| dim_airport | airport_id, latitude, longitude |
| dim_route | route_id, origin_airport_id, dest_airport_id |
| fact_flights | flight_id, date_id, airline_id, origin_airport_id, dest_airport_id, route_id |
| fact_revenue | revenue_id, date_id, airline_id, route_id |

---

## Step 5: Create Measures

### Quick Setup
1. **Modeling** → **New Measure**
2. Copy from `powerbi/dax_measures.md`
3. Organize into Display Folders:

```
Flight Operations
  ├── On-Time Performance
  ├── Delays
  ├── Taxi & Block Times
  └── Cancellations & Diversions

Carrier Analytics
  ├── Performance
  └── Rankings

Airport Analytics
  ├── Operations
  └── Efficiency

Route Analytics
  ├── Operations
  └── Categories

Revenue Analytics (Modeled)
  ├── Summary
  ├── By Carrier
  ├── By Route
  └── Profitability Matrix

Time & Seasonal
  ├── Day of Week
  ├── Season
  └── Departure Period

Benchmarks & KPIs
What-If Analysis
Data Quality
```

### Essential First Measures (create these first)
```dax
-- Base
Total Flights = COUNTROWS(fact_flights)

-- OTP
On-Time Flights = CALCULATE([Total Flights], fact_flights[is_delayed]=0, fact_flights[cancelled_flag]=0)
OTP % = DIVIDE([On-Time Flights], CALCULATE([Total Flights], fact_flights[cancelled_flag]=0), 0)

-- Revenue (Modeled)
Estimated Total Revenue = CALCULATE(SUM(fact_revenue[estimated_ticket_revenue]), fact_revenue[estimated_ticket_revenue]>0)
Estimated Profit Margin = DIVIDE([Estimated Total Revenue] - CALCULATE(SUM(fact_revenue[estimated_operating_cost])), [Estimated Total Revenue], BLANK())
```

---

## Step 6: What-If Parameter

1. **Modeling** → **New Parameter** → **Numeric Range**
2. Name: `CASM_WhatIf`
3. Data Type: Decimal Number
4. Minimum: 0.08
5. Maximum: 0.15
6. Default: 0.12
7. Increment: 0.01
8. Add slicer to report

---

## Step 7: Key Visuals to Build

### Page 1: Executive Dashboard
- **KPIs**: OTP %, Total Flights, Cancellation Rate, Est. Profit Margin
- **Trend**: OTP % by Month (line chart)
- **Carrier Ranking**: OTP % by Carrier (bar chart)
- **Revenue**: Estimated Revenue by Carrier (bar chart)

### Page 2: Operations Deep Dive
- **Delay Analysis**: Delay category distribution (donut)
- **Delay Causes**: Primary delay cause by carrier (stacked bar)
- **Time of Day**: Flights & OTP by Departure Period
- **Day of Week**: Heatmap of OTP by Day/Hour

### Page 3: Carrier Analysis
- **Carrier Scorecard**: Table with OTP, Delay, Cancellations, Market Share
- **Benchmark**: Carrier vs Industry OTP Gap
- **Trend**: Carrier OTP % over time

### Page 4: Airport Efficiency
- **Map**: Airport locations colored by Efficiency Score
- **Table**: Top/Bottom 10 airports by Efficiency Score
- **Drill-through**: Airport detail page

### Page 5: Route Profitability (Modeled)
- **2×2 Matrix**: Scatter plot Revenue vs Profit, colored by profitability_class
- **Route Table**: Revenue, Profit, Margin by Route
- **Carrier-Route**: Revenue by Carrier-Route

### Page 6: Seasonal & Temporal
- **Seasonal**: OTP by Season
- **Day of Week**: OTP by Day of Week
- **Departure Period**: Flights & OTP by Time of Day

### Page 7: What-If Analysis
- **CASM Slider**: What-If parameter
- **Sensitivity**: Profit Margin at different CASM levels
- **Scenario Comparison**: Table with Base/High/Low CASM

---

## Step 8: Conditional Formatting

### OTP % (Green-Yellow-Red)
1. Select measure in visual
2. **Format** → **Data colors** → **fx** (conditional)
3. Format by: **Rules**
   - ≥ 0.85 → Green (#2E7D32)
   - ≥ 0.75 → Amber (#F9A825)
   - ≥ 0.65 → Orange (#EF6C00)
   - Else → Red (#C62828)

### Profitability Matrix Colors
- High Rev/High Profit → Green (#2E7D32)
- Low Rev/High Profit → Blue (#1565C0)
- High Rev/Low Profit → Orange (#EF6C00)
- Low Rev/Low Profit → Red (#C62828)

---

## Step 9: Publishing & Sharing

### Publish to Service
1. **File** → **Publish** → **My Workspace**
2. Schedule refresh (if using gateway for local files)
3. Configure parameters if needed

### Row-Level Security (Optional)
```dax
-- Example: Restrict by Carrier
CarrierRLS = 
CONTAINSSTRING(
    USERPRINCIPALNAME(),
    dim_airline[carrier_code]
)
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Time intelligence not working | Mark dim_date as Date Table; ensure date column is Date type |
| Relationships not filtering | Check cross-filter direction = Single (Dim → Fact) |
| Measures returning BLANK | Use DIVIDE() instead of /; check filter context |
| Large fact_flights slow | Enable aggregations; use DirectQuery for fact_flights |
| Revenue shows as actual | Add "(Modeled)" to all revenue visual titles |
| Date hierarchy missing | Right-click date column → New Hierarchy → Year/Quarter/Month/Day |

---

## File Locations

| File | Path |
|------|------|
| DAX Measures | `powerbi/dax_measures.md` |
| Model Diagram | `powerbi/model_diagram.md` |
| Data Files | `data/processed/*.parquet` |
| Validation Report | `reports/validation_report.md` |
| Data Quality Report | `reports/data_quality_report.md` |

---

## Support

- **Data Issues**: Check `reports/validation_report.md` - all 33 checks pass
- **Methodology**: See `docs/assumptions.md` for all estimation assumptions
- **Model Design**: See `docs/data_model.md` for star schema details