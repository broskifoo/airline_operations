# ETL Design Document
## Airline Operations & Revenue Intelligence Platform

---

## Overview

This document describes the Extract, Transform, Load (ETL) pipeline for converting raw airline data into a star-schema analytical model ready for Power BI.

---

## Source Systems

| Source | Format | Frequency | Size (2024) | Access |
|--------|--------|-----------|-------------|--------|
| BTS On-Time Performance (Kaggle) | CSV | Monthly (3-mo lag) | 1.3 GB / 7M rows | Downloaded |
| BTS DB1B Market | CSV | Quarterly | 1.87 GB | Downloaded |
| BTS DB1B Coupon | CSV | Quarterly | 2.14 GB | Downloaded |
| BTS T-100 Segment | CSV | Monthly | TBD | Planned |
| BTS Master Coordinate (Airports) | CSV | Static | ~500 KB | Downloadable |
| BTS Carrier Lookup | CSV | Static | ~50 KB | Downloadable |

---

## Staging Layer

**Technology**: DuckDB (embedded analytical database)
**Format**: Parquet (columnar, compressed)
**Location**: `data/processed/staging/`

### Staging Tables

| Table | Source | Key Transformations |
|-------|--------|---------------------|
| `stg_flights` | Kaggle 2024 CSV | Type casting, column rename to snake_case |
| `stg_db1b_market` | DB1B Market CSV | Select key columns, filter US domestic |
| `stg_db1b_coupon` | DB1B Coupon CSV | Select key columns, filter US domestic |
| `stg_t100_segment` | T-100 CSV | Select key columns (when available) |
| `stg_airports` | BTS Master Coordinate | Clean airport metadata |
| `stg_carriers` | BTS Carrier Lookup | Map carrier codes to names |

---

## Dimension Build Logic

### DIM_DATE
```sql
-- Generate date spine for 2024 (extendable)
WITH date_spine AS (
    SELECT generate_series('2024-01-01'::date, '2024-12-31'::date, '1 day'::interval) AS date
)
SELECT
    CAST(strftime(date, '%Y%m%d') AS INTEGER) AS date_id,
    date,
    EXTRACT(YEAR FROM date) AS year,
    EXTRACT(QUARTER FROM date) AS quarter,
    EXTRACT(MONTH FROM date) AS month,
    strftime(date, '%B') AS month_name,
    EXTRACT(WEEK FROM date) AS week,
    EXTRACT(DAY FROM date) AS day,
    strftime(date, '%A') AS day_name,
    CASE WHEN EXTRACT(ISODOW FROM date) IN (6,7) THEN TRUE ELSE FALSE END AS weekend,
    CASE 
        WHEN EXTRACT(MONTH FROM date) IN (3,4,5) THEN 'Spring'
        WHEN EXTRACT(MONTH FROM date) IN (6,7,8) THEN 'Summer'
        WHEN EXTRACT(MONTH FROM date) IN (9,10,11) THEN 'Fall'
        ELSE 'Winter'
    END AS season
FROM date_spine;
```

### DIM_AIRLINE
```sql
-- From stg_flights distinct carriers + carrier lookup
SELECT
    ROW_NUMBER() OVER (ORDER BY carrier_code) AS airline_id,
    carrier_code,
    carrier_name
FROM (
    SELECT DISTINCT op_unique_carrier AS carrier_code FROM stg_flights
    UNION
    SELECT DISTINCT carrier_code FROM stg_carriers
) c
LEFT JOIN stg_carriers cl ON c.carrier_code = cl.code;
```

### DIM_AIRPORT
```sql
-- From stg_flights distinct airports + master coordinate
SELECT
    ROW_NUMBER() OVER (ORDER BY airport_code) AS airport_id,
    airport_code,
    airport_name,
    city,
    state,
    latitude,
    longitude
FROM (
    SELECT DISTINCT origin AS airport_code FROM stg_flights
    UNION
    SELECT DISTINCT dest AS airport_code FROM stg_flights
) a
LEFT JOIN stg_airports am ON a.airport_code = am.iata_code;
```

### DIM_ROUTE
```sql
-- Unique Origin-Dest pairs from fact
SELECT
    ROW_NUMBER() OVER (ORDER BY origin_airport_id, dest_airport_id) AS route_id,
    origin_airport_id,
    dest_airport_id,
    AVG(distance) AS distance,
    CASE 
        WHEN AVG(distance) < 500 THEN 'Short Haul'
        WHEN AVG(distance) < 1500 THEN 'Medium Haul'
        WHEN AVG(distance) < 3000 THEN 'Long Haul'
        ELSE 'Ultra Long Haul'
    END AS distance_category
FROM fact_flights_clean
GROUP BY origin_airport_id, dest_airport_id;
```

---

## Fact Table Build Logic

### FACT_FLIGHTS (Operational)

```sql
WITH cleaned AS (
    SELECT
        -- Surrogate keys (joined to dimensions)
        CAST(strftime(fl_date, '%Y%m%d') AS INTEGER) AS date_id,
        al.airline_id,
        ap_origin.airport_id AS origin_airport_id,
        ap_dest.airport_id AS dest_airport_id,
        r.route_id,
        
        -- Time conversions (hhmm → minutes since midnight)
        crs_dep_time,
        CASE WHEN dep_time = 2400 THEN 0 ELSE dep_time END AS dep_time,
        crs_arr_time,
        CASE WHEN arr_time = 2400 THEN 0 ELSE arr_time END AS arr_time,
        
        -- Delays (minutes)
        CASE WHEN cancelled = 1 THEN 0 ELSE dep_delay END AS dep_delay,
        CASE WHEN cancelled = 1 THEN 0 ELSE arr_delay END AS arr_delay,
        
        -- Taxi & air time
        taxi_out,
        taxi_in,
        air_time,
        distance,
        
        -- Status flags
        cancelled,
        cancellation_code,
        diverted,
        
        -- Delay causes (already 0-filled in Kaggle)
        carrier_delay,
        weather_delay,
        nas_delay,
        security_delay,
        late_aircraft_delay,
        
        -- Derived fields
        CASE WHEN cancelled = 1 THEN 0 ELSE CASE WHEN arr_delay >= 15 THEN 1 ELSE 0 END END AS is_delayed,
        CASE 
            WHEN cancelled = 1 THEN 'Cancelled'
            WHEN arr_delay < 15 THEN 'On-Time'
            WHEN arr_delay < 45 THEN 'Minor (15-45)'
            WHEN arr_delay < 90 THEN 'Moderate (45-90)'
            ELSE 'Severe (90+)'
        END AS delay_category,
        
        -- Departure hour & period
        FLOOR(crs_dep_time / 100) AS dep_hour,
        CASE 
            WHEN FLOOR(crs_dep_time / 100) BETWEEN 5 AND 7 THEN 'Early Morning'
            WHEN FLOOR(crs_dep_time / 100) BETWEEN 8 AND 11 THEN 'Morning'
            WHEN FLOOR(crs_dep_time / 100) BETWEEN 12 AND 16 THEN 'Afternoon'
            WHEN FLOOR(crs_dep_time / 100) BETWEEN 17 AND 20 THEN 'Evening'
            ELSE 'Night'
        END AS dep_period,
        
        -- Date parts
        EXTRACT(DOW FROM fl_date) + 1 AS day_of_week,  -- 1=Mon
        CASE WHEN EXTRACT(ISODOW FROM fl_date) IN (6,7) THEN TRUE ELSE FALSE END AS is_weekend
        
    FROM stg_flights f
    LEFT JOIN dim_airline al ON f.op_unique_carrier = al.carrier_code
    LEFT JOIN dim_airport ap_origin ON f.origin = ap_origin.airport_code
    LEFT JOIN dim_airport ap_dest ON f.dest = ap_dest.airport_code
    LEFT JOIN dim_route r ON ap_origin.airport_id = r.origin_airport_id AND ap_dest.airport_id = r.dest_airport_id
    WHERE f.distance > 0  -- Filter impossible distances
)
SELECT
    ROW_NUMBER() OVER (ORDER BY date_id, airline_id, origin_airport_id, dest_airport_id) AS flight_id,
    *
FROM cleaned;
```

### FACT_REVENUE (Modeled)

```sql
-- DB1B Market: Route-Carrier-Quarter revenue estimation
WITH db1b_quarterly AS (
    SELECT
        m.year,
        m.quarter,
        al.airline_id,
        r.route_id,
        SUM(m.passengers * 10) AS estimated_passengers,  -- 10% sample × 10
        SUM(m.mkt_fare * m.passengers * 10) AS estimated_ticket_revenue,
        AVG(m.mkt_distance) AS avg_distance
    FROM stg_db1b_market m
    LEFT JOIN dim_airline al ON m.op_carrier = al.carrier_code  -- Use operating carrier
    LEFT JOIN dim_airport ap_o ON m.origin = ap_o.airport_code
    LEFT JOIN dim_airport ap_d ON m.dest = ap_d.airport_code
    LEFT JOIN dim_route r ON ap_o.airport_id = r.origin_airport_id AND ap_d.airport_id = r.dest_airport_id
    WHERE m.bulk_fare = 0  -- Exclude bulk fares
    GROUP BY m.year, m.quarter, al.airline_id, r.route_id
),
t100_monthly AS (
    -- T-100: Monthly seats & departures by carrier-route
    SELECT
        t.year,
        t.month,
        al.airline_id,
        r.route_id,
        SUM(t.seats) AS total_seats,
        SUM(t.departures_performed) AS total_departures,
        SUM(t.passengers) AS total_passengers
    FROM stg_t100_segment t
    LEFT JOIN dim_airline al ON t.carrier = al.carrier_code
    LEFT JOIN dim_airport ap_o ON t.origin = ap_o.airport_code
    LEFT JOIN dim_airport ap_d ON t.dest = ap_d.airport_code
    LEFT JOIN dim_route r ON ap_o.airport_id = r.origin_airport_id AND ap_d.airport_id = r.dest_airport_id
    GROUP BY t.year, t.month, al.airline_id, r.route_id
),
revenue_modeled AS (
    SELECT
        dq.year,
        dq.quarter,
        al.airline_id,
        r.route_id,
        dq.estimated_passengers,
        dq.estimated_ticket_revenue,
        -- Load factor from T-100 (average monthly)
        AVG(tm.total_passengers / NULLIF(tm.total_seats, 0)) AS estimated_load_factor,
        -- Operating cost: Seats × Distance × CASM ($0.12/ASM)
        SUM(tm.total_seats * dq.avg_distance * 0.12) AS estimated_operating_cost
    FROM db1b_quarterly dq
    LEFT JOIN t100_monthly tm 
        ON dq.year = tm.year 
        AND dq.quarter = CEIL(tm.month / 3.0)
        AND dq.airline_id = tm.airline_id
        AND dq.route_id = tm.route_id
    LEFT JOIN dim_airline al ON dq.airline_id = al.airline_id
    LEFT JOIN dim_route r ON dq.route_id = r.route_id
    GROUP BY dq.year, dq.quarter, al.airline_id, r.route_id, dq.estimated_passengers, dq.estimated_ticket_revenue
)
SELECT
    ROW_NUMBER() OVER (ORDER BY year, quarter, airline_id, route_id) AS revenue_id,
    CAST(CONCAT(year, LPAD(quarter * 3 - 2, 2, '0'), '01') AS INTEGER) AS date_id,  -- First day of quarter
    year,
    quarter,
    airline_id,
    route_id,
    estimated_passengers,
    estimated_ticket_venue,
    estimated_load_factor,
    estimated_operating_cost,
    (estimated_ticket_revenue - estimated_operating_cost) AS estimated_profit,
    CASE WHEN estimated_ticket_revenue > 0 
         THEN (estimated_ticket_revenue - estimated_operating_cost) / estimated_ticket_revenue 
         ELSE NULL END AS profit_margin,
    CASE WHEN estimated_passengers > 0 
         THEN estimated_ticket_revenue / estimated_passengers 
         ELSE NULL END AS revenue_per_passenger,
    CASE WHEN total_departures > 0 
         THEN estimated_ticket_revenue / total_departures 
         ELSE NULL END AS revenue_per_flight
FROM revenue_modeled;
```

---

## Incremental Load Strategy

| Layer | Strategy | Watermark |
|-------|----------|-----------|
| Staging | Full replace (monthly files) | File timestamp |
| Dimensions | SCD Type 1 (overwrite) | Max date in fact |
| FACT_FLIGHTS | Append (partition by month) | Max flight_date |
| FACT_REVENUE | Full rebuild (quarterly) | DB1B quarter |

---

## Validation Checks (Post-Load)

```sql
-- 1. Referential Integrity
SELECT COUNT(*) FROM fact_flights f
LEFT JOIN dim_date d ON f.date_id = d.date_id
WHERE d.date_id IS NULL;  -- Should be 0

-- 2. No negative distances
SELECT COUNT(*) FROM fact_flights WHERE distance < 0;  -- Should be 0

-- 3. Delay reasonableness
SELECT COUNT(*) FROM fact_flights WHERE arr_delay > 1440;  -- Flag for review

-- 4. Cancellation consistency
SELECT COUNT(*) FROM fact_flights WHERE cancelled = 1 AND arr_delay != 0;  -- Should be 0

-- 5. Revenue fact completeness
SELECT COUNT(*) FROM fact_revenue WHERE estimated_ticket_revenue IS NULL;  -- Should be 0

-- 6. Row counts
SELECT 'fact_flights' AS table, COUNT(*) FROM fact_flights
UNION ALL SELECT 'fact_revenue', COUNT(*) FROM fact_revenue
UNION ALL SELECT 'dim_date', COUNT(*) FROM dim_date
UNION ALL SELECT 'dim_airline', COUNT(*) FROM dim_airline
UNION ALL SELECT 'dim_airport', COUNT(*) FROM dim_airport
UNION ALL SELECT 'dim_route', COUNT(*) FROM dim_route;
```

---

## Error Handling & Logging

| Stage | Error Type | Action |
|-------|------------|--------|
| Extract | File not found | Alert, retry with backoff |
| Extract | Corrupt CSV | Log bad lines, continue |
| Transform | Data type mismatch | Coerce with logging, flag rows |
| Transform | FK lookup failure | Assign to "Unknown" dimension member |
| Load | Constraint violation | Rollback batch, alert |
| Validation | Check failure | Alert, do not promote to production |

---

## Performance Considerations

- **DuckDB**: Use for all staging & transformation (columnar, parallel)
- **Partitioning**: FACT_FLIGHTS by month (Parquet files)
- **Indexes**: Dimension PKs, Fact FKs
- **Memory**: Process in chunks (100K rows) for large CSV reads
- **Parallel**: Dimension builds independent; Fact builds after dims

---

## Deployment

```bash
# Run full ETL
python src/etl_pipeline.py --full

# Run incremental (new month)
python src/etl_pipeline.py --incremental --year 2024 --month 7

# Validate only
python src/validation.py --all
```