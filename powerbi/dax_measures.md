# Power BI DAX Measures
## Airline Operations & Revenue Intelligence Platform

---
> **Usage**: Copy these measures into Power BI Desktop > Modeling > New Measure
> All measures follow best practices: DIVIDE for safe division, CALCULATE for context modification, explicit FILTER for performance

---

## 1. Base Measures (Flight Operations)

### Flight Count
```dax
Total Flights = 
COUNTROWS(fact_flights)
```

### On-Time Performance
```dax
On-Time Flights = 
CALCULATE(
    [Total Flights],
    fact_flights[is_delayed] = 0,
    fact_flights[cancelled_flag] = 0
)

OTP % = 
DIVIDE(
    [On-Time Flights],
    CALCULATE([Total Flights], fact_flights[cancelled_flag] = 0),
    0
)
```

### Delay Metrics
```dax
Avg Arrival Delay (min) = 
AVERAGEX(
    FILTER(fact_flights, fact_flights[cancelled_flag] = 0),
    fact_flights[arr_delay_min]
)

Avg Departure Delay (min) = 
AVERAGEX(
    FILTER(fact_flights, fact_flights[cancelled_flag] = 0),
    fact_flights[dep_delay_min]
)

Pct Delayed = 
DIVIDE(
    CALCULATE([Total Flights], fact_flights[is_delayed] = 1),
    CALCULATE([Total Flights], fact_flights[cancelled_flag] = 0),
    0
)

Pct Cancelled = 
DIVIDE(
    CALCULATE([Total Flights], fact_flights[cancelled_flag] = 1),
    [Total Flights],
    0
)
```

### Delay Categories
```dax
Pct Severe Delays (90+) = 
DIVIDE(
    CALCULATE([Total Flights], fact_flights[delay_category] = "Severe (90+)"),
    CALCULATE([Total Flights], fact_flights[cancelled_flag] = 0),
    0
)

Pct Moderate Delays (45-90) = 
DIVIDE(
    CALCULATE([Total Flights], fact_flights[delay_category] = "Moderate (45-90)"),
    CALCULATE([Total Flights], fact_flights[cancelled_flag] = 0),
    0
)

Pct Minor Delays (15-45) = 
DIVIDE(
    CALCULATE([Total Flights], fact_flights[delay_category] = "Minor (15-45)"),
    CALCULATE([Total Flights], fact_flights[cancelled_flag] = 0),
    0
)
```

### Delay Causes
```dax
Avg Carrier Delay (min) = 
AVERAGEX(
    FILTER(fact_flights, fact_flights[cancelled_flag] = 0),
    fact_flights[carrier_delay_min]
)

Avg Weather Delay (min) = 
AVERAGEX(
    FILTER(fact_flights, fact_flights[cancelled_flag] = 0),
    fact_flights[weather_delay_min]
)

Avg NAS Delay (min) = 
AVERAGEX(
    FILTER(fact_flights, fact_flights[cancelled_flag] = 0),
    fact_flights[nas_delay_min]
)

Avg Late Aircraft Delay (min) = 
AVERAGEX(
    FILTER(fact_flights, fact_flights[cancelled_flag] = 0),
    fact_flights[late_aircraft_delay_min]
)

Primary Delay Cause Distribution = 
VAR CauseCounts = 
    ADDCOLUMNS(
        VALUES(fact_flights[primary_delay_cause]),
        "Count", CALCULATE(COUNTROWS(fact_flights), fact_flights[is_delayed] = 1)
    )
RETURN
    CauseCounts
```

### Operational Efficiency
```dax
Avg Taxi Out (min) = 
AVERAGEX(
    FILTER(fact_flights, fact_flights[cancelled_flag] = 0),
    fact_flights[taxi_out_min]
)

Avg Taxi In (min) = 
AVERAGEX(
    FILTER(fact_flights, fact_flights[cancelled_flag] = 0),
    fact_flights[taxi_in_min]
)

Avg Air Time (min) = 
AVERAGEX(
    FILTER(fact_flights, fact_flights[cancelled_flag] = 0),
    fact_flights[air_time_min]
)

Avg Block Time (min) = 
AVERAGEX(
    FILTER(fact_flights, fact_flights[cancelled_flag] = 0),
    fact_flights[actual_elapsed_min]
)
```

---

## 2. Time Intelligence Measures

### Time Calculations
```dax
Flights YTD = 
CALCULATE(
    [Total Flights],
    DATESYTD(dim_date[date])
)

Flights MTD = 
CALCULATE(
    [Total Flights],
    DATESMTD(dim_date[date])
)

Flights QTD = 
CALCULATE(
    [Total Flights],
    DATESQTD(dim_date[date])
)
```

### Year-over-Year
```dax
Flights YoY % = 
VAR CurrentPeriod = [Total Flights]
VAR PriorPeriod = 
    CALCULATE(
        [Total Flights],
        SAMEPERIODLASTYEAR(dim_date[date])
    )
RETURN
    DIVIDE(CurrentPeriod - PriorPeriod, PriorPeriod, BLANK())

OTP YoY Change (pp) = 
[OTP %] - 
CALCULATE(
    [OTP %],
    SAMEPERIODLASTYEAR(dim_date[date])
)
```

### Rolling Averages
```dax
OTP 7-Day Rolling Avg = 
AVERAGEX(
    DATESINPERIOD(dim_date[date], LASTDATE(dim_date[date]), -7, DAY),
    [OTP %]
)

OTP 30-Day Rolling Avg = 
AVERAGEX(
    DATESINPERIOD(dim_date[date], LASTDATE(dim_date[date]), -30, DAY),
    [OTP %]
)
```

---

## 3. Carrier-Level Measures

### Carrier Performance
```dax
Carrier Flights = 
CALCULATE(
    [Total Flights],
    ALLEXCEPT(fact_flights, dim_airline[carrier_code])
)

Carrier OTP % = 
DIVIDE(
    CALCULATE(
        [On-Time Flights],
        ALLEXCEPT(fact_flights, dim_airline[carrier_code])
    ),
    CALCULATE(
        [Total Flights],
        ALLEXCEPT(fact_flights, dim_airline[carrier_code]),
        fact_flights[cancelled_flag] = 0
    ),
    0
)

Carrier Avg Delay = 
CALCULATE(
    [Avg Arrival Delay (min)],
    ALLEXCEPT(fact_flights, dim_airline[carrier_code])
)

Carrier Cancellation Rate = 
CALCULATE(
    [Pct Cancelled],
    ALLEXCEPT(fact_flights, dim_airline[carrier_code])
)

Carrier Market Share = 
DIVIDE(
    [Carrier Flights],
    CALCULATE([Total Flights], ALL(dim_airline)),
    0
)
```

### Carrier Ranking
```dax
Carrier OTP Rank = 
RANKX(
    ALL(dim_airline[carrier_code]),
    [Carrier OTP %],
    ,
    DESC,
    DENSE
)

Carrier Delay Rank = 
RANKX(
    ALL(dim_airline[carrier_code]),
    [Carrier Avg Delay],
    ,
    ASC,
    DENSE
)
```

---

## 4. Airport-Level Measures

### Airport Operations
```dax
Origin Airport Flights = 
CALCULATE(
    [Total Flights],
    ALLEXCEPT(fact_flights, dim_airport[airport_code])
)

Dest Airport Flights = 
CALCULATE(
    [Total Flights],
    ALLEXCEPT(fact_flights, dim_airport[airport_code])
)

Airport Total Flights = 
[Origin Airport Flights] + [Dest Airport Flights]

Origin OTP % = 
DIVIDE(
    CALCULATE(
        [On-Time Flights],
        ALLEXCEPT(fact_flights, dim_airport[airport_code])
    ),
    CALCULATE(
        [Total Flights],
        ALLEXCEPT(fact_flights, dim_airport[airport_code]),
        fact_flights[cancelled_flag] = 0
    ),
    0
)
```

### Airport Efficiency Score (Pre-calculated)
```dax
Airport Efficiency Score = 
CALCULATE(
    AVERAGE(dim_airport[efficiency_score]),
    ALLEXCEPT(dim_airport, dim_airport[airport_code])
)

Airport Efficiency Rank = 
CALCULATE(
    MIN(dim_airport[efficiency_rank]),
    ALLEXCEPT(dim_airport, dim_airport[airport_code])
)

Airport OTP % (Dim) = 
CALCULATE(
    AVERAGE(dim_airport[otp_pct]),
    ALLEXCEPT(dim_airport, dim_airport[airport_code])
)
```

---

## 5. Route-Level Measures

### Route Operations
```dax
Route Flights = 
CALCULATE(
    [Total Flights],
    ALLEXCEPT(fact_flights, dim_route[route_code])
)

Route Distance = 
CALCULATE(
    AVERAGE(dim_route[distance_miles]),
    ALLEXCEPT(dim_route, dim_route[route_code])
)

Route OTP % = 
DIVIDE(
    CALCULATE(
        [On-Time Flights],
        ALLEXCEPT(fact_flights, dim_route[route_code])
    ),
    CALCULATE(
        [Total Flights],
        ALLEXCEPT(fact_flights, dim_route[route_code]),
        fact_flights[cancelled_flag] = 0
    ),
    0
)

Route Avg Delay = 
CALCULATE(
    [Avg Arrival Delay (min)],
    ALLEXCEPT(fact_flights, dim_route[route_code])
)
```

### Route Categories
```dax
Short Haul Flights = 
CALCULATE(
    [Total Flights],
    dim_route[distance_category] = "Short Haul"
)

Medium Haul Flights = 
CALCULATE(
    [Total Flights],
    dim_route[distance_category] = "Medium Haul"
)

Long Haul Flights = 
CALCULATE(
    [Total Flights],
    dim_route[distance_category] = "Long Haul"
)

Ultra Long Haul Flights = 
CALCULATE(
    [Total Flights],
    dim_route[distance_category] = "Ultra Long Haul"
)
```

---

## 6. Revenue Measures (Modeled/Estimated)

> ⚠️ **Important**: All revenue measures are **ESTIMATED/MODELED** - must display as such in reports

```dax
Estimated Total Revenue = 
CALCULATE(
    SUM(fact_revenue[estimated_ticket_revenue]),
    fact_revenue[estimated_ticket_revenue] > 0
)

Estimated Total Passengers = 
CALCULATE(
    SUM(fact_revenue[estimated_passengers]),
    fact_revenue[estimated_passengers] > 0
)

Estimated Total Operating Cost = 
CALCULATE(
    SUM(fact_revenue[estimated_operating_cost]),
    fact_revenue[estimated_operating_cost] > 0
)

Estimated Total Profit = 
[Estimated Total Revenue] - [Estimated Total Operating Cost]

Estimated Profit Margin = 
DIVIDE(
    [Estimated Total Profit],
    [Estimated Total Revenue],
    BLANK()
)

Estimated Load Factor = 
CALCULATE(
    AVERAGE(fact_revenue[estimated_load_factor]),
    fact_revenue[estimated_load_factor] > 0
)

Revenue Per Passenger = 
DIVIDE(
    [Estimated Total Revenue],
    [Estimated Total Passengers],
    BLANK()
)

Revenue Per Flight = 
DIVIDE(
    [Estimated Total Revenue],
    CALCULATE(
        SUM(fact_revenue[estimated_passengers]) / AVERAGE(fact_revenue[estimated_load_factor]),
        fact_revenue[estimated_load_factor] > 0
    ),
    BLANK()
)
```

### Revenue by Carrier
```dax
Carrier Estimated Revenue = 
CALCULATE(
    [Estimated Total Revenue],
    ALLEXCEPT(fact_revenue, dim_airline[carrier_code])
)

Carrier Estimated Profit = 
CALCULATE(
    [Estimated Total Profit],
    ALLEXCEPT(fact_revenue, dim_airline[carrier_code])
)

Carrier Profit Margin = 
DIVIDE(
    [Carrier Estimated Profit],
    [Carrier Estimated Revenue],
    BLANK()
)
```

### Revenue by Route
```dax
Route Estimated Revenue = 
CALCULATE(
    [Estimated Total Revenue],
    ALLEXCEPT(fact_revenue, dim_route[route_code])
)

Route Estimated Profit = 
CALCULATE(
    [Estimated Total Profit],
    ALLEXCEPT(fact_revenue, dim_route[route_code])
)

Route Profit Margin = 
DIVIDE(
    [Route Estimated Profit],
    [Route Estimated Revenue],
    BLANK()
)
```

### Profitability Classification (Pre-calculated)
```dax
High Revenue High Profit Routes = 
CALCULATE(
    COUNTROWS(fact_revenue),
    fact_revenue[profitability_class] = "High Revenue / High Profit"
)

High Revenue Low Profit Routes = 
CALCULATE(
    COUNTROWS(fact_revenue),
    fact_revenue[profitability_class] = "High Revenue / Low Profit"
)

Low Revenue High Profit Routes = 
CALCULATE(
    COUNTROWS(fact_revenue),
    fact_revenue[profitability_class] = "Low Revenue / High Profit"
)

Low Revenue Low Profit Routes = 
CALCULATE(
    COUNTROWS(fact_revenue),
    fact_revenue[profitability_class] = "Low Revenue / Low Profit"
)
```

---

## 7. Seasonal & Temporal Measures

### Day of Week
```dax
Flights by DayOfWeek = 
CALCULATE(
    [Total Flights],
    ALLEXCEPT(fact_flights, dim_date[day_name])
)

OTP by DayOfWeek = 
CALCULATE(
    [OTP %],
    ALLEXCEPT(fact_flights, dim_date[day_name])
)

Weekend OTP % = 
CALCULATE(
    [OTP %],
    dim_date[is_weekend] = 1
)

Weekday OTP % = 
CALCULATE(
    [OTP %],
    dim_date[is_weekend] = 0
)
```

### Seasonal
```dax
Flights by Season = 
CALCULATE(
    [Total Flights],
    ALLEXCEPT(fact_flights, dim_date[season])
)

OTP by Season = 
CALCULATE(
    [OTP %],
    ALLEXCEPT(fact_flights, dim_date[season])
)
```

### Seasonal Revenue (Modeled/Estimated)
```dax
Estimated Revenue by Season = 
CALCULATE(
    [Estimated Total Revenue],
    ALLEXCEPT(fact_revenue, dim_date[season])
)

Estimated Profit by Season = 
CALCULATE(
    [Estimated Total Profit],
    ALLEXCEPT(fact_revenue, dim_date[season])
)

Estimated Profit Margin by Season = 
CALCULATE(
    [Estimated Profit Margin],
    ALLEXCEPT(fact_revenue, dim_date[season])
)

Estimated Passengers by Season = 
CALCULATE(
    [Estimated Total Passengers],
    ALLEXCEPT(fact_revenue, dim_date[season])
)

Estimated Load Factor by Season = 
CALCULATE(
    [Estimated Load Factor],
    ALLEXCEPT(fact_revenue, dim_date[season])
)

Seasonal Revenue Per Route = 
DIVIDE(
    [Estimated Revenue by Season],
    CALCULATE(
        DISTINCTCOUNT(fact_revenue[route_id]),
        ALLEXCEPT(fact_revenue, dim_date[season])
    ),
    BLANK()
)

Seasonal Profit Per Route = 
DIVIDE(
    [Estimated Profit by Season],
    CALCULATE(
        DISTINCTCOUNT(fact_revenue[route_id]),
        ALLEXCEPT(fact_revenue, dim_date[season])
    ),
    BLANK()
)

Seasonal Profitability Index = 
DIVIDE(
    [Estimated Profit by Season],
    [Estimated Revenue by Season],
    BLANK()
)

Revenue Seasonality Index = 
VAR AvgRevenue = CALCULATE([Estimated Total Revenue], ALL(dim_date[season]))
VAR SeasonRevenue = [Estimated Revenue by Season]
RETURN
    DIVIDE(SeasonRevenue, AvgRevenue, BLANK())

Profit Seasonality Index = 
VAR AvgProfit = CALCULATE([Estimated Total Profit], ALL(dim_date[season]))
VAR SeasonProfit = [Estimated Profit by Season]
RETURN
    DIVIDE(SeasonProfit, AvgProfit, BLANK())
```

### Seasonal Carrier Performance
```dax
Carrier Seasonal Revenue = 
CALCULATE(
    [Estimated Total Revenue],
    ALLEXCEPT(fact_revenue, dim_date[season], dim_airline[carrier_code])
)

Carrier Seasonal Profit = 
CALCULATE(
    [Estimated Total Profit],
    ALLEXCEPT(fact_revenue, dim_date[season], dim_airline[carrier_code])
)

Carrier Seasonal Profit Margin = 
DIVIDE(
    [Carrier Seasonal Profit],
    [Carrier Seasonal Revenue],
    BLANK()
)

Carrier Seasonal Load Factor = 
CALCULATE(
    [Estimated Load Factor],
    ALLEXCEPT(fact_revenue, dim_date[season], dim_airline[carrier_code])
)

Top Carrier by Season Revenue = 
MAXX(
    TOPN(1, 
        SUMMARIZE(
            fact_revenue,
            dim_date[season],
            dim_airline[carrier_code],
            "Revenue", [Estimated Total Revenue]
        ),
        [Revenue], DESC
    ),
    dim_airline[carrier_code]
)
```

### Seasonal Route Performance
```dax
Route Seasonal Revenue = 
CALCULATE(
    [Estimated Total Revenue],
    ALLEXCEPT(fact_revenue, dim_date[season], dim_route[route_code])
)

Route Seasonal Profit = 
CALCULATE(
    [Estimated Total Profit],
    ALLEXCEPT(fact_revenue, dim_date[season], dim_route[route_code])
)

Route Seasonal Profit Margin = 
DIVIDE(
    [Route Seasonal Profit],
    [Route Seasonal Revenue],
    BLANK()
)

Top Routes by Season Revenue = 
TOPN(
    20,
    SUMMARIZE(
        fact_revenue,
        dim_date[season],
        dim_route[route_code],
        "Revenue", [Estimated Total Revenue],
        "Profit", [Estimated Total Profit],
        "Margin", [Estimated Profit Margin]
    ),
    [Revenue], DESC
)

Seasonal Route Rank by Revenue = 
RANKX(
    FILTER(
        ALL(dim_route[route_code]),
        [Route Seasonal Revenue] > 0
    ),
    [Route Seasonal Revenue],
    , DESC, DENSE
)
```

### Departure Period
```dax
Flights by DepPeriod = 
CALCULATE(
    [Total Flights],
    ALLEXCEPT(fact_flights, fact_flights[dep_period])
)

OTP by DepPeriod = 
CALCULATE(
    [OTP %],
    ALLEXCEPT(fact_flights, fact_flights[dep_period])
)
```

---

## 8. Advanced Analytics Measures

### Cancellation Analysis
```dax
Cancellations by Cause = 
ADDCOLUMNS(
    VALUES(fact_flights[cancellation_category]),
    "Count", CALCULATE(COUNTROWS(fact_flights), fact_flights[cancelled_flag] = 1)
)

Carrier Cancellation Rate = 
CALCULATE(
    [Pct Cancelled],
    ALLEXCEPT(fact_flights, dim_airline[carrier_code])
)
```

### Diversion Analysis
```dax
Diversion Rate = 
DIVIDE(
    CALCULATE([Total Flights], fact_flights[diverted_flag] = 1),
    [Total Flights],
    0
)
```

### Benchmarking
```dax
Industry OTP Benchmark = 
CALCULATE(
    [OTP %],
    ALL(fact_flights)
)

Carrier vs Industry OTP Gap = 
[Carrier OTP %] - [Industry OTP Benchmark]

Airport vs Industry OTP Gap = 
[Origin OTP %] - [Industry OTP Benchmark]
```

### What-If Parameters (for sensitivity analysis)
```dax
// Create What-If Parameter in Power BI:
// Name: CASM_WhatIf
// Data Type: Decimal
// Minimum: 0.08
// Maximum: 0.15
// Default: 0.12
// Increment: 0.01

// Then use in custom measures:
Estimated Operating Cost (What-If) = 
CALCULATE(
    SUMX(
        fact_revenue,
        fact_revenue[total_seats_t100] * fact_revenue[avg_distance_t100] * CASM_WhatIf[CASM_WhatIf Value]
    )
)

Estimated Profit (What-If) = 
[Estimated Total Revenue] - [Estimated Operating Cost (What-If)]

Profit Margin (What-If) = 
DIVIDE(
    [Estimated Profit (What-If)],
    [Estimated Total Revenue],
    BLANK()
)
```

---

## 9. Visualization Best Practices

### Conditional Formatting Rules
```dax
// OTP % Color Scale
OTP Color = 
SWITCH(
    TRUE(),
    [OTP %] >= 0.85, "#2E7D32",      // Green
    [OTP %] >= 0.75, "#F9A825",      // Amber
    [OTP %] >= 0.65, "#EF6C00",      // Orange
    "#C62828"                        // Red
)

// Delay Severity Color
Delay Color = 
SWITCH(
    SELECTEDVALUE(fact_flights[delay_category]),
    "Severe (90+)", "#C62828",
    "Moderate (45-90)", "#EF6C00",
    "Minor (15-45)", "#F9A825",
    "On-Time", "#2E7D32",
    "#FFFFFF"
)

// Profitability Matrix Color
Profitability Color = 
SWITCH(
    SELECTEDVALUE(fact_revenue[profitability_class]),
    "High Revenue / High Profit", "#2E7D32",
    "Low Revenue / High Profit", "#1565C0",
    "High Revenue / Low Profit", "#EF6C00",
    "Low Revenue / Low Profit", "#C62828",
    "#FFFFFF"
)
```

### KPIs
```dax
// KPI: OTP Target (80%)
OTP KPI = 
VAR Actual = [OTP %]
VAR Target = 0.80
VAR Status = IF(Actual >= Target, 1, -1)
RETURN
    Actual

// KPI: Profit Margin Target (10%)
Profit Margin KPI = 
VAR Actual = [Estimated Profit Margin]
VAR Target = 0.10
VAR Status = IF(Actual >= Target, 1, -1)
RETURN
    Actual
```

---

## 10. Data Quality Flags

```dax
Data Freshness (Days) = 
DATEDIFF(
    MAX(dim_date[date]),
    TODAY(),
    DAY
)

Missing Delay Data % = 
DIVIDE(
    CALCULATE(COUNTROWS(fact_flights), ISBLANK(fact_flights[arr_delay_min])),
    COUNTROWS(fact_flights),
    0
)

Unmapped Routes % = 
DIVIDE(
    CALCULATE(COUNTROWS(fact_flights), fact_flights[route_id] = BLANK()),
    COUNTROWS(fact_flights),
    0
)
```

---

## Implementation Checklist

- [ ] Create all base measures in Power BI
- [ ] Set up Time Intelligence (mark dim_date as Date Table)
- [ ] Configure relationships (all Single direction: Dim → Fact)
- [ ] Add What-If parameters for CASM sensitivity
- [ ] Apply conditional formatting rules
- [ ] Set display folders for organization
- [ ] Add measure descriptions for end users
- [ ] Configure KPIs with targets
- [ ] Test all measures with sample data
- [ ] Document all "Estimated" labels in report

---

## Folder Structure in Power BI

```
📁 Flight Operations
  📁 On-Time Performance
    ✅ OTP %
    ✅ Total Flights
    ✅ On-Time Flights
    ✅ Pct Delayed
    ✅ Pct Cancelled
  📁 Delays
    ✅ Avg Arrival Delay
    ✅ Avg Departure Delay
    ✅ Delay Categories
    ✅ Delay Causes
  📁 Taxi & Block Times
    ✅ Avg Taxi Out
    ✅ Avg Taxi In
    ✅ Avg Air Time
  📁 Cancellations & Diversions
    ✅ Cancellation Rate
    ✅ Cancellation Causes
    ✅ Diversion Rate
  📁 Time Intelligence
    ✅ YTD/MTD/QTD
    ✅ YoY/YoY%
    ✅ Rolling Averages
📁 Carrier Analytics
  📁 Performance
    ✅ Carrier OTP %
    ✅ Carrier Avg Delay
    ✅ Carrier Flights
    ✅ Carrier Market Share
  📁 Rankings
    ✅ Carrier OTP Rank
    ✅ Carrier Delay Rank
📁 Airport Analytics
  📁 Operations
    ✅ Airport Flights (Origin/Dest)
    ✅ Airport OTP %
  📁 Efficiency
    ✅ Airport Efficiency Score
    ✅ Airport Efficiency Rank
📁 Route Analytics
  📁 Operations
    ✅ Route Flights
    ✅ Route Distance
    ✅ Route OTP %
    ✅ Route Avg Delay
  📁 Categories
    ✅ Short/Medium/Long/Ultra Haul
📁 Revenue Analytics (Modeled)
  📁 Summary
    ✅ Est. Total Revenue
    ✅ Est. Total Profit
    ✅ Est. Profit Margin
    ✅ Est. Load Factor
  📁 By Carrier
    ✅ Carrier Est. Revenue
    ✅ Carrier Est. Profit
    ✅ Carrier Profit Margin
    ✅ Carrier Seasonal Revenue
    ✅ Carrier Seasonal Profit
    ✅ Carrier Seasonal Profit Margin
    ✅ Carrier Seasonal Load Factor
    ✅ Top Carrier by Season Revenue
  📁 By Route
    ✅ Route Est. Revenue
    ✅ Route Est. Profit
    ✅ Route Profit Margin
    ✅ Route Seasonal Revenue
    ✅ Route Seasonal Profit
    ✅ Route Seasonal Profit Margin
    ✅ Top Routes by Season Revenue
    ✅ Seasonal Route Rank by Revenue
  📁 Profitability Matrix
    ✅ High Rev/High Profit
    ✅ High Rev/Low Profit
    ✅ Low Rev/High Profit
    ✅ Low Rev/Low Profit
📁 Time & Seasonal
  📁 Day of Week
    ✅ Flights by Day
    ✅ OTP by Day
  📁 Season
    ✅ Flights by Season
    ✅ OTP by Season
    ✅ Est. Revenue by Season
    ✅ Est. Profit by Season
    ✅ Est. Profit Margin by Season
    ✅ Est. Passengers by Season
    ✅ Est. Load Factor by Season
    ✅ Revenue Per Route by Season
    ✅ Profit Per Route by Season
    ✅ Seasonality Index (Revenue)
    ✅ Seasonality Index (Profit)
  📁 Departure Period
    ✅ Flights by Period
    ✅ OTP by Period
📁 Benchmarks & KPIs
  ✅ Industry OTP Benchmark
  ✅ Carrier vs Industry Gap
  ✅ OTP KPI (Target 80%)
  ✅ Profit Margin KPI (Target 10%)
📁 What-If Analysis
  ✅ CASM Sensitivity
  ✅ Est. Profit (What-If)
📁 Data Quality
  ✅ Data Freshness
  ✅ Missing Data %
  ✅ Unmapped Routes %
```

---

## Notes for Report Developers

1. **Always label revenue measures as "Estimated" or "Modeled"** in visuals
2. **Use DIVIDE()** for all division to handle blanks/zeros
3. **Mark dim_date as Date Table** in Power BI for time intelligence
4. **Hide surrogate keys** (date_id, airline_id, airport_id, route_id) from report view
5. **Set relationships** to Single direction (Dimension → Fact)
6. **Use ALLEXCEPT** for carrier/airport/route level calculations
7. **Filter cancelled_flag = 0** for delay calculations
8. **Pre-calculated columns** in dim_airport (efficiency_score) and fact_revenue (profitability_class) are ready to use
9. **What-If parameter** CASM enables sensitivity analysis
10. **Validation**: All 33 automated checks pass - data is production ready