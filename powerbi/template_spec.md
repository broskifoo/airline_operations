# Power BI Template Specification
## Airline Operations & Revenue Intelligence Platform

---
> **Format**: Human-readable specification for building .pbix file
> **Target**: Power BI Desktop (latest)
> **Data Source**: `data/processed/*.parquet`

---

## Template Metadata

```json
{
  "name": "Airline Operations & Revenue Intelligence",
  "version": "1.0",
  "author": "Airline Analytics Team",
  "description": "Star-schema operational & modeled revenue analytics for 2024 US domestic flights",
  "dataSource": "Parquet files in data/processed/",
  "refreshType": "Scheduled (daily)",
  "parameters": ["CASM_WhatIf"]
}
```

---

## Page Specifications

### Page 1: Executive Dashboard
**Layout**: 16:9 (1280×720)
**Background**: White (#FFFFFF)

| Visual | Type | Position | Size | Measures | Filters/Slicers |
|--------|------|----------|------|----------|-----------------|
| KPI Card | Card | (20, 20) | 280×120 | OTP %, Target: 80% | - |
| KPI Card | Card | (320, 20) | 280×120 | Total Flights | - |
| KPI Card | Card | (620, 20) | 280×120 | Cancellation Rate | - |
| KPI Card | Card | (920, 20) | 280×120 | Est. Profit Margin, Target: 10% | - |
| Line Chart | Line | (20, 160) | 620×350 | OTP % by Month | Year slicer |
| Bar Chart | Clustered Bar | (660, 160) | 600×350 | OTP % by Carrier | Carrier slicer |
| Bar Chart | Clustered Bar | (20, 530) | 620×150 | Est. Revenue by Carrier | Carrier slicer |
| Donut Chart | Donut | (660, 530) | 600×150 | Delay Category Distribution | - |

**Slicers (Top-right)**:
- Year (Dropdown): 2024
- Carrier (Multi-select): All
- Date Range: Jan 2024 - Dec 2024

---

### Page 2: Operations Deep Dive
**Layout**: 16:9

| Visual | Type | Position | Size | Measures | Filters/Slicers |
|--------|------|----------|------|----------|-----------------|
| Stacked Bar | Stacked Bar | (20, 20) | 620×350 | Delay Categories by Carrier | Carrier, Year |
| Stacked Bar | Stacked Bar | (660, 20) | 600×350 | Primary Delay Causes by Carrier | Carrier, Year |
| Heatmap | Matrix | (20, 390) | 620×300 | OTP % by Day of Week × Hour | Carrier, Month |
| Area Chart | Area | (660, 390) | 600×300 | Flights & OTP by Departure Period | Carrier |
| Line Chart | Line | (20, 710) | 620×150 | Rolling 7-day OTP | Carrier, Year |
| Scatter Plot | Scatter | (660, 710) | 600×150 | Avg Delay vs Flights by Route | Top 50 routes |

**Slicers (Left panel)**:
- Carrier (Multi-select)
- Month (Multi-select)
- Delay Category (Multi-select)

---

### Page 3: Carrier Scorecard
**Layout**: 16:9

| Visual | Type | Position | Size | Measures | Filters/Slicers |
|--------|------|----------|------|----------|-----------------|
| Table | Table | (20, 20) | 1240×500 | Carrier Scorecard (see columns below) | Year |
| Line Chart | Line | (20, 540) | 620×180 | Carrier OTP % Trend | Carrier, Year |
| Bar Chart | Clustered Bar | (660, 540) | 600×180 | Carrier vs Industry OTP Gap | Carrier, Year |

**Carrier Scorecard Columns**:
| Column | Measure | Format | Conditional Formatting |
|--------|---------|--------|----------------------|
| Carrier | carrier_code | Text | - |
| Airline | airline_name | Text | - |
| Flights | Total Flights | #,##0 | - |
| Market Share | Carrier Market Share | 0.0% | - |
| OTP % | Carrier OTP % | 0.0% | Green→Red (85%/75%/65%) |
| Avg Delay (min) | Carrier Avg Delay | 0.0 | Red→Green (45/15) |
| Cancellation Rate | Carrier Cancellation Rate | 0.0% | Red→Green (5%/1%) |
| Avg Taxi Out | Avg Taxi Out | 0.0 | - |
| OTP Rank | Carrier OTP Rank | # | - |

---

### Page 4: Airport Efficiency
**Layout**: 16:9

| Visual | Type | Position | Size | Measures | Filters/Slicers |
|--------|------|----------|------|----------|-----------------|
| Map | Azure Map / Filled Map | (20, 20) | 620×500 | Airport Efficiency Score (color) | State, Carrier |
| Table | Table | (660, 20) | 600×500 | Airport Efficiency Rankings (see columns) | State, Carrier |

**Map Configuration**:
- Location: airport_code
- Latitude: latitude
- Longitude: longitude
- Size: Total Flights
- Color: Efficiency Score (Green→Red)
- Tooltip: Airport Name, City, State, Efficiency Score, OTP %, Flights

**Rankings Table Columns**:
| Column | Measure | Format |
|--------|---------|--------|
| Airport | airport_code | Text |
| Name | airport_name | Text |
| City, State | city + ", " + state | Text |
| Flights | Airport Total Flights | #,##0 |
| Efficiency Score | Efficiency Score | 0.0 |
| Rank | Efficiency Rank | # |
| OTP % | Airport OTP % | 0.0% |
| Cancel % | 1 - Cancel Pct | 0.0% |

---

### Page 5: Route Profitability (Modeled)
**Layout**: 16:9
**Subtitle**: "All revenue metrics are ESTIMATED/MODELED"

| Visual | Type | Position | Size | Measures | Filters/Slicers |
|--------|------|----------|------|----------|-----------------|
| Scatter Plot | Scatter | (20, 20) | 620×500 | Route Profitability Matrix | Year, Carrier, Distance Category |
| Table | Table | (660, 20) | 600×500 | Route Profitability Details | Year, Carrier, Profitability Class |

**Scatter Plot Configuration**:
- X Axis: Estimated Revenue (log scale)
- Y Axis: Estimated Profit
- Size: Estimated Passengers
- Color: Profitability Class (4 colors)
- X Axis: Logarithmic
- Trend Line: Linear
- Quadrant Lines: Median Revenue (vertical), Median Profit (horizontal)
- Tooltip: Route, Carrier, Revenue, Profit, Margin, Passengers

**Route Details Table Columns**:
| Column | Measure | Format |
|--------|---------|--------|
| Route | route_code | Text |
| Carrier | carrier_code | Text |
| Distance | distance_miles | #,##0 mi |
| Category | distance_category | Text |
| Est. Passengers | estimated_passengers | #,##0 |
| Est. Revenue | estimated_ticket_revenue | $#,##0 |
| Est. Cost | estimated_operating_cost | $#,##0 |
| Est. Profit | estimated_profit | $#,##0 |
| Profit Margin | profit_margin | 0.0% |
| Rev/Passenger | revenue_per_passenger | $#,##0 |
| Class | profitability_class | Text |

---

### Page 6: Seasonal & Temporal
**Layout**: 16:9

| Visual | Type | Position | Size | Measures | Filters/Slicers |
|--------|------|----------|------|----------|-----------------|
| Column Chart | Clustered Column | (20, 20) | 400×300 | Flights by Season | Year |
| Column Chart | Clustered Column | (440, 20) | 400×300 | OTP % by Season | Year |
| Column Chart | Clustered Column | (860, 20) | 400×300 | Flights by Day of Week | Year |
| Column Chart | Clustered Column | (20, 340) | 400×300 | OTP % by Day of Week | Year |
| Column Chart | Clustered Column | (440, 340) | 400×300 | Flights by Departure Period | Year |
| Column Chart | Clustered Column | (860, 340) | 400×300 | OTP % by Departure Period | Year |
| Heatmap | Matrix | (20, 660) | 1240×200 | OTP % by Month × Carrier | Year |

---

### Page 7: What-If Analysis (CASM Sensitivity)
**Layout**: 16:9

| Visual | Type | Position | Size | Measures | Filters/Slicers |
|--------|------|----------|------|----------|-----------------|
| What-If Slicer | Numeric Range | (20, 20) | 300×80 | CASM_WhatIf | - |
| Line Chart | Line | (20, 120) | 620×300 | Profit Margin vs CASM | Carrier, Route |
| Table | Table | (660, 20) | 600×300 | Scenario Comparison | - |

**Scenario Comparison Table**:
| Scenario | CASM | Est. Revenue | Est. Cost | Est. Profit | Profit Margin |
|----------|------|--------------|-----------|-------------|---------------|
| Low | 0.08 | [Est. Revenue] | [Cost @ 0.08] | [Profit @ 0.08] | [Margin @ 0.08] |
| Base | 0.12 | [Est. Revenue] | [Cost @ 0.12] | [Profit @ 0.12] | [Margin @ 0.12] |
| High | 0.15 | [Est. Revenue] | [Cost @ 0.15] | [Profit @ 0.15] | [Margin @ 0.15] |

**Measures for Scenarios**:
```dax
Est. Cost @ 0.08 = CALCULATE([Est. Operating Cost (What-If)], CASM_WhatIf[CASM_WhatIf Value] = 0.08)
Est. Profit @ 0.08 = [Est. Total Revenue] - [Est. Cost @ 0.08]
Margin @ 0.08 = DIVIDE([Est. Profit @ 0.08], [Est. Total Revenue], BLANK())
```

---

### Page 8: Data Quality & Monitoring
**Layout**: 16:9

| Visual | Type | Position | Size | Measures | Filters/Slicers |
|--------|------|----------|------|----------|-----------------|
| Card | Card | (20, 20) | 280×120 | Data Freshness (Days) | - |
| Card | Card | (320, 20) | 280×120 | Missing Delay Data % | - |
| Card | Card | (620, 20) | 280×120 | Unmapped Routes % | - |
| Card | Card | (920, 20) | 280×120 | Total Fact Flights Rows | - |
| Table | Table | (20, 160) | 1240×200 | Validation Summary | - |
| Line Chart | Line | (20, 380) | 620×180 | Daily Flight Volume | Year |
| Line Chart | Line | (660, 380) | 600×180 | Daily OTP % | Year |

---

## Color Palette

| Name | Hex | Usage |
|------|-----|-------|
| Primary Blue | #1565C0 | Primary brand, headers |
| Success Green | #2E7D32 | Good OTP, High Profit |
| Warning Amber | #F9A825 | Moderate OTP, High Rev/Low Profit |
| Warning Orange | #EF6C00 | Low OTP, High Rev/Low Profit |
| Danger Red | #C62828 | Poor OTP, Low Rev/Low Profit |
| Neutral Gray | #757575 | Borders, gridlines |
| Light Gray | #F5F5F5 | Background cards |
| White | #FFFFFF | Page background |
| Dark Blue | #0D47A1 | Primary text |
| Medium Blue | #1E88E5 | Links, accents |

---

## Conditional Formatting Rules

### OTP % (All Visuals)
| Range | Color | Label |
|-------|-------|-------|
| ≥ 85% | #2E7D32 | Excellent |
| 75-85% | #F9A825 | Good |
| 65-75% | #EF6C00 | Fair |
| < 65% | #C62828 | Poor |

### Delay (min)
| Range | Color |
|-------|-------|
| ≤ 15 | #2E7D32 |
| 15-45 | #F9A825 |
| 45-90 | #EF6C00 |
| > 90 | #C62828 |

### Profitability Class
| Class | Color |
|-------|-------|
| High Rev / High Profit | #2E7D32 |
| Low Rev / High Profit | #1565C0 |
| High Rev / Low Profit | #EF6C00 |
| Low Rev / Low Profit | #C62828 |

---

## Formatting Standards

### Numbers
| Type | Format String | Example |
|------|---------------|---------|
| Large Counts | #,##0 | 7,079,081 |
| Percentages | 0.0% | 78.5% |
| Currency | $#,##0 | $1,234,567 |
| Currency (Compact) | $#,##0,, "M" | $1.2M |
| Minutes | 0.0 | 12.5 |
| Distance | #,##0 " mi" | 1,250 mi |
| Ratios | 0.00 | 1.25 |

### Text
- **Font Family**: Segoe UI (default)
- **Header Font Size**: 14pt, Bold
- **Body Font Size**: 11pt, Regular
- **KPI Value Font Size**: 28pt, Bold
- **KPI Label Font Size**: 11pt, Regular

---

## Tooltips

### Flight Tooltip (for drill-through)
**Page**: Tooltip_Flight
**Fields**: flight_id, carrier_name, origin, dest, arr_delay_min, delay_category, cancellation_category

### Route Tooltip
**Page**: Tooltip_Route
**Fields**: route_code, carrier_name, distance_miles, estimated_revenue, estimated_profit, profit_margin, profitability_class

### Airport Tooltip
**Page**: Tooltip_Airport
**Fields**: airport_code, airport_name, city, state, efficiency_score, efficiency_rank, otp_pct, total_flights

---

## Drill-Through Pages

### Carrier Detail
**Target**: Carrier Detail
**Drill-through Field**: carrier_code (dim_airline)
**Visuals**: Carrier trend, top routes, delay causes, cancellation breakdown

### Airport Detail
**Target**: Airport Detail
**Drill-through Field**: airport_code (dim_airport)
**Visuals**: Map, efficiency trend, top routes, carrier breakdown

### Route Detail
**Target**: Route Detail
**Drill-through Field**: route_code (dim_route)
**Visuals**: Revenue/profit trend, carrier comparison, seasonal pattern

---

## Bookmarks

| Bookmark | Name | Views |
|----------|------|-------|
| 1 | Overview | Page 1 (all slicers cleared) |
| 2 | Carrier View | Page 3 (Carrier selected) |
| 3 | Airport View | Page 4 (Airport selected) |
| 4 | Route View | Page 5 (Route selected) |
| 5 | What-If Base | Page 7 (CASM = 0.12) |
| 6 | What-If High | Page 7 (CASM = 0.15) |
| 7 | What-If Low | Page 7 (CASM = 0.08) |

---

## Accessibility

- **Alt Text**: All visuals have descriptive alt text
- **Color Contrast**: All text meets WCAG AA (4.5:1)
- **Keyboard Navigation**: Tab order logical
- **Screen Reader**: Data labels on all charts
- **High Contrast Mode**: Tested and verified

---

## Performance Optimizations

1. **Aggregations**: Create aggregation table for fact_flights at carrier-route-month level
2. **Fact_Flights**: Use DirectQuery mode (7M rows)
3. **Fact_Revenue**: Import mode (29K rows)
4. **Incremental Refresh**: Configure on fact_flights (date_id)
4. **Query Reduction**: Disable auto-date/time, use explicit date table

---

## Security

### Row-Level Security (RLS) Example
```dax
-- Carrier RLS
CarrierRLS = 
VAR UserEmail = USERPRINCIPALNAME()
VAR UserCarrier = LOOKUPVALUE(
    CarrierAccess[carrier_code],
    CarrierAccess[email], UserEmail
)
RETURN
dim_airline[carrier_code] = UserCarrier
```

---

## Migration Checklist

- [ ] Load all 6 Parquet files
- [ ] Verify 8 relationships (1:*, Single direction)
- [ ] Mark dim_date as Date Table
- [ ] Hide all surrogate keys
- [ ] Create 50+ measures (see dax_measures.md)
- [ ] Create CASM What-If parameter
- [ ] Build 8 pages with specified visuals
- [ ] Apply conditional formatting rules
- [ ] Configure 3 drill-through pages
- [ ] Set up 7 bookmarks
- [ ] Configure incremental refresh (fact_flights)
- [ ] Test all 33 validation scenarios
- [ ] Verify all "Estimated/Modeled" labels
- [ ] Test RLS with test users
- [ ] Publish to Power BI Service
- [ ] Schedule daily refresh

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-08-29 | Initial template with 8 pages, 50+ measures, CASM What-If |