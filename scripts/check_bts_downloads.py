#!/usr/bin/env python3
"""Check BTS Airline Data Downloads page for bulk T-100 downloads."""
import requests
from bs4 import BeautifulSoup

url = 'https://www.bts.gov/airline-data-downloads'
resp = requests.get(url, timeout=30)
print(f'Status: {resp.status_code}')

soup = BeautifulSoup(resp.text, 'html.parser')

# Find all links
for link in soup.find_all('a', href=True):
    href = link['href']
    text = link.get_text(strip=True)
    if 't100' in href.lower() or 't100' in text.lower() or 'segment' in text.lower():
        print(f"Link: {href}")
        print(f"  Text: {text}")

# Also search for download links
for link in soup.find_all('a', href=True):
    if '.zip' in link['href'] or '.csv' in link['href']:
        print(f"Download: {link['href']} - {link.get_text(strip=True)[:80]}")