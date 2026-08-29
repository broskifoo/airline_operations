#!/usr/bin/env python3
"""
Download T-100 Domestic Segment (All Carriers) data from BTS TranStats
using direct HTTP POST (faster and more reliable than Selenium).
"""

import argparse
import time
import logging
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Direct download endpoint for T-100 Domestic Segment (All Carriers)
# Table_ID=259 corresponds to "T-100 Domestic Segment (All Carriers)"
DOWNLOAD_URL = "https://www.transtats.bts.gov/DownLoad_Table2.asp"

# Form parameters for the download
# Based on TranStats form structure for Table_ID=259
DEFAULT_PARAMS = {
    'Table_ID': '259',
    'Has_Group': '3',
    'Is_Zipped': '1',
    'DBShortName': 'Air Carriers',
    'Download_Format': 'CSV',
    'QO_fu146_anzr': 'Nv4+Pn44vr45',
    'gnoyr_VQ': 'GEE',
    'GeoVarName': 'Geography',
    'GeoVarValue': 'All',
    'Year': '2024',
    'Month': '1',
}


def create_session() -> requests.Session:
    """Create a requests session with retry logic."""
    session = requests.Session()
    
    retry_strategy = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Set headers to mimic a browser
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    })
    
    return session


def get_form_tokens(session: requests.Session, url: str) -> dict:
    """Extract any hidden form tokens from the download page."""
    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        
        # Look for hidden inputs (like __VIEWSTATE, __EVENTVALIDATION, etc.)
        tokens = {}
        import re
        # Common ASP.NET hidden fields
        for field in ['__VIEWSTATE', '__EVENTVALIDATION', '__VIEWSTATEGENERATOR', '__EVENTTARGET', '__EVENTARGUMENT']:
            match = re.search(f'name="{field}"\s+value="([^"]*)"', resp.text)
            if match:
                tokens[field] = match.group(1)
        
        return tokens
    except Exception as e:
        logger.warning(f"Could not fetch form tokens: {e}")
        return {}


def download_t100_month(session: requests.Session, year: int, month: int, 
                        output_dir: Path) -> Path:
    """Download T-100 data for a specific year/month using direct POST."""
    logger.info(f"Downloading T-100 for {year}-{month:02d}...")
    
    # Prepare form data
    form_data = DEFAULT_PARAMS.copy()
    form_data['Year'] = str(year)
    form_data['Month'] = str(month)
    
    # Get form tokens
    tokens = get_form_tokens(session, "https://www.transtats.bts.gov/DL_SelectFields.aspx?Table_ID=259&DBShortName=Air%20Carriers")
    form_data.update(tokens)
    
    # The actual download POST endpoint
    download_url = "https://www.transtats.bts.gov/DownLoad_Table2.asp"
    
    # Some TranStats tables use different download endpoints
    # Try multiple possible endpoints
    endpoints = [
        "https://www.transtats.bts.gov/DownLoad_Table2.asp",
        "https://www.transtats.bts.gov/Download.asp",
        "https://www.transtats.bts.gov/Download_Table.asp",
    ]
    
    for endpoint in endpoints:
        try:
            logger.info(f"Trying endpoint: {endpoint}")
            resp = session.post(endpoint, data=form_data, timeout=120, stream=True)
            
            if resp.status_code == 200:
                content_type = resp.headers.get('Content-Type', '')
                content_disposition = resp.headers.get('Content-Disposition', '')
                
                # Check if we got a ZIP file
                if 'zip' in content_type.lower() or 'octet-stream' in content_type.lower() or 'attachment' in content_disposition.lower():
                    # Extract filename from Content-Disposition or create one
                    filename = f"T_T100D_SEGMENT_ALL_CARRIER_{year}_{month:02d}.zip"
                    if 'filename=' in content_disposition:
                        import re
                        match = re.search(r'filename[*]?=([^;]+)', content_disposition)
                        if match:
                            filename = match.group(1).strip('"')
                    
                    output_path = output_dir / filename
                    
                    # Save the ZIP
                    with open(output_path, 'wb') as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    if output_path.stat().st_size > 0:
                        logger.info(f"Downloaded: {filename} ({output_path.stat().st_size / 1e6:.1f} MB)")
                        return output_path
                    else:
                        logger.warning(f"Downloaded file is empty: {output_path}")
                        output_path.unlink(missing_ok=True)
                else:
                    # Check if response is HTML (error page)
                    if 'text/html' in content_type:
                        logger.debug(f"Got HTML response from {endpoint}, trying next...")
                        continue
            else:
                logger.warning(f"Endpoint {endpoint} returned status {resp.status_code}")
                
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout on {endpoint}")
        except Exception as e:
            logger.warning(f"Error with {endpoint}: {e}")
    
    # If all endpoints fail, try the legacy PREZIP pattern
    logger.info("Trying PREZIP directory listing...")
    return try_prezip_download(session, year, month, output_dir)


def try_prezip_download(session: requests.Session, year: int, month: int, output_dir: Path) -> Path:
    """Try to download from PREZIP directory listing."""
    prezip_url = "https://transtats.bts.gov/PREZIP/"
    
    try:
        resp = session.get(prezip_url, timeout=30)
        resp.raise_for_status()
        
        import re
        # Find links matching T-100 pattern for our year/month
        # Pattern: {id}_T_T100D_SEGMENT_ALL_CARRIER.zip
        links = re.findall(r'href="(/PREZIP/\d+_T_T100D_SEGMENT_ALL_CARRIER\.zip)"', resp.text)
        
        for link in links:
            full_url = f"https://transtats.bts.gov{link}"
            filename = link.split('/')[-1]
            
            logger.info(f"Found PREZIP file: {filename}")
            
            # Download it
            resp = session.get(full_url, timeout=120, stream=True)
            if resp.status_code == 200:
                output_path = output_dir / f"T_T100D_SEGMENT_ALL_CARRIER_{year}_{month:02d}.zip"
                with open(output_path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                if output_path.stat().st_size > 0:
                    logger.info(f"Downloaded from PREZIP: {output_path.name} ({output_path.stat().st_size / 1e6:.1f} MB)")
                    return output_path
                    
    except Exception as e:
        logger.warning(f"PREZIP download failed: {e}")
    
    return None


def main():
    parser = argparse.ArgumentParser(description="Download T-100 Domestic Segment data from BTS TranStats (direct HTTP)")
    parser.add_argument('--year', type=int, default=2024, help='Year to download (default: 2024)')
    parser.add_argument('--months', type=int, nargs='+', default=list(range(1, 13)), 
                        help='Months to download (default: 1-12)')
    parser.add_argument('--output-dir', type=Path, default=Path('data/raw'), 
                        help='Output directory (default: data/raw)')
    
    args = parser.parse_args()
    
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting T-100 direct download for {args.year}, months: {args.months}")
    logger.info(f"Output directory: {args.output_dir.absolute()}")
    
    session = create_session()
    
    downloaded_files = []
    failed_months = []
    
    for month in args.months:
        try:
            zip_path = download_t100_month(session, args.year, month, args.output_dir)
            if zip_path:
                downloaded_files.append(zip_path)
            else:
                failed_months.append(month)
            time.sleep(3)  # Be nice to the server
        except Exception as e:
            logger.error(f"Failed to download {args.year}-{month:02d}: {e}")
            failed_months.append(month)
    
    logger.info("=" * 50)
    logger.info(f"Download complete!")
    logger.info(f"Successful: {len(downloaded_files)} files")
    for f in downloaded_files:
        logger.info(f"  {f.name} ({f.stat().st_size / 1e6:.1f} MB)")
    
    if failed_months:
        logger.warning(f"Failed months: {failed_months}")
        logger.warning("Try manual download from:")
        logger.warning("https://www.transtats.bts.gov/DL_SelectFields.aspx?Table_ID=259&DBShortName=Air%20Carriers")


if __name__ == "__main__":
    main()