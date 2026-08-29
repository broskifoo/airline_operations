#!/usr/bin/env python3
"""Debug the merge with larger sample."""
import pandas as pd
import zipfile
from pathlib import Path

# Load T-100 - full first month
zip_path = Path('data/raw/T_T100D_SEGMENT_ALL_CARRIER_2024_01.zip')
with zipfile.ZipFile(zip_path, 'r') as zf:
    with zf.open('T_T100D_SEGMENT_US_CARRIER_ONLY.csv') as f:
        t100 = pd.read_csv(f, low_memory=False)

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
    'CLASS': 'service_class',
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
    'RAMP_TO_RAMP': 'ramp_to_ramp_minutes',
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
    'CLASS': 'service_class',
}

rename_map = {}
for col in t100.columns:
    upper_col = col.upper()
    if upper_col in T100_COLUMN_MAP:
        rename_map[col] = T100_COLUMN_MAP[upper_col]

t100 = t100.rename(columns=rename_map)

# Filter to F
if 'service_class' in t100.columns:
    t100 = t100[t100['service_class'] == 'F'].copy()

# Convert numeric
numeric_cols = ['year', 'month', 'departures_performed', 'departures_scheduled',
                'available_seats', 'passengers', 'distance_miles', 'available_capacity',
                'freight', 'mail', 'ramp_to_ramp_minutes', 'airborne_minutes',
                'payload', 'air_time', 'airline_id']
for col in numeric_cols:
    if col in t100.columns:
        t100[col] = pd.to_numeric(t100[col], errors='coerce')

t100 = t100[t100['distance_miles'] > 0].copy()
t100 = t100[t100['available_seats'] > 0].copy()
t100 = t100[t100['departures_performed'] > 0].copy()
t100['date_id'] = (t100['year'] * 10000 + t100['month'] * 100 + 1).astype(int)
t100['route'] = t100['origin_airport'] + '-' + t100['dest_airport']

print(f"T-100 cleaned: {len(t100)} rows")

# Aggregate T-100
t100_agg = t100.groupby(['year', 'month', 'carrier_code', 'route']).agg(
    total_seats=('available_seats', 'sum'),
    total_departures=('departures_performed', 'sum'),
    total_passengers=('passengers', 'sum'),
    avg_distance=('distance_miles', 'mean'),
).reset_index()

print(f"T-100 agg: {len(t100_agg)} rows")
print("T-100 agg columns:", list(t100_agg.columns))

# Now DB1B - load a sample
db1b_path = Path('data/raw/DB1B_Market_2024_Q1/Origin_and_Destination_Survey_DB1BMarket_2024_1.csv')
db1b = pd.read_csv(db1b_path, nrows=50000, low_memory=False)

print(f"\nDB1B sample: {len(db1b)} rows")

# Standardize DB1B columns
db1b_cols = {c.upper(): c for c in db1b.columns}
print("\nDB1B key columns:")
for k in ['OPCARRIER', 'TICKETCARRIER', 'ORIGIN', 'DEST', 'PASSENGERS', 'MKTFARE', 'MKTDISTANCE', 'MKTMILESFLOWN', 'BULKFARE', 'YEAR', 'QUARTER', 'ORIGINCOUNTRY', 'DESTCOUNTRY']:
    print(f"  {k}: {db1b_cols.get(k)}")

# Filter US domestic
if 'ORIGINCOUNTRY' in db1b.columns and 'DESTCOUNTRY' in db1b.columns:
    db1b = db1b[(db1b['ORIGINCOUNTRY'] == 'US') & (db1b['DESTCOUNTRY'] == 'US')].copy()
    print(f"After US filter: {len(db1b)} rows")

# Filter bulk fares
if 'BULKFARE' in db1b.columns:
    db1b = db1b[db1b['BULKFARE'] == 0].copy()
    print(f"After bulk filter: {len(db1b)} rows")

# Filter fare range
if 'MKTFARE' in db1b.columns:
    db1b = db1b[(db1b['MKTFARE'] >= 20) & (db1b['MKTFARE'] <= 9998)].copy()
    print(f"After fare filter: {len(db1b)} rows")

# Create route
db1b['route'] = db1b['ORIGIN'] + '-' + db1b['DEST']

# Aggregate DB1B
carrier_col = 'OPCARRIER'
origin_col = 'ORIGIN'
dest_col = 'DEST'
passengers_col = 'PASSENGERS'
fare_col = 'MKTFARE'
distance_col = 'MKTDISTANCE'
miles_flown_col = 'MKTMILESFLOWN'
year_col = 'YEAR'
quarter_col = 'QUARTER'

db1b_agg = db1b.groupby([year_col, quarter_col, carrier_col, 'route']).agg(
    db1b_passengers=(passengers_col, 'sum'),
    db1b_fare=(fare_col, 'mean'),
    db1b_distance=(distance_col, 'mean'),
    db1b_miles_flown=(miles_flown_col, 'mean'),
).reset_index()

print(f"\nDB1B agg: {len(db1b_agg)} rows")
print("DB1B agg columns:", list(db1b_agg.columns))

# Scale
DB1B_SAMPLE_RATE = 10
db1b_agg['estimated_passengers'] = db1b_agg['db1b_passengers'] * DB1B_SAMPLE_RATE
db1b_agg['estimated_ticket_revenue'] = db1b_agg['db1b_passengers'] * db1b_agg['db1b_fare'] * DB1B_SAMPLE_RATE

# Expand to monthly
quarter_to_months = {1: [1,2,3], 2: [4,5,6], 3: [7,8,9], 4: [10,11,12]}
monthly_rows = []
for _, row in db1b_agg.iterrows():
    for month in quarter_to_months.get(row[quarter_col], []):
        monthly_rows.append({
            'year': row[year_col],
            'month': month,
            'carrier_code': row[carrier_col],
            'route': row['route'],
            'estimated_passengers': row['estimated_passengers'] / 3,
            'estimated_ticket_revenue': row['estimated_ticket_revenue'] / 3,
            'avg_distance_db1b': row['db1b_distance'],
        })

db1b_monthly = pd.DataFrame(monthly_rows)
print(f"\nDB1B monthly: {len(db1b_monthly)} rows")
print("DB1B monthly columns:", list(db1b_monthly.columns))

# Now merge
merged = pd.merge(
    db1b_monthly,
    t100_agg,
    on=['year', 'month', 'carrier_code', 'route'],
    how='inner',
    suffixes=('_db1b', '_t100')
)

print(f"\nMerged: {len(merged)} rows")
print("Merged columns:", list(merged.columns))

if len(merged) > 0:
    print("\nSample merged data:")
    print(merged[['year', 'month', 'carrier_code', 'route', 'estimated_passengers', 'total_seats', 'total_passengers', 'avg_distance']].head())