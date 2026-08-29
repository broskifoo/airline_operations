"""
Configuration module for Airline Operations & Revenue Analytics
Centralized paths, constants, and settings.
"""
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent

# Data Directories
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"
PROCESSED_OUTPUTS_DIR = OUTPUTS_DIR / "processed_data"

# Source Files
KAGGLE_2024_FULL = RAW_DATA_DIR / "flight_data_2024.csv"
KAGGLE_2024_SAMPLE = RAW_DATA_DIR / "flight_data_2024_sample.csv"
KAGGLE_DICT = RAW_DATA_DIR / "flight_data_2024_data_dictionary.csv"

# DB1B Market files (all 4 quarters)
DB1B_MARKET_Q1 = RAW_DATA_DIR / "DB1B_Market_2024_Q1" / "Origin_and_Destination_Survey_DB1BMarket_2024_1.csv"
DB1B_MARKET_Q2 = RAW_DATA_DIR / "DB1B_Market_2024_Q2" / "Origin_and_Destination_Survey_DB1BMarket_2024_2.csv"
DB1B_MARKET_Q3 = RAW_DATA_DIR / "DB1B_Market_2024_Q3" / "Origin_and_Destination_Survey_DB1BMarket_2024_3.csv"
DB1B_MARKET_Q4 = RAW_DATA_DIR / "DB1B_Market_2024_Q4" / "Origin_and_Destination_Survey_DB1BMarket_2024_4.csv"

# DB1B Coupon files (all 4 quarters)
DB1B_COUPON_Q1 = RAW_DATA_DIR / "DB1B_Coupon_2024_Q1" / "Origin_and_Destination_Survey_DB1BCoupon_2024_1.csv"
DB1B_COUPON_Q2 = RAW_DATA_DIR / "DB1B_Coupon_2024_Q2" / "Origin_and_Destination_Survey_DB1BCoupon_2024_2.csv"
DB1B_COUPON_Q3 = RAW_DATA_DIR / "DB1B_Coupon_2024_Q3" / "Origin_and_Destination_Survey_DB1BCoupon_2024_3.csv"
DB1B_COUPON_Q4 = RAW_DATA_DIR / "DB1B_Coupon_2024_Q4" / "Origin_and_Destination_Survey_DB1BCoupon_2024_4.csv"

# All DB1B files for easy iteration
DB1B_MARKET_ALL = [DB1B_MARKET_Q1, DB1B_MARKET_Q2, DB1B_MARKET_Q3, DB1B_MARKET_Q4]
DB1B_COUPON_ALL = [DB1B_COUPON_Q1, DB1B_COUPON_Q2, DB1B_COUPON_Q3, DB1B_COUPON_Q4]

# BTS Reference Files (to be downloaded)
BTS_AIRPORTS = RAW_DATA_DIR / "bts_master_coordinate.csv"
BTS_CARRIERS = RAW_DATA_DIR / "bts_carrier_lookup.csv"

# T-100 Segment Data (to be downloaded)
T100_SEGMENT_DIR = RAW_DATA_DIR
T100_SEGMENT_PATTERN = "T_T100D_SEGMENT_ALL_CARRIER_*.zip"

# Processed Output Files
DIM_DATE = PROCESSED_DATA_DIR / "dim_date.parquet"
DIM_AIRLINE = PROCESSED_DATA_DIR / "dim_airline.parquet"
DIM_AIRPORT = PROCESSED_DATA_DIR / "dim_airport.parquet"
DIM_ROUTE = PROCESSED_DATA_DIR / "dim_route.parquet"
FACT_FLIGHTS = PROCESSED_DATA_DIR / "fact_flights.parquet"
FACT_REVENUE = PROCESSED_DATA_DIR / "fact_revenue.parquet"

# Staging
STAGING_DIR = PROCESSED_DATA_DIR / "staging"

# Column Mappings
KAGGLE_COLUMN_RENAME = {
    "year": "year",
    "month": "month",
    "day_of_month": "day_of_month",
    "day_of_week": "day_of_week",
    "fl_date": "flight_date",
    "op_unique_carrier": "carrier_code",
    "op_carrier_fl_num": "flight_number",
    "origin": "origin_airport",
    "origin_city_name": "origin_city",
    "origin_state_nm": "origin_state",
    "dest": "dest_airport",
    "dest_city_name": "dest_city",
    "dest_state_nm": "dest_state",
    "crs_dep_time": "sched_dep_time",
    "dep_time": "actual_dep_time",
    "dep_delay": "dep_delay_min",
    "taxi_out": "taxi_out_min",
    "wheels_off": "wheels_off_time",
    "wheels_on": "wheels_on_time",
    "taxi_in": "taxi_in_min",
    "crs_arr_time": "sched_arr_time",
    "arr_time": "actual_arr_time",
    "arr_delay": "arr_delay_min",
    "cancelled": "cancelled_flag",
    "cancellation_code": "cancellation_reason",
    "diverted": "diverted_flag",
    "crs_elapsed_time": "sched_elapsed_min",
    "actual_elapsed_time": "actual_elapsed_min",
    "air_time": "air_time_min",
    "distance": "distance_miles",
    "carrier_delay": "carrier_delay_min",
    "weather_delay": "weather_delay_min",
    "nas_delay": "nas_delay_min",
    "security_delay": "security_delay_min",
    "late_aircraft_delay": "late_aircraft_delay_min",
}

# Carrier Code to Name Mapping (major carriers 2024)
CARRIER_NAMES = {
    "WN": "Southwest Airlines",
    "DL": "Delta Air Lines",
    "AA": "American Airlines",
    "UA": "United Airlines",
    "OO": "SkyWest Airlines",
    "NK": "Spirit Airlines",
    "MQ": "Envoy Air",
    "B6": "JetBlue Airways",
    "AS": "Alaska Airlines",
    "F9": "Frontier Airlines",
    "OH": "PSA Airlines",
    "YX": "Republic Airways",
    "EV": "ExpressJet Airlines",
    "9E": "Endeavor Air",
    "G4": "Allegiant Air",
    "HA": "Hawaiian Airlines",
}

# Delay Categories
DELAY_CATEGORIES = {
    "On-Time": (float("-inf"), 15),
    "Minor (15-45)": (15, 45),
    "Moderate (45-90)": (45, 90),
    "Severe (90+)": (90, float("inf")),
}

# Departure Periods
DEP_PERIODS = {
    "Early Morning": (5, 7),
    "Morning": (8, 11),
    "Afternoon": (12, 16),
    "Evening": (17, 20),
    "Night": (21, 4),  # wraps midnight
}

# Distance Categories
DISTANCE_CATEGORIES = {
    "Short Haul": (0, 500),
    "Medium Haul": (500, 1500),
    "Long Haul": (1500, 3000),
    "Ultra Long Haul": (3000, float("inf")),
}

# Cancellation Code Mapping
CANCELLATION_CODES = {
    "A": "Carrier",
    "B": "Weather",
    "C": "National Aviation System",
    "D": "Security",
}

# CASM Assumption (cents per ASM)
DEFAULT_CASM = 0.12  # $0.12 per Available Seat Mile

# DB1B Sample Rate
DB1B_SAMPLE_RATE = 10  # 10% sample, multiply by 10

# Validation Thresholds
MAX_DELAY_MIN = 1440  # 24 hours
MAX_DISTANCE_MILES = 6000
MIN_DISTANCE_MILES = 1

# Seasons
SEASON_MAP = {
    1: "Winter", 2: "Winter", 3: "Spring",
    4: "Spring", 5: "Spring", 6: "Summer",
    7: "Summer", 8: "Summer", 9: "Fall",
    10: "Fall", 11: "Fall", 12: "Winter",
}