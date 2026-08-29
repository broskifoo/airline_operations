"""
Data Cleaning Module
Implements all cleaning rules for the airline operations dataset.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Any
from .config import (
    MAX_DELAY_MIN, MAX_DISTANCE_MILES, MIN_DISTANCE_MILES,
    CARRIER_NAMES, CANCELLATION_CODES,
    DELAY_CATEGORIES, DEP_PERIODS, DISTANCE_CATEGORIES, SEASON_MAP
)


def hhmm_to_minutes(hhmm_series: pd.Series) -> pd.Series:
    """Convert hhmm format to minutes since midnight.
    
    Handles: 1324 -> 804, 8 -> 8, 2400 -> 0, NaN -> NaN
    """
    def convert(val):
        if pd.isna(val):
            return np.nan
        val = int(val)
        if val == 2400:
            return 0
        hours = val // 100
        minutes = val % 100
        return hours * 60 + minutes
    
    return hhmm_series.apply(convert)


def categorize_delay(delay_min: float) -> str:
    """Categorize arrival delay into buckets."""
    if pd.isna(delay_min):
        return "Unknown"
    if delay_min < 15:
        return "On-Time"
    elif delay_min < 45:
        return "Minor (15-45)"
    elif delay_min < 90:
        return "Moderate (45-90)"
    else:
        return "Severe (90+)"


def get_departure_period(hour: int) -> str:
    """Map departure hour to period."""
    if pd.isna(hour):
        return "Unknown"
    hour = int(hour)
    if 5 <= hour <= 7:
        return "Early Morning"
    elif 8 <= hour <= 11:
        return "Morning"
    elif 12 <= hour <= 16:
        return "Afternoon"
    elif 17 <= hour <= 20:
        return "Evening"
    else:
        return "Night"


def get_distance_category(distance: float) -> str:
    """Categorize flight distance."""
    if pd.isna(distance):
        return "Unknown"
    if distance < 500:
        return "Short Haul"
    elif distance < 1500:
        return "Medium Haul"
    elif distance < 3000:
        return "Long Haul"
    else:
        return "Ultra Long Haul"


def get_primary_delay_cause(row: pd.Series) -> str:
    """Determine primary delay cause from the 5 cause columns."""
    causes = {
        "Carrier": row.get("carrier_delay_min", 0),
        "Weather": row.get("weather_delay_min", 0),
        "NAS": row.get("nas_delay_min", 0),
        "Security": row.get("security_delay_min", 0),
        "Late Aircraft": row.get("late_aircraft_delay_min", 0),
    }
    # Only consider if flight was delayed
    if row.get("arr_delay_min", 0) < 15:
        return "On-Time"
    max_cause = max(causes, key=causes.get)
    if causes[max_cause] == 0:
        return "Unknown"
    return max_cause


def clean_flights(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Main cleaning function for flights data.
    Returns cleaned DataFrame and cleaning report.
    """
    report = {
        "initial_rows": len(df),
        "initial_columns": len(df.columns),
        "steps": [],
    }
    
    df = df.copy()
    
    # 1. Ensure flight_date is datetime
    if "flight_date" in df.columns:
        df["flight_date"] = pd.to_datetime(df["flight_date"], errors="coerce")
        invalid_dates = df["flight_date"].isna().sum()
        if invalid_dates > 0:
            df = df.dropna(subset=["flight_date"])
            report["steps"].append(f"Dropped {invalid_dates} rows with invalid flight_date")
    
    # 2. Convert time columns from hhmm to minutes
    time_cols = ["sched_dep_time", "actual_dep_time", "wheels_off_time", 
                 "wheels_on_time", "sched_arr_time", "actual_arr_time"]
    for col in time_cols:
        if col in df.columns:
            df[col + "_min"] = hhmm_to_minutes(df[col])
    report["steps"].append("Converted hhmm time columns to minutes since midnight")
    
    # 3. Handle cancelled flights - set delays to 0
    cancelled_mask = df["cancelled_flag"] == 1
    delay_cols = ["dep_delay_min", "arr_delay_min", "taxi_out_min", "taxi_in_min",
                  "air_time_min", "actual_elapsed_min", "wheels_off_time_min", 
                  "wheels_on_time_min", "actual_dep_time_min", "actual_arr_time_min"]
    for col in delay_cols:
        if col in df.columns:
            df.loc[cancelled_mask, col] = 0
    report["steps"].append(f"Set delay/time columns to 0 for {cancelled_mask.sum()} cancelled flights")
    
    # 4. Validate distance
    if "distance_miles" in df.columns:
        invalid_dist = (df["distance_miles"] <= MIN_DISTANCE_MILES) | (df["distance_miles"] > MAX_DISTANCE_MILES)
        invalid_count = invalid_dist.sum()
        if invalid_count > 0:
            df = df[~invalid_dist]
            report["steps"].append(f"Dropped {invalid_count} rows with invalid distance (<={MIN_DISTANCE_MILES} or >{MAX_DISTANCE_MILES})")
    
    # 5. Cap extreme delays
    delay_cap_cols = ["dep_delay_min", "arr_delay_min", "carrier_delay_min", 
                      "weather_delay_min", "nas_delay_min", "security_delay_min", 
                      "late_aircraft_delay_min"]
    for col in delay_cap_cols:
        if col in df.columns:
            extreme = df[col] > MAX_DELAY_MIN
            extreme_count = extreme.sum()
            if extreme_count > 0:
                df.loc[extreme, col] = MAX_DELAY_MIN
                df.loc[extreme, col + "_capped"] = True
                report["steps"].append(f"Capped {extreme_count} extreme values in {col} at {MAX_DELAY_MIN} minutes")
    
    # 6. Remove duplicates on flight key
    flight_key = ["flight_date", "carrier_code", "flight_number", "origin_airport", "dest_airport"]
    if all(c in df.columns for c in flight_key):
        dup_mask = df.duplicated(subset=flight_key, keep="first")
        dup_count = dup_mask.sum()
        if dup_count > 0:
            df = df[~dup_mask]
            report["steps"].append(f"Removed {dup_count} duplicate flight keys (kept first)")
    
    # 7. Validate airport codes (3-char IATA)
    airport_cols = ["origin_airport", "dest_airport"]
    for col in airport_cols:
        if col in df.columns:
            invalid = df[col].astype(str).str.len() != 3
            invalid_count = invalid.sum()
            if invalid_count > 0:
                # Don't drop, just flag - we'll handle in dimension build
                df[col + "_valid"] = ~invalid
                report["steps"].append(f"Flagged {invalid_count} potentially invalid {col} codes")
    
    # 8. Validate carrier codes
    if "carrier_code" in df.columns:
        unknown_carriers = ~df["carrier_code"].isin(CARRIER_NAMES.keys())
        unknown_count = unknown_carriers.sum()
        if unknown_count > 0:
            df.loc[unknown_carriers, "carrier_code_valid"] = False
            report["steps"].append(f"Flagged {unknown_count} unknown carrier codes")
    
    # 9. Map cancellation codes
    if "cancellation_reason" in df.columns:
        df["cancellation_category"] = df["cancellation_reason"].map(CANCELLATION_CODES)
        df["cancellation_category"] = df["cancellation_category"].fillna("Unknown/Not Cancelled")
    
    # 9. Create derived analytical columns
    df = add_analytical_features(df)
    report["steps"].append("Added analytical features (delay category, departure period, etc.)")
    
    report["final_rows"] = len(df)
    report["final_columns"] = len(df.columns)
    report["rows_removed"] = report["initial_rows"] - report["final_rows"]
    
    return df, report


def add_analytical_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add all analytical features to the cleaned flights DataFrame."""
    df = df.copy()
    
    # Delay category
    if "arr_delay_min" in df.columns:
        df["delay_category"] = df["arr_delay_min"].apply(categorize_delay)
        df["is_delayed"] = (df["arr_delay_min"] >= 15).astype(int)
    
    # Departure hour and period
    if "sched_dep_time_min" in df.columns:
        df["dep_hour"] = (df["sched_dep_time_min"] // 60).astype("Int64")
        df["dep_period"] = df["dep_hour"].apply(get_departure_period)
    
    # Day of week, weekend, month, quarter, season
    if "flight_date" in df.columns:
        df["day_of_week_name"] = df["flight_date"].dt.day_name()
        df["is_weekend"] = df["flight_date"].dt.dayofweek.isin([5, 6]).astype(int)
        df["month_name"] = df["flight_date"].dt.month_name()
        df["quarter"] = df["flight_date"].dt.quarter
        df["season"] = df["flight_date"].dt.month.map(SEASON_MAP)
    
    # Distance category
    if "distance_miles" in df.columns:
        df["distance_category"] = df["distance_miles"].apply(get_distance_category)
    
    # Primary delay cause
    df["primary_delay_cause"] = df.apply(get_primary_delay_cause, axis=1)
    
    # Route identifier
    if "origin_airport" in df.columns and "dest_airport" in df.columns:
        df["route"] = df["origin_airport"] + "-" + df["dest_airport"]
    
    # Cancellation flag (already exists as cancelled_flag)
    df["cancellation_flag"] = df["cancelled_flag"].astype(int)
    df["diversion_flag"] = df["diverted_flag"].astype(int)
    
    return df


def clean_db1b_market(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Clean DB1B Market data."""
    report = {"initial_rows": len(df), "steps": []}
    df = df.copy()
    
    # Drop unnamed columns
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # Filter US domestic only
    if "OriginCountry" in df.columns and "DestCountry" in df.columns:
        us_mask = (df["OriginCountry"] == "US") & (df["DestCountry"] == "US")
        non_us = (~us_mask).sum()
        if non_us > 0:
            df = df[us_mask]
            report["steps"].append(f"Filtered out {non_us} non-US domestic itineraries")
    
    # Remove bulk fares
    if "BulkFare" in df.columns:
        bulk = (df["BulkFare"] == 1).sum()
        df = df[df["BulkFare"] == 0]
        report["steps"].append(f"Removed {bulk} bulk fare itineraries")
    
    # Validate fare range (per Borenstein methodology)
    if "MktFare" in df.columns:
        fare_outliers = (df["MktFare"] < 20) | (df["MktFare"] > 9998)
        outlier_count = fare_outliers.sum()
        if outlier_count > 0:
            df = df[~fare_outliers]
            report["steps"].append(f"Removed {outlier_count} fares outside [$20, $9998] range")
    
    # Remove first class fares (per academic practice)
    # Note: DB1B doesn't have clear cabin class in Market table
    # This is done at Coupon level
    
    report["final_rows"] = len(df)
    report["rows_removed"] = report["initial_rows"] - report["final_rows"]
    
    return df, report


def clean_db1b_coupon(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Clean DB1B Coupon data."""
    report = {"initial_rows": len(df), "steps": []}
    df = df.copy()
    
    # Drop unnamed columns
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # Filter US domestic
    if "OriginCountry" in df.columns and "DestCountry" in df.columns:
        us_mask = (df["OriginCountry"] == "US") & (df["DestCountry"] == "US")
        non_us = (~us_mask).sum()
        if non_us > 0:
            df = df[us_mask]
            report["steps"].append(f"Filtered out {non_us} non-US domestic coupons")
    
    # Filter coupon types (A=standard, D=other)
    if "CouponType" in df.columns:
        df = df[df["CouponType"].isin(["A", "D"])]
    
    report["final_rows"] = len(df)
    report["rows_removed"] = report["initial_rows"] - report["final_rows"]
    
    return df, report


def generate_data_quality_report(cleaning_reports: Dict[str, Dict]) -> str:
    """Generate markdown data quality report from cleaning reports."""
    lines = [
        "# Data Quality Report",
        f"\n**Generated**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "\n---\n"
    ]
    
    for dataset, report in cleaning_reports.items():
        lines.extend([
            f"## {dataset}",
            f"\n- **Initial Rows**: {report.get('initial_rows', 'N/A'):,}",
            f"- **Final Rows**: {report.get('final_rows', 'N/A'):,}",
            f"- **Rows Removed**: {report.get('rows_removed', 'N/A'):,}",
            f"- **Initial Columns**: {report.get('initial_columns', 'N/A')}",
            f"- **Final Columns**: {report.get('final_columns', 'N/A')}",
            "\n### Cleaning Steps\n"
        ])
        for step in report.get("steps", []):
            lines.append(f"- {step}")
        lines.append("\n---\n")
    
    return "\n".join(lines)