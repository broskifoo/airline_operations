#!/usr/bin/env python3
"""Check T-100 dataset from data.bts.gov Socrata API."""
import requests

url = 'https://data.bts.gov/resource/jqx4-4iha.json'
params = {'$limit': 5, '$order': 'year DESC, month DESC'}
resp = requests.get(url, params=params, timeout=30)
print(f'Status: {resp.status_code}')
data = resp.json()
if data:
    print(f'Columns: {list(data[0].keys())}')
    for row in data[:3]:
        print(row)
        
# Also check total count
params_count = {'$select': 'count(*)'}
resp = requests.get(url, params=params_count, timeout=30)
print(f'Total rows: {resp.json()}')

# Check available years
params_years = {'$select': 'year', '$group': 'year', '$order': 'year DESC'}
resp = requests.get(url, params=params_years, timeout=30)
years = [r['year'] for r in resp.json()]
print(f'Available years: {years}')