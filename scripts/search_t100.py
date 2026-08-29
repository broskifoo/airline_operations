#!/usr/bin/env python3
"""Search for T-100 datasets on data.bts.gov."""
import requests

url = 'https://data.bts.gov/api/views/metadata/v1'
resp = requests.get(url, timeout=30)
data = resp.json()

for item in data:
    name = item.get('name', '').lower()
    desc = item.get('description', '').lower()
    if 't100' in name or 't100' in desc or 'segment' in name or 'segment' in desc:
        if 'ferry' not in name and 'ncfo' not in name:
            print(f"ID: {item['id']}")
            print(f"  Name: {item['name']}")
            print(f"  Description: {item['description'][:150]}")
            print(f"  Updated: {item['dataUpdatedAt']}")
            print(f"  Web URI: {item['webUri']}")
            print()