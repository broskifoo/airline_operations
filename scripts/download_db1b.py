#!/usr/bin/env python3
"""
Download DB1B Market and Coupon data from BTS TranStats.
Uses Selenium to automate the form submission.

Usage:
    python scripts/download_db1b.py --year 2024 --quarter 2 --type market --output-dir data/raw
    python scripts/download_db1b.py --year 2024 --quarter 3 --type coupon --output-dir data/raw
    python scripts/download_db1b.py --year 2024 --quarters 2 3 4 --type both --output-dir data/raw
"""

import argparse
import time
import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# DB1B URLs
DB1B_MARKET_URL = "https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FGJ"
DB1B_COUPON_URL = "https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FGI"

# Form field IDs for DB1B (standard TranStats form)
FIELD_IDS = {
    'geography': 'cboGeography',
    'year': 'cboYear',
    'period': 'cboPeriod',  # Quarter for DB1B
    'download_button': 'btnDownload',
    'select_all_fields': 'chkSelectAll',
}


def setup_driver(download_dir: Path, headless: bool = False) -> webdriver.Chrome:
    """Setup Chrome driver with download preferences."""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    
    # Set download directory
    prefs = {
        "download.default_directory": str(download_dir.absolute()),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(60)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def wait_for_download(download_dir: Path, timeout: int = 600) -> Path:
    """Wait for a new ZIP file to appear in download directory."""
    initial_files = set(download_dir.glob("*.zip"))
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        current_files = set(download_dir.glob("*.zip"))
        new_files = current_files - initial_files
        if new_files:
            time.sleep(10)  # Wait for download to complete
            newest = max(new_files, key=lambda f: f.stat().st_mtime)
            if newest.stat().st_size > 0:
                logger.info(f"Download complete: {newest.name} ({newest.stat().st_size / 1e6:.1f} MB)")
                return newest
        time.sleep(3)
    
    raise TimeoutError(f"Download timed out after {timeout} seconds")


def download_db1b_quarter(driver: webdriver.Chrome, wait: WebDriverWait,
                          url: str, year: int, quarter: int, 
                          data_type: str, download_dir: Path) -> Path:
    """Download DB1B Market or Coupon data for a specific year/quarter."""
    logger.info(f"Downloading DB1B {data_type} for {year} Q{quarter}...")
    
    driver.get(url)
    time.sleep(3)
    
    try:
        # Select Geography: "All" 
        geo_select = Select(wait.until(EC.presence_of_element_located((By.ID, FIELD_IDS['geography']))))
        for option in geo_select.options:
            if 'all' in option.text.lower() or option.get_attribute('value') == 'All':
                geo_select.select_by_visible_text(option.text)
                logger.info(f"Selected geography: {option.text}")
                break
        else:
            geo_select.select_by_index(0)
            logger.info(f"Selected geography (default): {geo_select.first_selected_option.text}")
        
        time.sleep(1)
        
        # Select Year
        year_select = Select(wait.until(EC.presence_of_element_located((By.ID, FIELD_IDS['year']))))
        year_select.select_by_visible_text(str(year))
        logger.info(f"Selected year: {year}")
        time.sleep(1)
        
        # Select Period (Quarter for DB1B)
        period_select = Select(wait.until(EC.presence_of_element_located((By.ID, FIELD_IDS['period']))))
        quarter_text = f"Quarter {quarter}"
        try:
            period_select.select_by_visible_text(quarter_text)
        except NoSuchElementException:
            # Try just the number
            period_select.select_by_value(str(quarter))
        logger.info(f"Selected quarter: {quarter_text}")
        time.sleep(1)
        
        # Select All Fields
        select_all = wait.until(EC.element_to_be_clickable((By.ID, FIELD_IDS['select_all_fields'])))
        if not select_all.is_selected():
            select_all.click()
            logger.info("Selected all fields")
        time.sleep(1)
        
        # Click Download
        download_btn = wait.until(EC.element_to_be_clickable((By.ID, FIELD_IDS['download_button'])))
        download_btn.click()
        logger.info("Download initiated...")
        
        # Wait for download to complete
        zip_path = wait_for_download(download_dir)
        
        # Rename to include year/quarter for clarity
        new_name = f"DB1B_{data_type.capitalize()}_{year}_Q{quarter}.zip"
        new_path = download_dir / new_name
        if new_path.exists():
            new_path.unlink()
        zip_path.rename(new_path)
        logger.info(f"Renamed to: {new_name}")
        
        return new_path
        
    except TimeoutException as e:
        logger.error(f"Timeout downloading {data_type} {year} Q{quarter}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error downloading {data_type} {year} Q{quarter}: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description="Download DB1B Market/Coupon data from BTS TranStats")
    parser.add_argument('--year', type=int, default=2024, help='Year to download (default: 2024)')
    parser.add_argument('--quarters', type=int, nargs='+', default=[2, 3, 4],
                        help='Quarters to download (default: 2 3 4)')
    parser.add_argument('--type', choices=['market', 'coupon', 'both'], default='both',
                        help='Data type to download (default: both)')
    parser.add_argument('--output-dir', type=Path, default=Path('data/raw'),
                        help='Output directory (default: data/raw)')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting DB1B download for {args.year}, quarters: {args.quarters}, type: {args.type}")
    logger.info(f"Output directory: {args.output_dir.absolute()}")
    
    driver = None
    try:
        driver = setup_driver(args.output_dir, headless=args.headless)
        wait = WebDriverWait(driver, 30)
        
        downloaded_files = []
        failed = []
        
        types_to_download = ['market', 'coupon'] if args.type == 'both' else [args.type]
        
        for data_type in types_to_download:
            url = DB1B_MARKET_URL if data_type == 'market' else DB1B_COUPON_URL
            
            for quarter in args.quarters:
                try:
                    zip_path = download_db1b_quarter(driver, wait, url, args.year, quarter, data_type, args.output_dir)
                    downloaded_files.append(zip_path)
                    # Be nice to the server
                    time.sleep(10)
                except Exception as e:
                    logger.error(f"Failed to download {data_type} {args.year} Q{quarter}: {e}")
                    failed.append(f"{data_type} Q{quarter}")
        
        logger.info("=" * 50)
        logger.info(f"Download complete!")
        logger.info(f"Successful: {len(downloaded_files)} files")
        for f in downloaded_files:
            logger.info(f"  {f.name} ({f.stat().st_size / 1e6:.1f} MB)")
        
        if failed:
            logger.warning(f"Failed: {failed}")
            logger.warning("You may need to download these manually from:")
            logger.warning(f"  Market: {DB1B_MARKET_URL}")
            logger.warning(f"  Coupon: {DB1B_COUPON_URL}")
        
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    main()