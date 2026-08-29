#!/usr/bin/env python3
"""Debug the column names after rename."""
import pandas as pd
import zipfile
from pathlib import Path

# Load T-100
zip_path = Path('data/raw/T_T100D_SEGMENT_ALL_CARRIER_2024_01.zip')
with zipfile.ZipFile(zip_path, 'r') as zf:
    with zf.open('T_T100D_SEGMENT_US_CARRIER_ONLY.csv') as f:
        t100 = pd.read_csv(f, nrows=100, low_memory=False)

print("Original columns:")
for c in t100.columns:
    print(f"  {c}")

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
    'AIRBORNE_MINUTES': 'airborne_minutes',
    'PAYLOAD': 'payload',
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
    'CLASS': 'class',
}

rename_map = {}
for col in t100.columns:
    upper_col = col.upper()
    if upper_col in T100_COLUMN_MAP:
        rename_map[col] = T100_COLUMN_MAP[upper_col]

print("\nRename map:")
for k, v in rename_map.items():
    print(f"  {k} -> {v}")

t100_renamed = t100.rename(columns=rename_map)
print("\nRenamed columns:")
for c in t100_renamed.columns:
    print(f"  {c}")