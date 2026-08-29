#!/usr/bin/env python3
"""Try to find current T-100 files on PREZIP directory."""
import requests
import re

# Try to access PREZIP directory
prezip_url = "https://transtats.bts.gov/PREZIP/"
resp = requests.get(prezip_url, timeout=30)
print(f'PREZIP Status: {resp.status_code}')
print(f'Content length: {len(resp.text)}')

# Find all T-100 segment links
links = re.findall(r'href="(/PREZIP/[^"]+_T_T100[^"]+\.zip)"', resp.text)
print(f"\nFound {len(links)} T-100 links:")
for link in sorted(set(links))[:20]:
    print(f"  {link}")

# Also check for 2024 files
links_2024 = [l for l in links if '2024' in l]
print(f"\n2024 links: {len(links_2024)}")
for link in links_2024:
    print(f"  {link}")