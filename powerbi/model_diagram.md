# Power BI Data Model
## Airline Operations & Revenue Intelligence Platform

---
> **Star Schema**: All relationships are Single direction (Dimension → Fact)
> **Date Table**: dim_date marked as Date Table for Time Intelligence

---

## Model Diagram (Mermaid)

```mermaid
erDiagram
    DIM_DATE ||--o{ FACT_FLIGHTS : "date_id"
    DIM_AIRLINE ||--o{ FACT_FLIGHTS : "airline_id"
    DIM_AIRPORT ||--o{ FACT_FLIGHTS : "origin_airport_id"
    DIM_AIRPORT ||--o{ FACT_FLIGHTS : "dest_airport_id"
    DIM_ROUTE ||--o{ FACT_FLIGHTS : "route_id"
    
    DIM_DATE ||--o{ FACT_REVENUE : "date_id"
    DIM_AIRLINE ||--o{ FACT_REVENUE : "airline_id"
    DIM_ROUTE ||--o{ FACT_REVENUE : "route_id"

    DIM_DATE {
        int date_id PK "YYYYMMDD"
        date date
        int year
        int quarter
        int month
        string month_name
        int week
        int day
        string day_name
        int day_of_week "1=Mon"
        boolean is_weekend
        string season
        string year_month
        string year_quarter
    }

    DIM_AIRLINE {
        int airline_id PK
        string carrier_code "WN, DL, AA..."
        string airline_name
    }

    DIM_AIRPORT {
        int airport_id PK
        string airport_code "IATA"
        string airport_name
        string city
        string state
        float latitude
        float longitude
        float efficiency_score
        int efficiency_rank
        float otp_pct
        float cancel_pct
        float delay_severity_score
        float taxi_score
    }

    DIM_ROUTE {
        int route_id PK
        int origin_airport_id FK
        int dest_airport_id FK
        string origin_code
        string dest_code
        string route_code "ORIG-DEST"
        float distance_miles
        string distance_category
    }

    FACT_FLIGHTS {
        bigint flight_id PK
        int date_id FK
        int airline_id FK
        int origin_airport_id FK
        int dest_airport_id FK
        int route_id FK
        int sched_dep_time_min
        int actual_dep_time_min
        int sched_arr_time_min
        int actual_arr_time_min
        float dep_delay_min
        float arr_delay_min
        float taxi_out_min
        float taxi_in_min
        float air_time_min
        float distance_miles
        boolean cancelled_flag
        string cancellation_category
        boolean diverted_flag
        float carrier_delay_min
        float weather_delay_min
        float nas_delay_min
        float security_delay_min
        float late_aircraft_delay_min
        boolean is_delayed
        string delay_category
        int dep_hour
        string dep_period
        string day_of_week_name
        boolean is_weekend
        string month_name
        int quarter
        string season
        string distance_category
        string primary_delay_cause
    }

    FACT_REVENUE {
        bigint revenue_id PK
        int date_id FK
        int airline_id FK
        int route_id FK
        int estimated_passengers
        float estimated_ticket_revenue
        float estimated_load_factor
        float estimated_operating_cost
        float estimated_profit
        float profit_margin
        float revenue_per_passenger
        float revenue_per_flight
        int year
        int quarter
        int month
        string profitability_class
    }
```

---

## Relationship Details

| From (Dimension) | To (Fact) | Column | Cardinality | Filter Direction |
|------------------|-----------|--------|-------------|------------------|
| DIM_DATE | FACT_FLIGHTS | date_id | 1:* | Single (Dim → Fact) |
| DIM_AIRLINE | FACT_FLIGHTS | airline_id | 1:* | Single (Dim → Fact) |
| DIM_AIRPORT | FACT_FLIGHTS (Origin) | origin_airport_id | 1:* | Single (Dim → Fact) |
| DIM_AIRPORT | FACT_FLIGHTS (Dest) | dest_airport_id | 1:* | Single (Dim → Fact) |
| DIM_ROUTE | FACT_FLIGHTS | route_id | 1:* | Single (Dim → Fact) |
| DIM_DATE | FACT_REVENUE | date_id | 1:* | Single (Dim → Fact) |
| DIM_AIRLINE | FACT_REVENUE | airline_id | 1:* | Single (Dim → Fact) |
| DIM_ROUTE | FACT_REVENUE | route_id | 1:* | Single (Dim → Fact) |

---

## Hidden Columns (Not visible in report view)

| Table | Hidden Columns |
|-------|----------------|
| DIM_DATE | date_id, year_quarter, year_start, quarter_start, month_start |
| DIM_AIRLINE | airline_id |
| DIM_AIRPORT | airport_id, latitude, longitude, efficiency_rank, delay_severity_score, taxi_score, cancel_pct |
| DIM_ROUTE | route_id, origin_airport_id, dest_airport_id |
| FACT_FLIGHTS | flight_id, date_id, airline_id, origin_airport_id, dest_airport_id, route_id |
| FACT_REVENUE | revenue_id, date_id, airline_id, route_id |

---

## Calculated Columns (Pre-built in ETL)

### DIM_AIRPORT
- `efficiency_score` - Weighted composite (OTP 40%, Cancellation 25%, Delay 20%, Taxi 15%)
- `efficiency_rank` - Rank by efficiency_score (1 = best)
- `otp_pct` - On-Time Performance %
- `cancel_pct` - Non-cancellation %
- `delay_severity_score` - Normalized delay severity
- `taxi_score` - Normalized taxi performance

### FACT_REVENUE
- `profitability_class` - 2×2 matrix: "High Revenue / High Profit", "High Revenue / Low Profit", "Low Revenue / High Profit", "Low Revenue / Low Profit"
- All revenue columns prefixed with `estimated_` or `modeled_`

### FACT_FLIGHTS
- `delay_category` - "On-Time", "Minor (15-45)", "Moderate (45-90)", "Severe (90+)"
- `dep_period` - "Early Morning", "Morning", "Afternoon", "Evening", "Night"
- `distance_category` - "Short Haul", "Medium Haul", "Long Haul", "Ultra Long Haul"
- `primary_delay_cause` - "Carrier", "Weather", "NAS", "Security", "Late Aircraft", "On-Time"
- `is_delayed` - Boolean (arr_delay >= 15)

---

## Recommended Visuals by Table

### DIM_DATE (Time Intelligence)
- Calendar hierarchy: Year → Quarter → Month → Week → Day
- Mark as Date Table → date column
- Enable: Year, Quarter, Month, Week, Day hierarchies

### DIM_AIRLINE
- Slicer: carrier_code (WN, DL, AA, UA, OO, NK, B6, AS, F9, etc.)
- Search enabled for carrier lookup

### DIM_AIRPORT
- Map visual: latitude/longitude for airport locations
- Slicer: airport_code, city, state
- Search enabled

### DIM_ROUTE
- Slicer: route_code (e.g., "LAX-JFK"), origin_code, dest_code
- Distance category filter

### FACT_FLIGHTS (Operational)
- Large fact table (7M rows) - use DirectQuery or aggregations
- Partitioned by date_id for performance
- Key metrics: delays, cancellations, diversions, taxi times

### FACT_REVENUE (Modeled Revenue)
- Smaller fact table (29K rows) - Import mode fine
- All metrics labeled "Estimated" in visuals
- Profitability classification for 2×2 matrix

---

## Performance Recommendations

1. **FACT_FLIGHTS**: Use aggregations for large dataset
   - Create aggregation table at carrier-route-month level
   - Set detail rows to fact_flights
   - Enable "Show detail rows" for drill-through

2. **FACT_REVENUE**: Import mode (29K rows is small)

3. **DIM_AIRPORT**: Use for map visuals with lat/long

4. **DIM_DATE**: Mark as Date Table for time intelligence

5. **Relationships**: All Single direction, no bi-directional

6. **Measures**: Use calculation groups for time intelligence (YoY, MoM, YTD, MTD)

---

## What-If Parameters

| Parameter | Table | Min | Max | Default | Increment |
|-----------|-------|-----|-----|---------|-----------|
| CASM | CASM_WhatIf | 0.08 | 0.15 | 0.12 | 0.01 |

Usage in measures:
```dax
Estimated Operating Cost (What-If) = 
SUMX(
    fact_revenue,
    fact_revenue[total_seats_t100] * fact_revenue[avg_distance_t100] * CASM_WhatIf[CASM_WhatIf Value]
)
```

---

## Data Labels Convention

| Prefix | Meaning | Display Name Example |
|--------|---------|---------------------|
| (none) | Observed/Actual | "Arrival Delay" |
| `Estimated ` | Scaled from sample | "Estimated Ticket Revenue (Modeled)" |
| `Modeled ` | Derived via formula | "Modeled Operating Cost" |

All revenue visuals must include "(Modeled)" or "(Estimated)" in titles.