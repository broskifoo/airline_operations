# Data Validation Report

**Total Checks**: 33 | **Passed**: 33 | **Failed**: 0 | **Pass Rate**: 100.0%

---

## dim_date [PASS]

4/4 checks passed

| Check | Status | Message |
|-------|--------|---------|
| required_columns | PASS | All required columns present |
| pk_uniqueness | PASS | PK is unique |
| date_continuity | PASS | Date sequence is continuous |
| date_range | PASS | Range: 2024-01-01 00:00:00 to 2024-12-31 00:00:00 |

---

## dim_airline [PASS]

3/3 checks passed

| Check | Status | Message |
|-------|--------|---------|
| required_columns | PASS | All required columns present |
| pk_uniqueness | PASS | PK is unique |
| carrier_code_uniqueness | PASS | Carrier codes are unique |

---

## dim_airport [PASS]

4/4 checks passed

| Check | Status | Message |
|-------|--------|---------|
| required_columns | PASS | All required columns present |
| pk_uniqueness | PASS | PK is unique |
| airport_code_uniqueness | PASS | Airport codes are unique |
| airport_code_format | PASS | All airport codes are 3 chars |

---

## dim_route [PASS]

4/4 checks passed

| Check | Status | Message |
|-------|--------|---------|
| required_columns | PASS | All required columns present |
| pk_uniqueness | PASS | PK is unique |
| distance_validity | PASS | All distances valid |
| no_self_loops | PASS | No self-loop routes |

---

## fact_flights [PASS]

11/11 checks passed

| Check | Status | Message |
|-------|--------|---------|
| required_columns | PASS | All required columns present |
| pk_uniqueness | PASS | PK is unique |
| fk_date_id | PASS | FK date_id valid |
| fk_airline_id | PASS | FK airline_id valid |
| fk_origin_airport_id | PASS | FK origin_airport_id valid |
| fk_dest_airport_id | PASS | FK dest_airport_id valid |
| fk_route_id | PASS | FK route_id valid |
| no_negative_distance | PASS | No negative distances |
| delay_reasonableness | PASS | All delays reasonable |
| cancellation_consistency | PASS | Cancelled flights have zero delay |
| is_delayed_consistency | PASS | is_delayed flag consistent with arr_delay_min |

---

## fact_revenue [PASS]

7/7 checks passed

| Check | Status | Message |
|-------|--------|---------|
| required_columns | PASS | All required columns present |
| pk_uniqueness | PASS | PK is unique |
| fk_date_id | PASS | FK date_id valid |
| fk_airline_id | PASS | FK airline_id valid |
| fk_route_id | PASS | FK route_id valid |
| non_negative_revenue | PASS | All revenue non-negative |
| profit_margin_range | PASS | Profit margins in valid range |

---
