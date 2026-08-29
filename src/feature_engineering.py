"""
Feature Engineering Module
Creates analytical features for both operational and revenue analysis.
"""
import pandas as pd
import numpy as np
import logging
from .config import DEFAULT_CASM, DB1B_SAMPLE_RATE

logger = logging.getLogger(__name__)


def create_dim_date(start_date: str = "2024-01-01", end_date: str = "2024-12-31") -> pd.DataFrame:
    """Create date dimension table."""
    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    df = pd.DataFrame({"date": dates})
    
    df["date_id"] = df["date"].dt.strftime("%Y%m%d").astype(int)
    df["year"] = df["date"].dt.year
    df["quarter"] = df["date"].dt.quarter
    df["month"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.month_name()
    df["week"] = df["date"].dt.isocalendar().week
    df["day"] = df["date"].dt.day
    df["day_name"] = df["date"].dt.day_name()
    df["day_of_week"] = df["date"].dt.dayofweek + 1  # 1=Monday
    df["is_weekend"] = df["date"].dt.dayofweek.isin([5, 6]).astype(int)
    df["is_holiday"] = 0  # Placeholder for US holidays
    
    # Season mapping
    season_map = {1: "Winter", 2: "Winter", 3: "Spring",
                  4: "Spring", 5: "Spring", 6: "Summer",
                  7: "Summer", 8: "Summer", 9: "Fall",
                  10: "Fall", 11: "Fall", 12: "Winter"}
    df["season"] = df["month"].map(season_map)
    
    # Time intelligence helpers
    df["year_month"] = df["date"].dt.strftime("%Y-%m")
    df["year_quarter"] = df["year"].astype(str) + "Q" + df["quarter"].astype(str)
    df["month_start"] = df["date"].dt.to_period("M").dt.to_timestamp()
    df["quarter_start"] = df["date"].dt.to_period("Q").dt.to_timestamp()
    df["year_start"] = df["date"].dt.to_period("Y").dt.to_timestamp()
    
    return df


def create_dim_airline(flight_df: pd.DataFrame, carrier_lookup: pd.DataFrame = None) -> pd.DataFrame:
    """Create airline dimension from flights data."""
    carriers = flight_df["carrier_code"].dropna().unique()
    df = pd.DataFrame({"carrier_code": sorted(carriers)})
    df["airline_id"] = range(1, len(df) + 1)
    
    # Add names from lookup or config
    from .config import CARRIER_NAMES
    df["airline_name"] = df["carrier_code"].map(CARRIER_NAMES).fillna("Unknown")
    
    return df[["airline_id", "carrier_code", "airline_name"]]


def create_dim_airport(flight_df: pd.DataFrame, master_coord: pd.DataFrame = None) -> pd.DataFrame:
    """Create airport dimension from flights data."""
    # Get unique airports from origin and dest
    origins = flight_df[["origin_airport", "origin_city", "origin_state"]].drop_duplicates()
    origins.columns = ["airport_code", "city", "state"]
    
    dests = flight_df[["dest_airport", "dest_city", "dest_state"]].drop_duplicates()
    dests.columns = ["airport_code", "city", "state"]
    
    airports = pd.concat([origins, dests]).drop_duplicates(subset=["airport_code"])
    airports = airports.sort_values("airport_code").reset_index(drop=True)
    airports["airport_id"] = range(1, len(airports) + 1)
    
    # Merge with master coordinate if available
    if master_coord is not None and not master_coord.empty:
        airports = airports.merge(
            master_coord[["iata_code", "airport_name", "latitude", "longitude"]],
            left_on="airport_code", right_on="iata_code", how="left"
        )
        airports.drop(columns=["iata_code"], inplace=True, errors="ignore")
    else:
        airports["airport_name"] = airports["city"] + ", " + airports["state"]
        airports["latitude"] = np.nan
        airports["longitude"] = np.nan
    
    return airports[["airport_id", "airport_code", "airport_name", "city", "state", "latitude", "longitude"]]


def create_dim_route(clean_flights: pd.DataFrame, dim_airport: pd.DataFrame) -> pd.DataFrame:
    """Create route dimension from clean flights data (using airport codes)."""
    # Get unique origin-dest pairs with distance
    routes = clean_flights[["origin_airport", "dest_airport", "distance_miles"]].drop_duplicates()
    
    # Aggregate distance (use median to avoid outliers)
    routes = routes.groupby(["origin_airport", "dest_airport"])["distance_miles"].median().reset_index()
    
    # Map airport codes to IDs
    airport_map = dim_airport.set_index("airport_code")["airport_id"].to_dict()
    routes["origin_airport_id"] = routes["origin_airport"].map(airport_map)
    routes["dest_airport_id"] = routes["dest_airport"].map(airport_map)
    
    # Drop any routes that couldn't be mapped
    routes = routes.dropna(subset=["origin_airport_id", "dest_airport_id"])
    routes["origin_airport_id"] = routes["origin_airport_id"].astype(int)
    routes["dest_airport_id"] = routes["dest_airport_id"].astype(int)
    
    routes["route_id"] = range(1, len(routes) + 1)
    
    # Distance category
    def dist_cat(d):
        if d < 500: return "Short Haul"
        elif d < 1500: return "Medium Haul"
        elif d < 3000: return "Long Haul"
        else: return "Ultra Long Haul"
    
    routes["distance_category"] = routes["distance_miles"].apply(dist_cat)
    
    # Add airport codes for readability
    routes = routes.merge(
        dim_airport[["airport_id", "airport_code"]].rename(columns={"airport_code": "origin_code"}),
        left_on="origin_airport_id", right_on="airport_id"
    ).drop(columns=["airport_id"])
    routes = routes.merge(
        dim_airport[["airport_id", "airport_code"]].rename(columns={"airport_code": "dest_code"}),
        left_on="dest_airport_id", right_on="airport_id"
    ).drop(columns=["airport_id"])
    
    routes["route_code"] = routes["origin_code"] + "-" + routes["dest_code"]
    
    return routes[["route_id", "origin_airport_id", "dest_airport_id", "origin_code", "dest_code", 
                   "route_code", "distance_miles", "distance_category"]]


def create_fact_flights(clean_flights: pd.DataFrame, 
                        dim_date: pd.DataFrame,
                        dim_airline: pd.DataFrame,
                        dim_airport: pd.DataFrame,
                        dim_route: pd.DataFrame) -> pd.DataFrame:
    """Create fact_flights table by joining cleaned flights with dimensions."""
    
    # Create lookup maps
    date_map = dim_date.set_index("date")["date_id"].to_dict()
    airline_map = dim_airline.set_index("carrier_code")["airline_id"].to_dict()
    airport_map = dim_airport.set_index("airport_code")["airport_id"].to_dict()
    route_map = dim_route.set_index("route_code")["route_id"].to_dict()
    
    df = clean_flights.copy()
    
    # Map surrogate keys
    df["date_id"] = df["flight_date"].map(date_map)
    df["airline_id"] = df["carrier_code"].map(airline_map)
    df["origin_airport_id"] = df["origin_airport"].map(airport_map)
    df["dest_airport_id"] = df["dest_airport"].map(airport_map)
    df["route_id"] = df["route"].map(route_map)
    
    # Check for unmapped keys
    unmapped = {
        "date_id": df["date_id"].isna().sum(),
        "airline_id": df["airline_id"].isna().sum(),
        "origin_airport_id": df["origin_airport_id"].isna().sum(),
        "dest_airport_id": df["dest_airport_id"].isna().sum(),
        "route_id": df["route_id"].isna().sum(),
    }
    print(f"Unmapped keys: {unmapped}")
    
    # Select and order fact columns
    fact_cols = [
        "date_id", "airline_id", "origin_airport_id", "dest_airport_id", "route_id",
        "sched_dep_time_min", "actual_dep_time_min", "sched_arr_time_min", "actual_arr_time_min",
        "dep_delay_min", "arr_delay_min",
        "taxi_out_min", "taxi_in_min", "air_time_min", "distance_miles",
        "cancelled_flag", "cancellation_category", "diverted_flag",
        "carrier_delay_min", "weather_delay_min", "nas_delay_min", 
        "security_delay_min", "late_aircraft_delay_min",
        "is_delayed", "delay_category", "dep_hour", "dep_period",
        "day_of_week_name", "is_weekend", "month_name", "quarter", "season",
        "distance_category", "primary_delay_cause", "cancellation_flag", "diversion_flag"
    ]
    
    # Only keep columns that exist
    fact_cols = [c for c in fact_cols if c in df.columns]
    
    fact = df[fact_cols].copy()
    fact["flight_id"] = range(1, len(fact) + 1)
    
    # Reorder with flight_id first
    cols = ["flight_id"] + [c for c in fact_cols if c != "flight_id"]
    fact = fact[cols]
    
    return fact


T100_COLUMN_MAP = {
    'UNIQUE_CARRIER': 'carrier_code',
    'CARRIER': 'carrier_iata',
    'UNIQUE_CARRIER_ENTITY': 'carrier_entity',
    'YEAR': 'year',
    'MONTH': 'month',
    'ORIGIN': 'origin_airport',
    'ORIGIN_AIRPORT': 'origin_airport',
    'DEST': 'dest_airport',
    'DESTINATION': 'dest_airport',
    'DEST_AIRPORT': 'dest_airport',
    'SERVICE_CLASS': 'service_class',
    'CLASS': 'service_class',  # T-100 uses CLASS
    'AIRCRAFT_TYPE': 'aircraft_type',
    'DEPARTURES_PERFORMED': 'departures_performed',
    'DEPARTURES_SCHEDULED': 'departures_scheduled',
    'AVAILABLE_SEATS': 'available_seats',
    'SEATS': 'available_seats',
    'PASSENGERS': 'passengers',
    'PASSENGERS_TRANSPORTED': 'passengers',
    'DISTANCE': 'distance_miles',
    'DISTANCE_MILES': 'distance_miles',
    'INTER_AIRPORT_DISTANCE': 'distance_miles',
    'AVAILABLE_CAPACITY': 'available_capacity',
    'FREIGHT': 'freight',
    'MAIL': 'mail',
    'RAMP_TO_RAMP_MINUTES': 'ramp_to_ramp_minutes',
    'RAMP_TO_RAMP': 'ramp_to_ramp_minutes',  # T-100 uses RAMP_TO_RAMP
    'AIRBORNE_MINUTES': 'airborne_minutes',
    'AIR_TIME': 'air_time',
    'AIRLINE_ID': 'airline_id',
    'UNIQUE_CARRIER_NAME': 'carrier_name',
    'CARRIER_NAME': 'carrier_name_2',
    'CARRIER_GROUP': 'carrier_group',
    'CARRIER_GROUP_NEW': 'carrier_group_new',
    'REGION': 'region',
    'ORIGIN_AIRPORT_ID': 'origin_airport_id',
    'ORIGIN_AIRPORT_SEQ_ID': 'origin_airport_seq_id',
    'ORIGIN_CITY_MARKET_ID': 'origin_city_market_id',
    'ORIGIN_CITY_NAME': 'origin_city_name',
    'ORIGIN_STATE_ABR': 'origin_state_abr',
    'ORIGIN_STATE_FIPS': 'origin_state_fips',
    'ORIGIN_STATE_NM': 'origin_state_nm',
    'ORIGIN_WAC': 'origin_wac',
    'DEST_AIRPORT_ID': 'dest_airport_id',
    'DEST_AIRPORT_SEQ_ID': 'dest_airport_seq_id',
    'DEST_CITY_MARKET_ID': 'dest_city_market_id',
    'DEST_CITY_NAME': 'dest_city_name',
    'DEST_STATE_ABR': 'dest_state_abr',
    'DEST_STATE_FIPS': 'dest_state_fips',
    'DEST_STATE_NM': 'dest_state_nm',
    'DEST_WAC': 'dest_wac',
    'AIRCRAFT_GROUP': 'aircraft_group',
    'AIRCRAFT_CONFIG': 'aircraft_config',
    'QUARTER': 'quarter',
    'DISTANCE_GROUP': 'distance_group',
    'CLASS': 'service_class',  # T-100 uses CLASS for service class
}


def standardize_t100_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize T-100 column names to snake_case."""
    df = df.copy()
    # Create mapping for columns that exist
    rename_map = {}
    for col in df.columns:
        upper_col = col.upper()
        if upper_col in T100_COLUMN_MAP:
            rename_map[col] = T100_COLUMN_MAP[upper_col]
    if rename_map:
        df = df.rename(columns=rename_map)
    return df


def clean_t100_segment(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and validate T-100 segment data."""
    df = standardize_t100_columns(df)
    
    # Filter to scheduled passenger service (Service Class = 'F')
    if 'service_class' in df.columns:
        df = df[df['service_class'] == 'F'].copy()
    
    # Ensure required columns exist - use carrier_code (from UNIQUE_CARRIER)
    required = ['carrier_code', 'year', 'month', 'origin_airport', 'dest_airport', 
                'departures_performed', 'available_seats', 'passengers', 'distance_miles']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required T-100 columns: {missing}")
    
    # Convert numeric columns
    numeric_cols = ['year', 'month', 'departures_performed', 'departures_scheduled',
                    'available_seats', 'passengers', 'distance_miles', 'available_capacity',
                    'freight', 'mail', 'ramp_to_ramp_minutes', 'airborne_minutes',
                    'payload', 'air_time', 'airline_id']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Filter valid data
    df = df[df['distance_miles'] > 0].copy()
    df = df[df['available_seats'] > 0].copy()
    df = df[df['departures_performed'] > 0].copy()
    
    # Create date_id for joining with dim_date
    df['date_id'] = (df['year'] * 10000 + df['month'] * 100 + 1).astype(int)
    
    # Create route key
    df['route'] = df['origin_airport'] + '-' + df['dest_airport']
    
    return df


def create_fact_revenue(db1b_market: pd.DataFrame,
                        db1b_coupon: pd.DataFrame,
                        t100_segment: pd.DataFrame,
                        dim_date: pd.DataFrame,
                        dim_airline: pd.DataFrame,
                        dim_route: pd.DataFrame,
                        casm: float = DEFAULT_CASM) -> pd.DataFrame:
    """
    Create modeled revenue fact table from DB1B and T-100 data.
    
    All metrics are ESTIMATED/MODELED and must be labeled as such.
    """
    if t100_segment.empty:
        return pd.DataFrame()
    
    # Clean T-100 data
    t100 = clean_t100_segment(t100_segment)
    
    # Aggregate T-100 to carrier-route-month level
    t100_agg = t100.groupby(['year', 'month', 'carrier_code', 'route']).agg(
        total_seats=('available_seats', 'sum'),
        total_departures=('departures_performed', 'sum'),
        total_passengers=('passengers', 'sum'),
        avg_distance=('distance_miles', 'mean'),
    ).reset_index()
    
    t100_agg['date_id'] = (t100_agg['year'] * 10000 + t100_agg['month'] * 100 + 1).astype(int)
    t100_agg['load_factor'] = t100_agg['total_passengers'] / t100_agg['total_seats']
    t100_agg['load_factor'] = t100_agg['load_factor'].clip(0, 1)
    
    # Process DB1B Market data
    if db1b_market.empty:
        return pd.DataFrame()
    
    db1b = db1b_market.copy()
    
    # Process DB1B Market data
    if db1b_market.empty:
        return pd.DataFrame()
    
    db1b = db1b_market.copy()
    
    # Case-insensitive column mapping for DB1B
    db1b_cols_lower = {c.lower(): c for c in db1b.columns}
    
    required_cols = {
        'opcarrier': 'OpCarrier',
        'origin': 'Origin',
        'dest': 'Dest',
        'passengers': 'Passengers',
        'mktfare': 'MktFare',
        'mktdistance': 'MktDistance',  # Note: MktDistance (with 't')
        'mktmilesflown': 'MktMilesFlown',
        'bulkfare': 'BulkFare',
        'year': 'Year',
        'quarter': 'Quarter',
        'origincountry': 'OriginCountry',
        'destcountry': 'DestCountry',
    }
    
    # Check and map required columns
    missing = []
    actual_cols = {}
    for req, default in required_cols.items():
        if req in db1b_cols_lower:
            actual_cols[req] = db1b_cols_lower[req]
        else:
            missing.append(req)
    
    if missing:
        logger.warning(f"Missing DB1B columns: {missing}")
        return pd.DataFrame()
    
    # Assign actual column names
    carrier_col = actual_cols['opcarrier']
    origin_col = actual_cols['origin']
    dest_col = actual_cols['dest']
    passengers_col = actual_cols['passengers']
    fare_col = actual_cols['mktfare']
    distance_col = actual_cols['mktdistance']
    miles_flown_col = actual_cols['mktmilesflown']
    bulk_fare_col = actual_cols['bulkfare']
    year_col = actual_cols['year']
    quarter_col = actual_cols['quarter']
    origin_country_col = actual_cols['origincountry']
    dest_country_col = actual_cols['destcountry']
    
# Filter US domestic, non-bulk fares, valid fare range
    if bulk_fare_col in db1b.columns:
        db1b = db1b[db1b[bulk_fare_col] == 0].copy()
    
    if origin_country_col in db1b.columns and dest_country_col in db1b.columns:
        db1b = db1b[(db1b[origin_country_col] == 'US') & (db1b[dest_country_col] == 'US')].copy()
    
    # Filter fare range per Borenstein methodology
    db1b = db1b[(db1b[fare_col] >= 20) & (db1b[fare_col] <= 9998)].copy()
    
    # Create route key
    db1b['route'] = db1b[origin_col] + '-' + db1b[dest_col]
    
    # Aggregate DB1B to carrier-route-quarter
    # Use OpCarrier (operating carrier) for consistency with T-100
    db1b_agg = db1b.groupby([year_col, quarter_col, carrier_col, 'route']).agg(
        db1b_passengers=(passengers_col, 'sum'),
        db1b_fare=(fare_col, 'mean'),
        db1b_distance=(distance_col, 'mean'),
        db1b_miles_flown=(miles_flown_col, 'mean') if miles_flown_col in db1b.columns else (distance_col, 'mean'),
    ).reset_index()
    
    # Scale DB1B 10% sample to 100%
    db1b_agg['estimated_passengers'] = db1b_agg['db1b_passengers'] * DB1B_SAMPLE_RATE
    db1b_agg['estimated_ticket_revenue'] = db1b_agg['db1b_passengers'] * db1b_agg['db1b_fare'] * DB1B_SAMPLE_RATE
    
    # Convert quarter to month range for joining with monthly T-100
    quarter_to_months = {1: [1,2,3], 2: [4,5,6], 3: [7,8,9], 4: [10,11,12]}
    
    # Expand quarterly DB1B to monthly
    monthly_rows = []
    for _, row in db1b_agg.iterrows():
        for month in quarter_to_months.get(row[quarter_col], []):
            monthly_rows.append({
                'year': row[year_col],
                'month': month,
                'carrier_code': row[carrier_col],
                'route': row['route'],
                'estimated_passengers': row['estimated_passengers'] / 3,  # Split quarterly across 3 months
                'estimated_ticket_revenue': row['estimated_ticket_revenue'] / 3,
                'avg_distance_db1b': row['db1b_distance'],
            })
    
    if not monthly_rows:
        return pd.DataFrame()
    
    db1b_monthly = pd.DataFrame(monthly_rows)
    db1b_monthly['date_id'] = (db1b_monthly['year'] * 10000 + db1b_monthly['month'] * 100 + 1).astype(int)
    
    # Join DB1B monthly with T-100 monthly on carrier, route, year, month
    # Rename T-100 columns to avoid conflicts and make them identifiable
    t100_agg_renamed = t100_agg.rename(columns={
        'total_seats': 'total_seats_t100',
        'total_departures': 'total_departures_t100',
        'total_passengers': 'total_passengers_t100',
        'avg_distance': 'avg_distance_t100',
    })
    
    merged = pd.merge(
        db1b_monthly,
        t100_agg_renamed,
        on=['year', 'month', 'carrier_code', 'route'],
        how='inner'
    )
    
    if merged.empty:
        logger.warning("No matching carrier-route-month between DB1B and T-100")
        return pd.DataFrame()
    
    # Join with dimensions to get surrogate keys
    # Airline
    airline_map = dim_airline.set_index('carrier_code')['airline_id'].to_dict()
    merged['airline_id'] = merged['carrier_code'].map(airline_map)
    
    # Route
    route_map = dim_route.set_index('route_code')['route_id'].to_dict()
    merged['route_id'] = merged['route'].map(route_map)
    
    # Date
    merged['date_id'] = (merged['year'] * 10000 + merged['month'] * 100 + 1).astype(int)
    
    # Drop rows with missing keys
    merged = merged.dropna(subset=['airline_id', 'route_id', 'date_id'])
    merged['airline_id'] = merged['airline_id'].astype(int)
    merged['route_id'] = merged['route_id'].astype(int)
    
    if merged.empty:
        return pd.DataFrame()
    
    # Calculate modeled metrics
    # Use T-100 columns (with _t100 suffix)
    merged['estimated_load_factor'] = merged['total_passengers_t100'] / merged['total_seats_t100']
    merged['estimated_load_factor'] = merged['estimated_load_factor'].clip(0, 1)
    
    # Estimated operating cost = Total Seats * Avg Distance * CASM
    merged['estimated_operating_cost'] = merged['total_seats_t100'] * merged['avg_distance_t100'] * casm
    
    merged['estimated_profit'] = merged['estimated_ticket_revenue'] - merged['estimated_operating_cost']
    merged['profit_margin'] = merged['estimated_profit'] / merged['estimated_ticket_revenue'].replace(0, np.nan)
    merged['profit_margin'] = merged['profit_margin'].clip(-1, 1)
    
    merged['revenue_per_passenger'] = merged['estimated_ticket_revenue'] / merged['estimated_passengers'].replace(0, np.nan)
    merged['revenue_per_flight'] = merged['estimated_ticket_revenue'] / merged['total_departures_t100'].replace(0, np.nan)
    
    # Add quarter
    merged['quarter'] = ((merged['month'] - 1) // 3) + 1
    
    # Add surrogate revenue_id
    merged['revenue_id'] = range(1, len(merged) + 1)
    
    # Select and order output columns
    output_cols = [
        'revenue_id', 'date_id', 'year', 'quarter', 'month',
        'airline_id', 'route_id',
        'estimated_passengers', 'estimated_ticket_revenue',
        'estimated_load_factor', 'estimated_operating_cost',
        'estimated_profit', 'profit_margin',
        'revenue_per_passenger', 'revenue_per_flight'
    ]
    
    result = merged[output_cols].copy()
    return result


def add_airport_efficiency_score(fact_flights: pd.DataFrame, dim_airport: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Airport Operational Efficiency Score.
    
    Framework:
    - 40% On-Time Performance (OTP %)
    - 25% Cancellation Performance (1 - cancel %)
    - 20% Delay Severity (1 - avg delay / max delay)
    - 15% Taxi/Turnaround Performance (1 - avg taxi / max taxi)
    """
    # Calculate airport-level metrics (as origin)
    origin_metrics = fact_flights.groupby("origin_airport_id").agg(
        total_flights=("flight_id", "count"),
        delayed_flights=("is_delayed", "sum"),
        cancelled_flights=("cancelled_flag", "sum"),
        avg_arr_delay=("arr_delay_min", "mean"),
        avg_taxi_out=("taxi_out_min", "mean"),
        avg_taxi_in=("taxi_in_min", "mean"),
    ).reset_index()
    
    # Calculate components (0-100 scale)
    origin_metrics["otp_pct"] = 100 * (1 - origin_metrics["delayed_flights"] / origin_metrics["total_flights"])
    origin_metrics["cancel_pct"] = 100 * (1 - origin_metrics["cancelled_flights"] / origin_metrics["total_flights"])
    
    # Normalize delay severity (invert: lower delay = higher score)
    max_delay = origin_metrics["avg_arr_delay"].max()
    origin_metrics["delay_severity_score"] = 100 * (1 - origin_metrics["avg_arr_delay"] / max_delay)
    
    # Normalize taxi performance
    max_taxi = origin_metrics[["avg_taxi_out", "avg_taxi_in"]].max().max()
    origin_metrics["avg_taxi"] = (origin_metrics["avg_taxi_out"] + origin_metrics["avg_taxi_in"]) / 2
    origin_metrics["taxi_score"] = 100 * (1 - origin_metrics["avg_taxi"] / max_taxi)
    
    # Weighted composite
    origin_metrics["efficiency_score"] = (
        0.40 * origin_metrics["otp_pct"] +
        0.25 * origin_metrics["cancel_pct"] +
        0.20 * origin_metrics["delay_severity_score"] +
        0.15 * origin_metrics["taxi_score"]
    )
    
    # Rank
    origin_metrics["efficiency_rank"] = origin_metrics["efficiency_score"].rank(ascending=False, method="min").astype(int)
    
    # Merge back to airport dimension
    airport_scores = origin_metrics[["origin_airport_id", "efficiency_score", "efficiency_rank", 
                                      "otp_pct", "cancel_pct", "delay_severity_score", "taxi_score"]]
    airport_scores.columns = ["airport_id", "efficiency_score", "efficiency_rank",
                               "otp_pct", "cancel_pct", "delay_severity_score", "taxi_score"]
    
    dim_airport = dim_airport.merge(airport_scores, on="airport_id", how="left")
    
    return dim_airport


def add_route_profitability_classification(fact_revenue: pd.DataFrame) -> pd.DataFrame:
    """Classify routes into 2x2 profitability matrix."""
    if fact_revenue.empty:
        return fact_revenue
    
    df = fact_revenue.copy()
    
    # Use medians as thresholds
    rev_median = df["estimated_ticket_revenue"].median()
    profit_median = df["estimated_profit"].median()
    
    def classify(row):
        high_rev = row["estimated_ticket_revenue"] >= rev_median
        high_profit = row["estimated_profit"] >= profit_median
        
        if high_rev and high_profit:
            return "High Revenue / High Profit"
        elif high_rev and not high_profit:
            return "High Revenue / Low Profit"
        elif not high_rev and high_profit:
            return "Low Revenue / High Profit"
        else:
            return "Low Revenue / Low Profit"
    
    df["profitability_class"] = df.apply(classify, axis=1)
    return df


def add_seasonal_revenue_analysis(fact_revenue: pd.DataFrame, dim_date: pd.DataFrame) -> pd.DataFrame:
    """Add seasonal revenue analysis to fact_revenue."""
    if fact_revenue.empty:
        return fact_revenue
    
    df = fact_revenue.copy()
    
    # Add season from dim_date
    season_map = dim_date.set_index("date_id")["season"].to_dict()
    df["season"] = df["date_id"].map(season_map)
    
    return df


def get_seasonal_revenue_summary(fact_revenue: pd.DataFrame, dim_date: pd.DataFrame) -> pd.DataFrame:
    """Generate seasonal revenue summary."""
    if fact_revenue.empty:
        return pd.DataFrame()
    
    df = fact_revenue.copy()
    
    # Add season
    season_map = dim_date.set_index("date_id")["season"].to_dict()
    df["season"] = df["date_id"].map(season_map)
    
    # Seasonal aggregation
    seasonal = df.groupby("season").agg(
        estimated_revenue=("estimated_ticket_revenue", "sum"),
        estimated_profit=("estimated_profit", "sum"),
        estimated_passengers=("estimated_passengers", "sum"),
        routes=("route_id", "nunique"),
        carriers=("airline_id", "nunique"),
        avg_load_factor=("estimated_load_factor", "mean"),
        avg_profit_margin=("profit_margin", "mean"),
    ).reset_index()
    
    seasonal["profit_margin_pct"] = seasonal["estimated_profit"] / seasonal["estimated_revenue"]
    seasonal["revenue_per_route"] = seasonal["estimated_revenue"] / seasonal["routes"]
    seasonal["profit_per_route"] = seasonal["estimated_profit"] / seasonal["routes"]
    
    # Order seasons
    season_order = {"Winter": 0, "Spring": 1, "Summer": 2, "Fall": 3}
    seasonal["season_order"] = seasonal["season"].map(season_order)
    seasonal = seasonal.sort_values("season_order").drop("season_order", axis=1)
    
    return seasonal


def get_seasonal_carrier_performance(fact_revenue: pd.DataFrame, dim_date: pd.DataFrame, dim_airline: pd.DataFrame) -> pd.DataFrame:
    """Generate seasonal carrier performance."""
    if fact_revenue.empty:
        return pd.DataFrame()
    
    df = fact_revenue.copy()
    
    # Add season
    season_map = dim_date.set_index("date_id")["season"].to_dict()
    df["season"] = df["date_id"].map(season_map)
    
    # Add carrier name
    carrier_map = dim_airline.set_index("airline_id")["carrier_code"].to_dict()
    df["carrier_code"] = df["airline_id"].map(carrier_map)
    
    seasonal_carrier = df.groupby(["season", "carrier_code"]).agg(
        estimated_revenue=("estimated_ticket_revenue", "sum"),
        estimated_profit=("estimated_profit", "sum"),
        estimated_passengers=("estimated_passengers", "sum"),
        routes=("route_id", "nunique"),
        avg_load_factor=("estimated_load_factor", "mean"),
    ).reset_index()
    
    seasonal_carrier["profit_margin"] = seasonal_carrier["estimated_profit"] / seasonal_carrier["estimated_revenue"]
    seasonal_carrier["revenue_per_route"] = seasonal_carrier["estimated_revenue"] / seasonal_carrier["routes"]
    
    # Order seasons
    season_order = {"Winter": 0, "Spring": 1, "Summer": 2, "Fall": 3}
    seasonal_carrier["season_order"] = seasonal_carrier["season"].map(season_order)
    seasonal_carrier = seasonal_carrier.sort_values(["season_order", "estimated_revenue"], ascending=[True, False])
    seasonal_carrier = seasonal_carrier.drop("season_order", axis=1)
    
    return seasonal_carrier


def get_seasonal_route_performance(fact_revenue: pd.DataFrame, dim_date: pd.DataFrame, dim_route: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """Generate top seasonal routes by revenue."""
    if fact_revenue.empty:
        return pd.DataFrame()
    
    df = fact_revenue.copy()
    
    # Add season
    season_map = dim_date.set_index("date_id")["season"].to_dict()
    df["season"] = df["date_id"].map(season_map)
    
    # Add route code
    route_map = dim_route.set_index("route_id")["route_code"].to_dict()
    df["route_code"] = df["route_id"].map(route_map)
    
    seasonal_route = df.groupby(["season", "route_code"]).agg(
        estimated_revenue=("estimated_ticket_revenue", "sum"),
        estimated_profit=("estimated_profit", "sum"),
        estimated_passengers=("estimated_passengers", "sum"),
        avg_load_factor=("estimated_load_factor", "mean"),
    ).reset_index()
    
    seasonal_route["profit_margin"] = seasonal_route["estimated_profit"] / seasonal_route["estimated_revenue"]
    
    # Order seasons and get top N per season
    season_order = {"Winter": 0, "Spring": 1, "Summer": 2, "Fall": 3}
    seasonal_route["season_order"] = seasonal_route["season"].map(season_order)
    seasonal_route = seasonal_route.sort_values(["season_order", "estimated_revenue"], ascending=[True, False])
    
    top_routes = seasonal_route.groupby("season").head(top_n).drop("season_order", axis=1)
    
    return top_routes