# Assumptions & Methodology Documentation
## Airline Operations & Revenue Intelligence Platform

---

## Core Principle

**All estimated/modeled metrics are explicitly labeled and never presented as actual airline financial data.**

---

## Revenue Estimation Assumptions

### 1. DB1B 10% Sample Scaling
- **Assumption**: DB1B Market/Coupon data represents a 10% random sample of all tickets
- **Method**: Multiply `Passengers` and fare-based revenue by 10
- **Label**: `Estimated_Passengers`, `Estimated_Ticket_Revenue`
- **Limitation**: Sample variance; small markets may have high relative error
- **Validation**: Compare scaled totals to T-100 enplanements where available

### 2. Fare Representativeness
- **Assumption**: `MktFare` (market fare = ItinYield × MktMilesFlown) approximates average ticket revenue per passenger
- **Exclusions**: 
  - Bulk fares (`BulkFare = 1`) — removed per BTS guidance
  - First class fares (anomalously low in DB1B) — removed per academic practice
  - Fares < $20 or > $9998 — truncated per Borenstein methodology
- **Label**: `Estimated_Ticket_Revenue`

### 3. Carrier Mapping
- **Assumption**: DB1B `OpCarrier` (operating carrier) maps to On-Time `op_unique_carrier`
- **Reality**: DB1B has `RPCarrier` (reporting), `TkCarrier` (ticketing), `OpCarrier` (operating)
- **Decision**: Use `OpCarrier` for operational analysis; `RPCarrier` for revenue attribution
- **Gap**: Carrier code changes (mergers) — use BTS carrier mapping table

### 4. Operating Cost Model (CASM)
- **Assumption**: Cost per Available Seat Mile (CASM) = $0.12 (industry average 2024)
- **Source**: Industry reports (IATA, airline 10-K filings average)
- **Formula**: `Estimated_Operating_Cost = Total_Seats × Distance × $0.12`
- **Label**: `Estimated_Operating_Cost` (Modeled)
- **Limitation**: 
  - Actual CASM varies by carrier (ULCC ~$0.08, Legacy ~$0.15)
  - Excludes non-fuel costs allocation
  - No stage-length adjustment
- **Future Improvement**: Carrier-specific CASM from BTS Form 41 (P-12)

### 5. Load Factor Estimation
- **Source**: T-100 Segment `Passengers / Seats` by carrier-route-month
- **Assumption**: DB1B quarterly averages align with T-100 monthly
- **Method**: Average monthly load factor across quarter
- **Label**: `Estimated_Load_Factor`

### 6. Profit Calculation
- **Formula**: `Estimated_Profit = Estimated_Ticket_Revenue - Estimated_Operating_Cost`
- **Excludes**: Ancillary revenue, cargo, loyalty program, non-operating items
- **Label**: `Estimated_Profit` (Modeled)
- **Profit Margin**: `Estimated_Profit / Estimated_Ticket_Revenue`

---

## Operational Metrics Assumptions

### 1. Delay Definition (BTS Standard)
- **On-Time**: Arrival within 15 minutes of scheduled (`arr_delay < 15`)
- **Delayed**: Arrival 15+ minutes late (`arr_delay >= 15`)
- **Cancelled**: `cancelled = 1` (excluded from delay calculations)
- **Diverted**: `diverted = 1` (included in operations, excluded from OTP)

### 2. Delay Cause Attribution
- **Source**: BTS reports prorated causes (each cause ≥5 min gets share)
- **Kaggle Dataset**: Pre-filled with 0 for non-applicable causes
- **Assumption**: Sum of 5 causes ≈ total delay for delayed flights
- **Primary Cause**: `argmax(Carrier, Weather, NAS, Security, Late_Aircraft)`

### 3. Cancellation Codes
| Code | Meaning | Category |
|------|---------|----------|
| A | Carrier | Carrier |
| B | Weather | Weather |
| C | National Aviation System | NAS |
| D | Security | Security |
| (null) | Not cancelled / Unknown | — |

### 4. Time Conversions
- **Format**: hhmm (e.g., 1324 = 13:24, 8 = 00:08, 2400 = 00:00 next day)
- **Conversion**: `minutes = (hhmm // 100) * 60 + (hhmm % 100)`
- **Edge Case**: 2400 → 0 (midnight)

### 5. Airport Codes
- **Standard**: 3-letter IATA codes
- **Validation**: Cross-reference BTS Master Coordinate table
- **Non-US**: Filtered out (DB1B/On-Time are US domestic only)

---

## Data Quality Assumptions

### 1. Missing Actual Times
- **Cause**: Cancelled flights have no `dep_time`, `arr_time`, `wheels_off`, `wheels_on`
- **Handling**: 
  - Set `dep_delay = arr_delay = 0` for cancelled flights
  - Keep `cancelled = 1` flag
  - Do not impute taxi/air time

### 2. Negative Delays
- **Meaning**: Early departure/arrival
- **Handling**: Keep as negative (do not clip to 0)
- **OTP Calculation**: Only `arr_delay >= 15` counts as delayed

### 3. Outlier Delays
- **Threshold**: > 1440 minutes (24 hours)
- **Action**: Cap at 1440, flag `is_outlier = true`
- **Rationale**: Likely data entry errors (e.g., date mismatch)

### 4. Distance Validation
- **Range**: 31 - 5095 miles (observed in 2024 data)
- **Action**: Drop rows with `distance <= 0` or `distance > 6000`

### 5. Duplicate Flights
- **Key**: `fl_date + op_unique_carrier + op_carrier_fl_num + origin + dest`
- **Action**: Keep first occurrence, log count

---

## Power BI Modeling Assumptions

### 1. Date Table
- **Type**: Standard calendar (not fiscal)
- **Range**: 2024-01-01 to 2024-12-31 (extendable)
- **Mark as Date Table**: Yes

### 2. Relationships
- **All**: Single direction (Dimension → Fact)
- **No**: Many-to-many, bi-directional filters

### 3. DAX Measures
- **Division**: Always use `DIVIDE(numerator, denominator, 0)`
- **Time Intelligence**: Requires contiguous date table
- **Revenue Measures**: Explicitly labeled "Estimated" in display names

### 4. What-If Parameters
- **CASM**: Parameter for operating cost sensitivity ($0.08 - $0.15)
- **Load Factor Target**: Parameter for capacity planning (0.75 - 0.95)

---

## Limitations & Caveats

| Area | Limitation | Impact |
|------|------------|--------|
| Revenue | DB1B 10% sample × 10 ≠ actual revenue | Directional only; not for financial reporting |
| Revenue | No ancillary revenue (bags, seats, etc.) | Understates total revenue |
| Revenue | No cargo revenue | Understates for cargo-heavy routes |
| Cost | Single CASM ($0.12) for all carriers | Misstates profitability by carrier type |
| Cost | No airport-specific costs (landing fees, etc.) | Route-level cost approximation |
| On-Time | Only marketing carriers ≥0.5% revenue | Excludes regional/small carriers |
| On-Time | 3-month reporting lag | Not real-time |
| DB1B | Quarterly (pre-Jul 2025) | Monthly trends require interpolation |
| DB1B | No flight-level detail | Cannot join to specific On-Time flights |

---

## Labeling Convention

| Prefix | Meaning | Example |
|--------|---------|---------|
| (none) | Observed/Actual | `arr_delay`, `cancelled`, `distance` |
| `estimated_` | Scaled from sample | `estimated_passengers`, `estimated_ticket_revenue` |
| `modeled_` | Derived via formula | `modeled_operating_cost`, `modeled_profit` |

**Display Names in Power BI**: 
- "Estimated Passengers (Modeled)"
- "Estimated Ticket Revenue (Modeled)"
- "Modeled Operating Cost"
- "Modeled Profit Margin"

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-08-21 | Initial assumptions for 2024 analysis |