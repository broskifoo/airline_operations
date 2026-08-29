#!/usr/bin/env python3
"""Check T-100 Segment Summary By Carrier dataset."""
import requests

# By Carrier - try without order param
url = 'https://data.bts.gov/resource/q4tb-tbff.json'
params = {'$limit': 5}
resp = requests.get(url, params=params, timeout=30)
print(f'By Carrier - Status: {resp.status_code}')
print(f'Response: {resp.text[:500]}')
if resp.status_code == 200:
    data = resp.json()
    if data:
        print(f'Columns: {list(data[0].keys())}')
        for row in data[:3]:
            print(row)
    else:
        print('No data returned')

print("\n" + "="*60)

# By Origin Airport
url2 = 'https://data.bts.gov/resource/r495-tyji.json'
resp2 = requests.get(url2, params=params, timeout=30)
print(f'By Origin Airport - Status: {resp2.status_code}')
print(f'Response: {resp2.text[:500]}')
if resp2.status_code == 200:
    data2 = resp2.json()
    if data2:
        print(f'Columns: {list(data2[0].keys())}')
        for row in data2[:3]:
            print(row)
    else:
        print('No data returned')