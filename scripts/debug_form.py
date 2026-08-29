#!/usr/bin/env python3
"""Debug the TranStats download form."""
import requests
import re

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

url = 'https://www.transtats.bts.gov/DL_SelectFields.aspx?Table_ID=259&DBShortName=Air%20Carriers'
resp = session.get(url, timeout=30)
print(f'Status: {resp.status_code}')
print(f'Content length: {len(resp.text)}')

# Find form action
forms = re.findall(r'<form[^>]*action="([^"]*)"', resp.text)
print(f'Form actions: {forms}')

# Find all input fields
inputs = re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"', resp.text)
for name, value in inputs[:30]:
    print(f'  {name} = {value}')

# Find select options
selects = re.findall(r'<select[^>]*name="([^"]*)"', resp.text)
print(f'Select names: {selects}')

# Save full HTML for inspection
with open('debug_form.html', 'w', encoding='utf-8') as f:
    f.write(resp.text)
print('\nFull HTML saved to debug_form.html')