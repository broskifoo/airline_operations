#!/usr/bin/env python3
"""Try various direct download URL patterns for TranStats."""
import requests
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.transtats.bts.gov/DL_SelectFields.aspx?Table_ID=259&DBShortName=Air%20Carriers',
})

# Various URL patterns to try
urls = [
    # Pattern 1: Direct download with params
    "https://www.transtats.bts.gov/Download_Lookup.asp?Table_ID=259&DBShortName=Air%20Carriers&Has_Group=3&Is_Zipped=1&Download_Format=CSV&Year=2024&Month=1&Geography=All",
    
    # Pattern 2: Another download endpoint
    "https://www.transtats.bts.gov/DownLoad_Table2.asp?Table_ID=259&DBShortName=Air%20Carriers&Has_Group=3&Is_Zipped=1&Download_Format=CSV&Year=2024&Month=1&Geography=All",
    
    # Pattern 3: With QO parameters
    "https://www.transtats.bts.gov/DownLoad_Table2.asp?QO_fu146_anzr=Nv4+Pn44vr45&gnoyr_VQ=GEE&Table_ID=259&DBShortName=Air%20Carriers&Has_Group=3&Is_Zipped=1&Download_Format=CSV&Year=2024&Month=1&Geography=All",
    
    # Pattern 4: Using cbo field names
    "https://www.transtats.bts.gov/DownLoad_Table2.asp?Table_ID=259&DBShortName=Air%20Carriers&Has_Group=3&Is_Zipped=1&Download_Format=CSV&cboYear=2024&cboPeriod=1&cboGeography=All&chkSelectAll=on",
    
    # Pattern 5: POST to the form URL
    # Will try POST separately
]

for i, url in enumerate(urls, 1):
    print(f"\nTrying pattern {i}: {url[:100]}...")
    try:
        resp = session.get(url, timeout=60, stream=True)
        print(f"  Status: {resp.status_code}")
        print(f"  Content-Type: {resp.headers.get('Content-Type', 'N/A')}")
        print(f"  Content-Disposition: {resp.headers.get('Content-Disposition', 'N/A')}")
        print(f"  Content-Length: {resp.headers.get('Content-Length', 'N/A')}")
        
        if resp.status_code == 200:
            content_type = resp.headers.get('Content-Type', '').lower()
            if 'zip' in content_type or 'octet-stream' in content_type:
                # Save it
                filename = f"test_pattern_{i}.zip"
                with open(filename, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                import os
                size = os.path.getsize(filename)
                print(f"  Saved: {filename} ({size/1e6:.1f} MB)")
                if size > 1000:
                    print("  *** SUCCESS! ***")
                    break
            elif 'html' in content_type:
                # Check if it's an error page
                content = resp.text[:500]
                print(f"  HTML response: {content[:200]}...")
    except Exception as e:
        print(f"  Error: {e}")

# Now try POST
print("\n\nTrying POST to form action...")
post_url = "https://www.transtats.bts.gov/DownLoad_Table2.asp"
post_data = {
    'Table_ID': '259',
    'DBShortName': 'Air Carriers',
    'Has_Group': '3',
    'Is_Zipped': '1',
    'Download_Format': 'CSV',
    'QO_fu146_anzr': 'Nv4+Pn44vr45',
    'gnoyr_VQ': 'GEE',
    'Year': '2024',
    'Month': '1',
    'Geography': 'All',
    'cboYear': '2024',
    'cboPeriod': '1',
    'cboGeography': 'All',
    'chkSelectAll': 'on',
}

try:
    resp = session.post(post_url, data=post_data, timeout=60, stream=True)
    print(f"  Status: {resp.status_code}")
    print(f"  Content-Type: {resp.headers.get('Content-Type', 'N/A')}")
    print(f"  Content-Disposition: {resp.headers.get('Content-Disposition', 'N/A')}")
    
    if resp.status_code == 200:
        content_type = resp.headers.get('Content-Type', '').lower()
        if 'zip' in content_type or 'octet-stream' in content_type:
            filename = "test_post.zip"
            with open(filename, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            import os
            size = os.path.getsize(filename)
            print(f"  Saved: {filename} ({size/1e6:.1f} MB)")
            if size > 1000:
                print("  *** POST SUCCESS! ***")
        else:
            print(f"  Not a zip: {resp.text[:300]}")
except Exception as e:
    print(f"  POST Error: {e}")