#!/usr/bin/env python3
"""
Fix data integrity issues:
1. Rebuild dim_route from fact_flights (source of truth for routes)
2. Remap fact_flights route_ids to match new dim_route
3. Remap fact_revenue route_ids to match new dim_route
4. Fix flight_id duplicates (assign globally unique IDs)
"""
import pandas as pd
import numpy as np
import glob
import os
from pathlib import Path

PROCESSED_DIR = Path("data/processed")
FACT_FLIGHTS_DIR = PROCESSED_DIR / "fact_flights.parquet"
DIM_ROUTE_PATH = PROCESSED_DIR / "dim_route.parquet"
DIM_AIRPORT_PATH = PROCESSED_DIR / "dim_airport.parquet"
FACT_REVENUE_PATH = PROCESSED_DIR / "fact_revenue.parquet"

print("=" * 60)
print("FIXING DATA INTEGRITY ISSUES")
print("=" * 60)

# 1. Read dim_airport for code lookups
print("\n1. Loading dim_airport...")
dim_airport = pd.read_parquet(DIM_AIRPORT_PATH)
airport_id_to_code = dim_airport.set_index("airport_id")["airport_code"].to_dict()
airport_code_to_id = dim_airport.set_index("airport_code")["airport_id"].to_dict()
print(f"   dim_airport: {len(dim_airport)} airports")

# 2. Read fact_flights (all partitions) to get unique routes
print("\n2. Loading fact_flights to extract unique routes...")
parquet_files = sorted(glob.glob(str(FACT_FLIGHTS_DIR / "date_id=*/*.parquet")))
print(f"   Found {len(parquet_files)} partitions")

all_routes = []
total_rows = 0
for i, f in enumerate(parquet_files):
    df = pd.read_parquet(f, columns=["origin_airport_id", "dest_airport_id", "distance_miles", "route_id"])
    total_rows += len(df)
    routes = df[["origin_airport_id", "dest_airport_id", "distance_miles"]].drop_duplicates()
    all_routes.append(routes)
    if (i + 1) % 1000 == 0:
        print(f"   Processed {i+1}/{len(parquet_files)} partitions...")

fact_routes = pd.concat(all_routes, ignore_index=True).drop_duplicates()
print(f"   Total fact_flights rows: {total_rows:,}")
print(f"   Unique routes in fact_flights: {len(fact_routes)}")

# 3. Build new dim_route from fact_flights routes
print("\n3. Building new dim_route from fact_flights routes...")
dim_route_new = fact_routes.groupby(["origin_airport_id", "dest_airport_id"])["distance_miles"].median().reset_index()
dim_route_new["route_id"] = range(1, len(dim_route_new) + 1)

# Add airport codes for readability
dim_route_new = dim_route_new.merge(
    dim_airport[["airport_id", "airport_code"]].rename(columns={"airport_code": "origin_code"}),
    left_on="origin_airport_id", right_on="airport_id"
).drop(columns=["airport_id"])
dim_route_new = dim_route_new.merge(
    dim_airport[["airport_id", "airport_code"]].rename(columns={"airport_code": "dest_code"}),
    left_on="dest_airport_id", right_on="airport_id"
).drop(columns=["airport_id"])

dim_route_new["route_code"] = dim_route_new["origin_code"] + "-" + dim_route_new["dest_code"]

# Distance category
def dist_cat(d):
    if d < 500: return "Short Haul"
    elif d < 1500: return "Medium Haul"
    elif d < 3000: return "Long Haul"
    else: return "Ultra Long Haul"

dim_route_new["distance_category"] = dim_route_new["distance_miles"].apply(dist_cat)

# Reorder columns
dim_route_new = dim_route_new[["route_id", "origin_airport_id", "dest_airport_id", 
                                "origin_code", "dest_code", "route_code", 
                                "distance_miles", "distance_category"]]

print(f"   New dim_route: {len(dim_route_new)} routes")
print(f"   Route ID range: {dim_route_new['route_id'].min()} - {dim_route_new['route_id'].max()}")

# 4. Create mapping from (origin_id, dest_id) to new route_id
route_map = dim_route_new.set_index(["origin_airport_id", "dest_airport_id"])["route_id"].to_dict()

# 5. Update fact_flights route_ids
print("\n4. Updating fact_flights route_ids...")
for i, f in enumerate(parquet_files):
    df = pd.read_parquet(f)
    df["route_id_new"] = df.apply(
        lambda row: route_map.get((row["origin_airport_id"], row["dest_airport_id"])), axis=1
    )
    unmapped = df["route_id_new"].isna().sum()
    if unmapped > 0:
        print(f"   WARNING: Partition {i} has {unmapped} unmapped routes")
    df["route_id"] = df["route_id_new"].astype("int64")
    df = df.drop(columns=["route_id_new"])
    df.to_parquet(f, index=False)
    if (i + 1) % 1000 == 0:
        print(f"   Updated {i+1}/{len(parquet_files)} partitions...")

print(f"   Updated all {len(parquet_files)} partitions")

# 6. Fix flight_id - assign globally unique IDs
print("\n5. Fixing flight_id (assigning globally unique IDs)...")
flight_id_counter = 1
for i, f in enumerate(parquet_files):
    df = pd.read_parquet(f)
    n = len(df)
    df["flight_id"] = range(flight_id_counter, flight_id_counter + n)
    flight_id_counter += n
    df.to_parquet(f, index=False)
    if (i + 1) % 1000 == 0:
        print(f"   Fixed flight_id for {i+1}/{len(parquet_files)} partitions...")

print(f"   Assigned flight_id 1 to {flight_id_counter - 1:,}")

# 7. Save new dim_route
print("\n6. Saving new dim_route...")
dim_route_new.to_parquet(DIM_ROUTE_PATH, index=False)
print(f"   Saved {len(dim_route_new)} routes to {DIM_ROUTE_PATH}")

# 8. Rebuild fact_revenue with new dim_route
print("\n7. Rebuilding fact_revenue with new dim_route...")

from src.config import DB1B_MARKET_Q1, DB1B_COUPON_Q1, DEFAULT_CASM, DB1B_SAMPLE_RATE
from src.data_loader import load_db1b_market_chunked, load_db1b_coupon_chunked, load_t100_all_months
from src.feature_engineering import create_fact_revenue, add_route_profitability_classification

# Load DB1B Market
print("   Loading DB1B Market...")
market_chunks = list(load_db1b_market_chunked(chunksize=50000))
raw_market = pd.concat(market_chunks, ignore_index=True) if market_chunks else pd.DataFrame()

# Load DB1B Coupon
print("   Loading DB1B Coupon...")
coupon_chunks = list(load_db1b_coupon_chunked(chunksize=50000))
raw_coupon = pd.concat(coupon_chunks, ignore_index=True) if coupon_chunks else pd.DataFrame()

# Load T-100
print("   Loading T-100 Segment...")
from src.data_loader import find_t100_files
t100_files = find_t100_files()
if t100_files:
    t100_segment = load_t100_all_months()
else:
    t100_segment = pd.DataFrame()

# Load dimensions
dim_date = pd.read_parquet(PROCESSED_DIR / "dim_date.parquet")
dim_airline = pd.read_parquet(PROCESSED_DIR / "dim_airline.parquet")

# Rebuild fact_revenue
print("   Creating fact_revenue...")
fact_revenue_new = create_fact_revenue(
    raw_market, raw_coupon, t100_segment,
    dim_date, dim_airline, dim_route_new,
    casm=DEFAULT_CASM
)

if not fact_revenue_new.empty:
    fact_revenue_new = add_route_profitability_classification(fact_revenue_new)
    fact_revenue_new.to_parquet(FACT_REVENUE_PATH, index=False)
    print(f"   Rebuilt fact_revenue: {len(fact_revenue_new)} rows")
else:
    print("   WARNING: fact_revenue is empty!")

# 9. Verify fixes
print("\n8. Verifying fixes...")

# Check fact_flights
fact_flights = pd.read_parquet(FACT_FLIGHTS_DIR)
print(f"   fact_flights rows: {len(fact_flights):,}")
print(f"   Unique flight_ids: {fact_flights['flight_id'].nunique():,}")
print(f"   Duplicate flight_ids: {fact_flights['flight_id'].duplicated().sum()}")

dim_route_check = pd.read_parquet(DIM_ROUTE_PATH)
print(f"   dim_route rows: {len(dim_route_check)}")

fact_routes_set = set(fact_flights["route_id"].dropna().unique())
dim_routes_set = set(dim_route_check["route_id"].unique())
orphaned = fact_routes_set - dim_routes_set
print(f"   Orphaned route_ids in fact_flights: {len(orphaned)}")

# Check fact_revenue
fact_rev_check = pd.read_parquet(FACT_REVENUE_PATH)
print(f"   fact_revenue rows: {len(fact_rev_check)}")
rev_routes_set = set(fact_rev_check["route_id"].dropna().unique())
rev_orphaned = rev_routes_set - dim_routes_set
print(f"   Orphaned route_ids in fact_revenue: {len(rev_orphaned)}")

print("\n" + "=" * 60)
print("FIX COMPLETE")
print("=" * 60)