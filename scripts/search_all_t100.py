#!/usr/bin/env python3
"""Search all T-100 related datasets on data.bts.gov."""
import requests

url = 'https://data.bts.gov/api/views/metadata/v1'
resp = requests.get(url, timeout=30)
data = resp.json()

for item in data:
    name = (item.get('name') or '').lower()
    desc = (item.get('description') or '').lower()
    if 't100' in name or 't-100' in name or 'traffic' in name or 'capacity' in name or 'segment' in name:
        if 'ferry' not in name and 'ncfo' not in name:
            print(f"ID: {item['id']}")
            print(f"  Name: {item['name']}")
            d = item.get('description') or ''
            print(f"  Desc: {d[:120]}")
            print()