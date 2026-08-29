#!/usr/bin/env python3
"""Debug T-100 column standardization."""
import pandas as pd
import zipfile
from pathlib import Path

zip_path = Path('data/raw/T_T100D_SEGMENT_ALL_CARRIER_2024_01.zip')
with zipfile.ZipFile(zip_path, 'r') as zf:
    with zf.open('T_T100D_SEGMENT_US_CARRIER_ONLY.csv') as f:
        df = pd.read_csv(f, nrows=100, low_memory=False)
        print('Original columns:')
        for c in df.columns:
            print(f'  {c}')
        print()
        
        # Test standardization
        T100_COLUMN_MAP = {
            'UNIQUE_CARRIER': 'carrier_code',
            'CARRIER': 'carrier_code',
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
        }
        
        rename_map = {}
        for col in df.columns:
            upper_col = col.upper()
            if upper_col in T100_COLUMN_MAP:
                rename_map[col] = T100_COLUMN_MAP[upper_col]
        
        print('Rename map:')
        for k, v in rename_map.items():
            print(f'  {k} -> {v}')
        
        # Check for duplicates in target
        targets = list(rename_map.values())
        from collections import Counter
        dup = [k for k, v in Counter(targets).items() if v > 1]
        print(f'\nDuplicate targets: {dup}')