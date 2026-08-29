# Data Profile Report: Kaggle Flight Delay Dataset 2024

**Generated**: 2026-08-21 16:59:51
**Source**: flight_data_2024_sample.csv (sample) + flight_data_2024.csv (full)

---

## Sample Dataset (10,000 rows)

**Rows**: 10,000 | **Columns**: 35 | **Memory**: 6.6 MB
**Duplicate Rows**: 0
**Date Range**: 2024-01-01 00:00:00 to 2024-12-31 00:00:00

### Column Summary

| Column | Type | Non-Null | Null % | Unique | Min | Max | Mean | Std |
|--------|------|----------|--------|--------|-----|-----|------|-----|
| year | int64 | 10,000 | 0.0% | 1 | 2024.00 | 2024.00 | 2024.00 | 0.00 |
| month | int64 | 10,000 | 0.0% | 12 | 1.00 | 12.00 | 6.61 | 3.38 |
| day_of_month | int64 | 10,000 | 0.0% | 31 | 1.00 | 31.00 | 15.84 | 8.79 |
| day_of_week | int64 | 10,000 | 0.0% | 7 | 1.00 | 7.00 | 3.95 | 2.01 |
| fl_date | object | 10,000 | 0.0% | 366 | N/A | N/A | N/A | N/A |
| op_unique_carrier | object | 10,000 | 0.0% | 15 | N/A | N/A | N/A | N/A |
| op_carrier_fl_num | float64 | 10,000 | 0.0% | 4,593 | 1.00 | 8771.00 | 2529.76 | 1656.00 |
| origin | object | 10,000 | 0.0% | 284 | N/A | N/A | N/A | N/A |
| origin_city_name | object | 10,000 | 0.0% | 278 | N/A | N/A | N/A | N/A |
| origin_state_nm | object | 10,000 | 0.0% | 52 | N/A | N/A | N/A | N/A |
| dest | object | 10,000 | 0.0% | 287 | N/A | N/A | N/A | N/A |
| dest_city_name | object | 10,000 | 0.0% | 281 | N/A | N/A | N/A | N/A |
| dest_state_nm | object | 10,000 | 0.0% | 52 | N/A | N/A | N/A | N/A |
| crs_dep_time | int64 | 10,000 | 0.0% | 1,077 | 22.00 | 2359.00 | 1324.45 | 488.54 |
| dep_time | float64 | 9,884 | 1.2% | 1,204 | 1.00 | 2400.00 | 1330.16 | 504.95 |
| dep_delay | float64 | 9,884 | 1.2% | 312 | -22.00 | 2011.00 | 13.00 | 53.61 |
| taxi_out | float64 | 9,880 | 1.2% | 95 | 4.00 | 154.00 | 17.88 | 9.77 |
| wheels_off | float64 | 9,880 | 1.2% | 1,203 | 1.00 | 2400.00 | 1353.56 | 507.45 |
| wheels_on | float64 | 9,873 | 1.3% | 1,258 | 1.00 | 2400.00 | 1460.50 | 536.91 |
| taxi_in | float64 | 9,873 | 1.3% | 73 | 1.00 | 140.00 | 8.41 | 7.07 |
| crs_arr_time | int64 | 10,000 | 0.0% | 1,177 | 2.00 | 2359.00 | 1496.54 | 513.23 |
| arr_time | float64 | 9,873 | 1.3% | 1,256 | 1.00 | 2400.00 | 1468.10 | 540.10 |
| arr_delay | float64 | 9,836 | 1.6% | 333 | -78.00 | 2014.00 | 7.55 | 55.80 |
| cancelled | int64 | 10,000 | 0.0% | 2 | 0.00 | 1.00 | 0.01 | 0.11 |
| cancellation_code | object | 122 | 98.8% | 3 | N/A | N/A | N/A | N/A |
| diverted | int64 | 10,000 | 0.0% | 2 | 0.00 | 1.00 | 0.00 | 0.06 |
| crs_elapsed_time | float64 | 10,000 | 0.0% | 382 | 23.00 | 685.00 | 147.37 | 72.93 |
| actual_elapsed_time | float64 | 9,836 | 1.6% | 390 | 17.00 | 691.00 | 141.73 | 72.79 |
| air_time | float64 | 9,836 | 1.6% | 375 | 8.00 | 635.00 | 115.45 | 70.74 |
| distance | float64 | 10,000 | 0.0% | 1,275 | 31.00 | 5095.00 | 838.35 | 598.53 |
| carrier_delay | int64 | 10,000 | 0.0% | 182 | 0.00 | 2011.00 | 4.87 | 33.50 |
| weather_delay | int64 | 10,000 | 0.0% | 90 | 0.00 | 664.00 | 1.08 | 15.82 |
| nas_delay | int64 | 10,000 | 0.0% | 135 | 0.00 | 454.00 | 3.03 | 15.76 |
| security_delay | int64 | 10,000 | 0.0% | 7 | 0.00 | 22.00 | 0.01 | 0.38 |
| late_aircraft_delay | int64 | 10,000 | 0.0% | 208 | 0.00 | 995.00 | 6.14 | 29.63 |

### Missing Values Detail

| Column              | Null %   |
|:--------------------|:---------|
| cancellation_code   | 98.78%   |
| arr_delay           | 1.64%    |
| actual_elapsed_time | 1.64%    |
| air_time            | 1.64%    |
| wheels_on           | 1.27%    |
| taxi_in             | 1.27%    |
| arr_time            | 1.27%    |
| taxi_out            | 1.20%    |
| wheels_off          | 1.20%    |
| dep_time            | 1.16%    |
| dep_delay           | 1.16%    |
| year                | 0.00%    |
| month               | 0.00%    |
| day_of_month        | 0.00%    |
| day_of_week         | 0.00%    |
| fl_date             | 0.00%    |
| op_unique_carrier   | 0.00%    |
| op_carrier_fl_num   | 0.00%    |
| origin              | 0.00%    |
| origin_city_name    | 0.00%    |
| origin_state_nm     | 0.00%    |
| dest                | 0.00%    |
| dest_city_name      | 0.00%    |
| dest_state_nm       | 0.00%    |
| crs_dep_time        | 0.00%    |
| crs_arr_time        | 0.00%    |
| cancelled           | 0.00%    |
| diverted            | 0.00%    |
| crs_elapsed_time    | 0.00%    |
| distance            | 0.00%    |
| carrier_delay       | 0.00%    |
| weather_delay       | 0.00%    |
| nas_delay           | 0.00%    |
| security_delay      | 0.00%    |
| late_aircraft_delay | 0.00%    |

---

## Full Dataset (First 100,000 rows)

**Rows**: 100,000 | **Columns**: 35 | **Memory**: 66.0 MB
**Duplicate Rows**: 0
**Date Range**: 2024-01-01 00:00:00 to 2024-01-06 00:00:00

### Column Summary

| Column | Type | Non-Null | Null % | Unique | Min | Max | Mean | Std |
|--------|------|----------|--------|--------|-----|-----|------|-----|
| year | int64 | 100,000 | 0.0% | 1 | 2024.00 | 2024.00 | 2024.00 | 0.00 |
| month | int64 | 100,000 | 0.0% | 1 | 1.00 | 1.00 | 1.00 | 0.00 |
| day_of_month | int64 | 100,000 | 0.0% | 6 | 1.00 | 6.00 | 3.28 | 1.59 |
| day_of_week | int64 | 100,000 | 0.0% | 6 | 1.00 | 6.00 | 3.28 | 1.59 |
| fl_date | object | 100,000 | 0.0% | 6 | N/A | N/A | N/A | N/A |
| op_unique_carrier | object | 100,000 | 0.0% | 15 | N/A | N/A | N/A | N/A |
| op_carrier_fl_num | float64 | 100,000 | 0.0% | 5,568 | 1.00 | 8811.00 | 2225.40 | 1529.65 |
| origin | object | 100,000 | 0.0% | 333 | N/A | N/A | N/A | N/A |
| origin_city_name | object | 100,000 | 0.0% | 327 | N/A | N/A | N/A | N/A |
| origin_state_nm | object | 100,000 | 0.0% | 52 | N/A | N/A | N/A | N/A |
| dest | object | 100,000 | 0.0% | 333 | N/A | N/A | N/A | N/A |
| dest_city_name | object | 100,000 | 0.0% | 327 | N/A | N/A | N/A | N/A |
| dest_state_nm | object | 100,000 | 0.0% | 52 | N/A | N/A | N/A | N/A |
| crs_dep_time | int64 | 100,000 | 0.0% | 1,195 | 8.00 | 2359.00 | 1331.01 | 499.16 |
| dep_time | float64 | 99,665 | 0.3% | 1,335 | 1.00 | 2400.00 | 1331.39 | 510.14 |
| dep_delay | float64 | 99,665 | 0.3% | 556 | -38.00 | 1675.00 | 7.86 | 43.73 |
| taxi_out | float64 | 99,655 | 0.3% | 114 | 1.00 | 163.00 | 18.03 | 9.19 |
| wheels_off | float64 | 99,655 | 0.3% | 1,341 | 1.00 | 2400.00 | 1353.32 | 511.42 |
| wheels_on | float64 | 99,634 | 0.4% | 1,429 | 1.00 | 2400.00 | 1466.52 | 538.43 |
| taxi_in | float64 | 99,634 | 0.4% | 95 | 1.00 | 143.00 | 8.05 | 6.25 |
| crs_arr_time | int64 | 100,000 | 0.0% | 1,310 | 1.00 | 2359.00 | 1492.52 | 529.48 |
| arr_time | float64 | 99,634 | 0.4% | 1,425 | 1.00 | 2400.00 | 1469.55 | 543.78 |
| arr_delay | float64 | 99,530 | 0.5% | 579 | -80.00 | 1676.00 | 0.46 | 45.70 |
| cancelled | int64 | 100,000 | 0.0% | 2 | 0.00 | 1.00 | 0.00 | 0.06 |
| cancellation_code | object | 351 | 99.6% | 3 | N/A | N/A | N/A | N/A |
| diverted | int64 | 100,000 | 0.0% | 2 | 0.00 | 1.00 | 0.00 | 0.03 |
| crs_elapsed_time | float64 | 100,000 | 0.0% | 422 | 26.00 | 690.00 | 153.00 | 74.85 |
| actual_elapsed_time | float64 | 99,530 | 0.5% | 526 | 17.00 | 685.00 | 145.49 | 73.48 |
| air_time | float64 | 99,530 | 0.5% | 509 | 8.00 | 647.00 | 119.41 | 71.58 |
| distance | float64 | 100,000 | 0.0% | 1,451 | 31.00 | 5095.00 | 869.27 | 605.91 |
| carrier_delay | int64 | 100,000 | 0.0% | 380 | 0.00 | 1647.00 | 3.73 | 28.14 |
| weather_delay | int64 | 100,000 | 0.0% | 172 | 0.00 | 1069.00 | 0.47 | 14.07 |
| nas_delay | int64 | 100,000 | 0.0% | 155 | 0.00 | 1134.00 | 1.61 | 9.38 |
| security_delay | int64 | 100,000 | 0.0% | 53 | 0.00 | 141.00 | 0.04 | 1.17 |
| late_aircraft_delay | int64 | 100,000 | 0.0% | 337 | 0.00 | 1175.00 | 3.63 | 23.00 |

### Missing Values Detail

| Column              | Null %   |
|:--------------------|:---------|
| cancellation_code   | 99.65%   |
| arr_delay           | 0.47%    |
| actual_elapsed_time | 0.47%    |
| air_time            | 0.47%    |
| wheels_on           | 0.37%    |
| taxi_in             | 0.37%    |
| arr_time            | 0.37%    |
| taxi_out            | 0.34%    |
| wheels_off          | 0.34%    |
| dep_time            | 0.34%    |
| dep_delay           | 0.34%    |
| year                | 0.00%    |
| month               | 0.00%    |
| day_of_month        | 0.00%    |
| day_of_week         | 0.00%    |
| fl_date             | 0.00%    |
| op_unique_carrier   | 0.00%    |
| op_carrier_fl_num   | 0.00%    |
| origin              | 0.00%    |
| origin_city_name    | 0.00%    |
| origin_state_nm     | 0.00%    |
| dest                | 0.00%    |
| dest_city_name      | 0.00%    |
| dest_state_nm       | 0.00%    |
| crs_dep_time        | 0.00%    |
| crs_arr_time        | 0.00%    |
| cancelled           | 0.00%    |
| diverted            | 0.00%    |
| crs_elapsed_time    | 0.00%    |
| distance            | 0.00%    |
| carrier_delay       | 0.00%    |
| weather_delay       | 0.00%    |
| nas_delay           | 0.00%    |
| security_delay      | 0.00%    |
| late_aircraft_delay | 0.00%    |

---

## Data Dictionary (from Kaggle)

| Column | Description |
|--------|-------------|
| year | Int64 |
| month | Int64 |
| day_of_month | Int64 |
| day_of_week | Int64 |
| fl_date | datetime64[ns] |
| op_unique_carrier | object |
| op_carrier_fl_num | float64 |
| origin | object |
| origin_city_name | object |
| origin_state_nm | object |
| dest | object |
| dest_city_name | object |
| dest_state_nm | object |
| crs_dep_time | Int64 |
| dep_time | float64 |
| dep_delay | float64 |
| taxi_out | float64 |
| wheels_off | float64 |
| wheels_on | float64 |
| taxi_in | float64 |
| crs_arr_time | Int64 |
| arr_time | float64 |
| arr_delay | float64 |
| cancelled | int64 |
| cancellation_code | object |
| diverted | int64 |
| crs_elapsed_time | float64 |
| actual_elapsed_time | float64 |
| air_time | float64 |
| distance | float64 |
| carrier_delay | int64 |
| weather_delay | int64 |
| nas_delay | int64 |
| security_delay | int64 |
| late_aircraft_delay | int64 |