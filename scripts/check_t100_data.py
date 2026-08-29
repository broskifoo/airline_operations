#!/usr/bin/env python3
"""Check the downloaded T-100 data quality."""
import pandas as pd
import zipfile
from pathlib import Path

zip_path = Path('data/raw/T_T100D_SEGMENT_US_CARRIER_ONLY_20260828_152133.zip')
with zipfile.ZipFile(zip_path, 'r') as zf:
    with zf.open('T_T100D_SEGMENT_US_CARRIER_ONLY.csv') as f:
        df = pd.read_csv(f, low_memory=False)
        print('Total rows:', len(df))
        print('Rows with departures > 0:', (df['DEPARTURES_PERFORMED'] > 0).sum())
        print()
        
        # Check regions
        print('Region breakdown:')
        print(df['REGION'].value_counts())
        print()
        
        # Check carrier groups
        print('Carrier group breakdown:')
        print(df['CARRIER_GROUP'].value_counts())
        print()
        
        # Check if major US carriers have data
        major = ['WN', 'DL', 'AA', 'UA', 'OO', 'NK', 'B6', 'AS', 'F9']
        for c in major:
            sub = df[df['UNIQUE_CARRIER'] == c]
            dep = sub['DEPARTURES_PERFORMED'].sum()
            seats = sub['SEATS'].sum()
            pax = sub['PASSENGERS'].sum()
            routes = sub['ORIGIN'].nunique()
            print(f'{c}: departures={dep:.0f}, seats={seats:.0f}, pax={pax:.0f}, routes={routes}')