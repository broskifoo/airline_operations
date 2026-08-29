#!/usr/bin/env python3
"""
Download T-100 Segment data using the skynet R package approach.
Ported from: https://github.com/ropensci/skynet/blob/HEAD/R/download_t100.R

This properly handles ASP.NET viewstate and event validation.
"""

import requests
import re
import time
import logging
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# URLs from skynet - note the different gnoyr_VQ parameters for market vs segment
SEGMENT_URL = "https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FIM&QO_fu146_anzr=Nv4%25Pn44vr45"
MARKET_URL = "https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FIL&QO_fu146_anzr=Nv4%20Pn44vr45"
POST_URL = "https://www.transtats.bts.gov/DL_SelectFields.aspx"


def create_session():
    """Create session with retry logic."""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    return session


def extract_viewstate(html: str) -> dict:
    """Extract ASP.NET viewstate fields from HTML."""
    viewstate = {}
    
    # __VIEWSTATE
    match = re.search(r'id="__VIEWSTATE"\s+value="([^"]*)"', html)
    if match:
        viewstate['__VIEWSTATE'] = match.group(1)
    
    # __VIEWSTATEGENERATOR
    match = re.search(r'id="__VIEWSTATEGENERATOR"\s+value="([^"]*)"', html)
    if match:
        viewstate['__VIEWSTATEGENERATOR'] = match.group(1)
    
    # __EVENTVALIDATION
    match = re.search(r'id="__EVENTVALIDATION"\s+value="([^"]*)"', html)
    if match:
        viewstate['__EVENTVALIDATION'] = match.group(1)
    
    return viewstate


def download_t100_segment(year: int, output_dir: Path, period: str = "All") -> Path:
    """
    Download T-100 Segment data for a given year.
    
    Args:
        year: Year to download (e.g., 2024)
        output_dir: Directory to save the ZIP file
        period: "All" for full year, or specific month "1"-"12"
    
    Returns:
        Path to downloaded ZIP file
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    session = create_session()
    
    logger.info(f"Fetching form for T-100 Segment {year}...")
    
    # Step 1: GET the form page to extract viewstate
    resp = session.get(SEGMENT_URL, timeout=30)
    resp.raise_for_status()
    
    viewstate = extract_viewstate(resp.text)
    logger.info(f"Extracted viewstate keys: {list(viewstate.keys())}")
    
    if not viewstate.get('__VIEWSTATE'):
        logger.error("Failed to extract __VIEWSTATE")
        logger.debug(f"HTML preview: {resp.text[:2000]}")
        raise ValueError("Could not extract viewstate from form page")
    
    # Step 2: POST the download request
    post_data = {
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        '__LASTFOCUS': '',
        '__VIEWSTATE': viewstate['__VIEWSTATE'],
        '__VIEWSTATEGENERATOR': viewstate.get('__VIEWSTATEGENERATOR', ''),
        '__EVENTVALIDATION': viewstate.get('__EVENTVALIDATION', ''),
        'txtSearch': '',
        'btnDownload': 'Download',
        'cboGeography': 'All',
        'cboYear': str(year),
        'cboPeriod': period,
        'chkAllVars': 'on',
        'UNIQUE_CARRIER': 'on',
        'UNIQUE_CARRIER_NAME': 'on',
        'ORIGIN_AIRPORT_ID': 'on',
        'ORIGIN': 'on',
        'DEST_AIRPORT_ID': 'on',
        'DEST': 'on',
        'MONTH': 'on',
        # These are the field selections from skynet
        'AIRCRAFT_TYPE': 'on',
        'SERVICE_CLASS': 'on',
        'DEPARTURES_PERFORMED': 'on',
        'DEPARTURES_SCHEDULED': 'on',
        'AVAILABLE_SEATS': 'on',
        'PASSENGERS': 'on',
        'FREIGHT': 'on',
        'MAIL': 'on',
        'DISTANCE': 'on',
        'RAMP_TO_RAMP': 'on',
        'AIRBORNE': 'on',
        'AVAILABLE_CAPACITY': 'on',
    }
    
    # Add the query parameters to the POST URL
    params = {
        'gnoyr_VQ': 'FIM',
        'QO_fu146_anzr': 'Nv4+Pn44vr45'
    }
    
    logger.info(f"Submitting download request for {year} (period={period})...")
    
    resp = session.post(POST_URL, data=post_data, params=params, timeout=180, stream=True)
    logger.info(f"POST status: {resp.status_code}")
    logger.info(f"Response Content-Type: {resp.headers.get('Content-Type', 'N/A')}")
    logger.info(f"Response Content-Disposition: {resp.headers.get('Content-Disposition', 'N/A')}")
    
    if resp.status_code != 200:
        logger.error(f"Download failed with status {resp.status_code}")
        logger.error(f"Response: {resp.text[:500]}")
        raise ValueError(f"Download failed: {resp.status_code}")
    
    content_type = resp.headers.get('Content-Type', '').lower()
    content_disp = resp.headers.get('Content-Disposition', '')
    
    if 'zip' in content_type or 'octet-stream' in content_type or 'attachment' in content_disp.lower():
        # Extract filename from Content-Disposition or create one
        filename = f"T_T100D_SEGMENT_ALL_CARRIER_{year}.zip"
        if 'filename=' in content_disp:
            match = re.search(r'filename[*]?=([^;]+)', content_disp)
            if match:
                filename = match.group(1).strip('"')
        
        output_path = output_dir / filename
        
        with open(output_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        if output_path.stat().st_size > 0:
            logger.info(f"Downloaded: {filename} ({output_path.stat().st_size / 1e6:.1f} MB)")
            return output_path
        else:
            logger.warning("Downloaded file is empty")
            output_path.unlink(missing_ok=True)
            raise ValueError("Empty download")
    else:
        # Check if response is HTML (error page)
        if 'html' in content_type:
            logger.error("Received HTML instead of ZIP - likely an error page")
            logger.debug(f"Response preview: {resp.text[:1000]}")
        raise ValueError(f"Unexpected content type: {content_type}")


def download_t100_monthly(year: int, output_dir: Path) -> list:
    """Download T-100 Segment data month by month (more reliable for large datasets)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded = []
    failed = []
    
    for month in range(1, 13):
        try:
            zip_path = download_t100_segment(year, output_dir, period=str(month))
            downloaded.append(zip_path)
            logger.info(f"  Month {month}: SUCCESS")
            time.sleep(5)  # Be nice to server
        except Exception as e:
            logger.error(f"  Month {month}: FAILED - {e}")
            failed.append(month)
    
    return downloaded, failed


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Download T-100 Segment data using viewstate method")
    parser.add_argument('--year', type=int, default=2024, help='Year to download')
    parser.add_argument('--output-dir', type=Path, default=Path('data/raw'), help='Output directory')
    parser.add_argument('--monthly', action='store_true', help='Download month by month instead of full year')
    
    args = parser.parse_args()
    
    if args.monthly:
        downloaded, failed = download_t100_monthly(args.year, args.output_dir)
    else:
        try:
            zip_path = download_t100_segment(args.year, args.output_dir)
            downloaded = [zip_path]
            failed = []
        except Exception as e:
            logger.error(f"Full year download failed: {e}")
            downloaded = []
            failed = list(range(1, 13))
    
    logger.info("=" * 50)
    logger.info(f"Download complete!")
    logger.info(f"Successful: {len(downloaded)} files")
    for f in downloaded:
        logger.info(f"  {f.name} ({f.stat().st_size / 1e6:.1f} MB)")
    if failed:
        logger.warning(f"Failed months: {failed}")


if __name__ == "__main__":
    main()