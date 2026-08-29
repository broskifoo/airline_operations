"""
Validation Module
Automated data quality checks for the analytical model.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any
from .config import MAX_DELAY_MIN, MAX_DISTANCE_MILES, MIN_DISTANCE_MILES


def validate_dim_date(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate DIM_DATE table."""
    results = {"table": "dim_date", "checks": []}
    
    # Check required columns
    required = ["date_id", "date", "year", "month", "day", "quarter"]
    missing = [c for c in required if c not in df.columns]
    results["checks"].append({
        "name": "required_columns", "passed": len(missing) == 0,
        "message": f"Missing: {missing}" if missing else "All required columns present"
    })
    
    # Check PK uniqueness
    dup = df["date_id"].duplicated().sum()
    results["checks"].append({
        "name": "pk_uniqueness", "passed": dup == 0,
        "message": f"{dup} duplicate date_ids" if dup else "PK is unique"
    })
    
    # Check date continuity
    df_sorted = df.sort_values("date")
    gaps = (df_sorted["date"].diff().dt.days > 1).sum()
    results["checks"].append({
        "name": "date_continuity", "passed": gaps == 0,
        "message": f"{gaps} gaps in date sequence" if gaps else "Date sequence is continuous"
    })
    
    # Check date range
    results["checks"].append({
        "name": "date_range", "passed": True,
        "message": f"Range: {df['date'].min()} to {df['date'].max()}"
    })
    
    return results


def validate_dim_airline(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate DIM_AIRLINE table."""
    results = {"table": "dim_airline", "checks": []}
    
    required = ["airline_id", "carrier_code", "airline_name"]
    missing = [c for c in required if c not in df.columns]
    results["checks"].append({
        "name": "required_columns", "passed": len(missing) == 0,
        "message": f"Missing: {missing}" if missing else "All required columns present"
    })
    
    dup = df["airline_id"].duplicated().sum()
    results["checks"].append({
        "name": "pk_uniqueness", "passed": dup == 0,
        "message": f"{dup} duplicate airline_ids" if dup else "PK is unique"
    })
    
    dup_code = df["carrier_code"].duplicated().sum()
    results["checks"].append({
        "name": "carrier_code_uniqueness", "passed": dup_code == 0,
        "message": f"{dup_code} duplicate carrier_codes" if dup_code else "Carrier codes are unique"
    })
    
    return results


def validate_dim_airport(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate DIM_AIRPORT table."""
    results = {"table": "dim_airport", "checks": []}
    
    required = ["airport_id", "airport_code", "city", "state"]
    missing = [c for c in required if c not in df.columns]
    results["checks"].append({
        "name": "required_columns", "passed": len(missing) == 0,
        "message": f"Missing: {missing}" if missing else "All required columns present"
    })
    
    dup = df["airport_id"].duplicated().sum()
    results["checks"].append({
        "name": "pk_uniqueness", "passed": dup == 0,
        "message": f"{dup} duplicate airport_ids" if dup else "PK is unique"
    })
    
    dup_code = df["airport_code"].duplicated().sum()
    results["checks"].append({
        "name": "airport_code_uniqueness", "passed": dup_code == 0,
        "message": f"{dup_code} duplicate airport_codes" if dup_code else "Airport codes are unique"
    })
    
    # Validate airport code format (3 chars)
    if "airport_code" in df.columns:
        invalid = df["airport_code"].astype(str).str.len() != 3
        invalid_count = invalid.sum()
        results["checks"].append({
            "name": "airport_code_format", "passed": invalid_count == 0,
            "message": f"{invalid_count} airport codes not 3 chars" if invalid_count else "All airport codes are 3 chars"
        })
    
    return results


def validate_dim_route(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate DIM_ROUTE table."""
    results = {"table": "dim_route", "checks": []}
    
    required = ["route_id", "origin_airport_id", "dest_airport_id", "distance_miles"]
    missing = [c for c in required if c not in df.columns]
    results["checks"].append({
        "name": "required_columns", "passed": len(missing) == 0,
        "message": f"Missing: {missing}" if missing else "All required columns present"
    })
    
    dup = df["route_id"].duplicated().sum()
    results["checks"].append({
        "name": "pk_uniqueness", "passed": dup == 0,
        "message": f"{dup} duplicate route_ids" if dup else "PK is unique"
    })
    
    # Check distance validity
    if "distance_miles" in df.columns:
        invalid = (df["distance_miles"] < MIN_DISTANCE_MILES) | (df["distance_miles"] > MAX_DISTANCE_MILES)
        invalid_count = invalid.sum()
        results["checks"].append({
            "name": "distance_validity", "passed": invalid_count == 0,
            "message": f"{invalid_count} routes with invalid distance" if invalid_count else "All distances valid"
        })
    
    # Check no self-loops
    if "origin_airport_id" in df.columns and "dest_airport_id" in df.columns:
        self_loops = (df["origin_airport_id"] == df["dest_airport_id"]).sum()
        results["checks"].append({
            "name": "no_self_loops", "passed": self_loops == 0,
            "message": f"{self_loops} self-loop routes" if self_loops else "No self-loop routes"
        })
    
    return results


def validate_fact_flights(df: pd.DataFrame, 
                          dim_date: pd.DataFrame,
                          dim_airline: pd.DataFrame,
                          dim_airport: pd.DataFrame,
                          dim_route: pd.DataFrame) -> Dict[str, Any]:
    """Validate FACT_FLIGHTS table."""
    results = {"table": "fact_flights", "checks": []}
    
    required = ["flight_id", "date_id", "airline_id", "origin_airport_id", 
                "dest_airport_id", "route_id", "arr_delay_min", "cancelled_flag"]
    missing = [c for c in required if c not in df.columns]
    results["checks"].append({
        "name": "required_columns", "passed": len(missing) == 0,
        "message": f"Missing: {missing}" if missing else "All required columns present"
    })
    
    # PK uniqueness
    dup = df["flight_id"].duplicated().sum()
    results["checks"].append({
        "name": "pk_uniqueness", "passed": dup == 0,
        "message": f"{dup} duplicate flight_ids" if dup else "PK is unique"
    })
    
    # FK referential integrity
    fk_checks = [
        ("date_id", dim_date["date_id"], "dim_date"),
        ("airline_id", dim_airline["airline_id"], "dim_airline"),
        ("origin_airport_id", dim_airport["airport_id"], "dim_airport"),
        ("dest_airport_id", dim_airport["airport_id"], "dim_airport"),
        ("route_id", dim_route["route_id"], "dim_route"),
    ]
    
    for fk_col, pk_series, ref_table in fk_checks:
        if fk_col in df.columns:
            orphaned = (~df[fk_col].isin(pk_series)).sum()
            results["checks"].append({
                "name": f"fk_{fk_col}", "passed": orphaned == 0,
                "message": f"{orphaned} orphaned {fk_col} (not in {ref_table})" if orphaned else f"FK {fk_col} valid"
            })
    
    # No negative distances
    if "distance_miles" in df.columns:
        neg_dist = (df["distance_miles"] < 0).sum()
        results["checks"].append({
            "name": "no_negative_distance", "passed": neg_dist == 0,
            "message": f"{neg_dist} negative distances" if neg_dist else "No negative distances"
        })
    
    # Delay reasonableness
    if "arr_delay_min" in df.columns:
        extreme = (df["arr_delay_min"] > MAX_DELAY_MIN).sum()
        results["checks"].append({
            "name": "delay_reasonableness", "passed": extreme == 0,
            "message": f"{extreme} delays > {MAX_DELAY_MIN} min" if extreme else "All delays reasonable"
        })
    
    # Cancellation consistency: cancelled flights should have 0 delay
    if "cancelled_flag" in df.columns and "arr_delay_min" in df.columns:
        cancelled_with_delay = ((df["cancelled_flag"] == 1) & (df["arr_delay_min"] != 0)).sum()
        results["checks"].append({
            "name": "cancellation_consistency", "passed": cancelled_with_delay == 0,
            "message": f"{cancelled_with_delay} cancelled flights with non-zero delay" if cancelled_with_delay else "Cancelled flights have zero delay"
        })
    
    # is_delayed flag consistency
    if "is_delayed" in df.columns and "arr_delay_min" in df.columns:
        inconsistent = ((df["is_delayed"] == 1) & (df["arr_delay_min"] < 15)).sum()
        inconsistent += ((df["is_delayed"] == 0) & (df["arr_delay_min"] >= 15)).sum()
        results["checks"].append({
            "name": "is_delayed_consistency", "passed": inconsistent == 0,
            "message": f"{inconsistent} inconsistent is_delayed flags" if inconsistent else "is_delayed flag consistent with arr_delay_min"
        })
    
    # Percentage ranges
    pct_cols = [c for c in df.columns if "pct" in c.lower() or "margin" in c.lower()]
    for col in pct_cols:
        if col in df.columns:
            invalid = ((df[col] < 0) | (df[col] > 1)).sum()
            results["checks"].append({
                "name": f"pct_range_{col}", "passed": invalid == 0,
                "message": f"{invalid} values outside [0,1] in {col}" if invalid else f"{col} in valid range"
            })
    
    return results


def validate_fact_revenue(df: pd.DataFrame,
                          dim_date: pd.DataFrame,
                          dim_airline: pd.DataFrame,
                          dim_route: pd.DataFrame) -> Dict[str, Any]:
    """Validate FACT_REVENUE table."""
    results = {"table": "fact_revenue", "checks": []}
    
    if df.empty:
        results["checks"].append({
            "name": "non_empty", "passed": False,
            "message": "FACT_REVENUE is empty"
        })
        return results
    
    required = ["revenue_id", "date_id", "airline_id", "route_id", 
                "estimated_ticket_revenue", "estimated_operating_cost"]
    missing = [c for c in required if c not in df.columns]
    results["checks"].append({
        "name": "required_columns", "passed": len(missing) == 0,
        "message": f"Missing: {missing}" if missing else "All required columns present"
    })
    
    dup = df["revenue_id"].duplicated().sum()
    results["checks"].append({
        "name": "pk_uniqueness", "passed": dup == 0,
        "message": f"{dup} duplicate revenue_ids" if dup else "PK is unique"
    })
    
    # FK checks
    fk_checks = [
        ("date_id", dim_date["date_id"], "dim_date"),
        ("airline_id", dim_airline["airline_id"], "dim_airline"),
        ("route_id", dim_route["route_id"], "dim_route"),
    ]
    for fk_col, pk_series, ref_table in fk_checks:
        if fk_col in df.columns:
            orphaned = (~df[fk_col].isin(pk_series)).sum()
            results["checks"].append({
                "name": f"fk_{fk_col}", "passed": orphaned == 0,
                "message": f"{orphaned} orphaned {fk_col}" if orphaned else f"FK {fk_col} valid"
            })
    
    # Non-negative revenue
    if "estimated_ticket_revenue" in df.columns:
        neg = (df["estimated_ticket_revenue"] < 0).sum()
        results["checks"].append({
            "name": "non_negative_revenue", "passed": neg == 0,
            "message": f"{neg} negative revenue values" if neg else "All revenue non-negative"
        })
    
    # Profit margin range
    if "profit_margin" in df.columns:
        invalid = ((df["profit_margin"] < -1) | (df["profit_margin"] > 1)).sum()
        results["checks"].append({
            "name": "profit_margin_range", "passed": invalid == 0,
            "message": f"{invalid} profit margins outside [-1, 1]" if invalid else "Profit margins in valid range"
        })
    
    return results


def run_all_validations(dim_date: pd.DataFrame,
                        dim_airline: pd.DataFrame,
                        dim_airport: pd.DataFrame,
                        dim_route: pd.DataFrame,
                        fact_flights: pd.DataFrame,
                        fact_revenue: pd.DataFrame) -> Dict[str, Any]:
    """Run all validation checks and return summary."""
    all_results = {}
    
    all_results["dim_date"] = validate_dim_date(dim_date)
    all_results["dim_airline"] = validate_dim_airline(dim_airline)
    all_results["dim_airport"] = validate_dim_airport(dim_airport)
    all_results["dim_route"] = validate_dim_route(dim_route)
    all_results["fact_flights"] = validate_fact_flights(fact_flights, dim_date, dim_airline, dim_airport, dim_route)
    all_results["fact_revenue"] = validate_fact_revenue(fact_revenue, dim_date, dim_airline, dim_route)
    
    # Summary
    total_checks = sum(len(r["checks"]) for r in all_results.values())
    passed_checks = sum(sum(c["passed"] for c in r["checks"]) for r in all_results.values())
    
    summary = {
        "total_checks": total_checks,
        "passed": passed_checks,
        "failed": total_checks - passed_checks,
        "pass_rate": passed_checks / total_checks if total_checks > 0 else 0,
        "details": all_results
    }
    
    return summary


def print_validation_summary(summary: Dict[str, Any]):
    """Print validation summary to console."""
    print(f"\n{'='*60}")
    print(f"VALIDATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total Checks: {summary['total_checks']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Pass Rate: {summary['pass_rate']:.1%}")
    print(f"{'='*60}\n")
    
    for table, result in summary["details"].items():
        table_passed = sum(c["passed"] for c in result["checks"])
        table_total = len(result["checks"])
        status = "PASS" if table_passed == table_total else "FAIL"
        print(f"  {table}: {table_passed}/{table_total} [{status}]")
        for check in result["checks"]:
            icon = "[OK]" if check["passed"] else "[FAIL]"
            print(f"    {icon} {check['name']}: {check['message']}")
        print()


def save_validation_report(summary: Dict[str, Any], output_path: Path):
    """Save validation report as markdown."""
    lines = [
        "# Data Validation Report",
        f"\n**Total Checks**: {summary['total_checks']} | **Passed**: {summary['passed']} | **Failed**: {summary['failed']} | **Pass Rate**: {summary['pass_rate']:.1%}",
        "\n---\n"
    ]
    
    for table, result in summary["details"].items():
        table_passed = sum(c["passed"] for c in result["checks"])
        table_total = len(result["checks"])
        status = "PASS" if table_passed == table_total else "FAIL"
        
        lines.append(f"## {table} [{status}]")
        lines.append(f"\n{table_passed}/{table_total} checks passed\n")
        
        lines.append("| Check | Status | Message |")
        lines.append("|-------|--------|---------|")
        
        for check in result["checks"]:
            status_icon = "PASS" if check["passed"] else "FAIL"
            lines.append(f"| {check['name']} | {status_icon} | {check['message']} |")
        
        lines.append("\n---\n")
    
    output_path.write_text("\n".join(lines))
    print(f"Validation report saved to {output_path}")