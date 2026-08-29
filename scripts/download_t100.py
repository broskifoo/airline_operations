#!/usr/bin/env python3
"""
Download T-100 Domestic Segment (All Carriers) data from BTS TranStats.
Uses Selenium to automate the form submission.

Usage:
    python scripts/download_t100.py --year 2024 --output-dir data/raw
    python scripts/download_t100.py --year 2024 --months 1 2 3 --output-dir data/raw
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

# T-100 Domestic Segment (All Carriers) download URL
DOWNLOAD_URL = "https://www.transtats.bts.gov/DL_SelectFields.aspx?QO_fu146_anzr=Nv4+Pn44vr45&gnoyr_VQ=GEE"

# Form field IDs (based on TranStats standard form)
FIELD_IDS = {
    'geography': 'cboGeography',
    'year': 'cboYear',
    'period': 'cboPeriod',
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
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(60)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def wait_for_download(download_dir: Path, timeout: int = 300) -> Path:
    """Wait for a new ZIP file to appear in download directory."""
    initial_files = set(download_dir.glob("*.zip"))
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        current_files = set(download_dir.glob("*.zip"))
        new_files = current_files - initial_files
        if new_files:
            # Wait a bit more for download to complete
            time.sleep(5)
            # Return the newest file
            newest = max(new_files, key=lambda f: f.stat().st_mtime)
            if newest.stat().st_size > 0:
                logger.info(f"Download complete: {newest.name} ({newest.stat().st_size / 1e6:.1f} MB)")
                return newest
        time.sleep(2)
    
    raise TimeoutError(f"Download timed out after {timeout} seconds")


def download_t100_month(driver: webdriver.Chrome, wait: WebDriverWait, 
                        year: int, month: int, download_dir: Path) -> Path:
    """Download T-100 data for a specific year/month."""
    logger.info(f"Downloading T-100 for {year}-{month:02d}...")
    
    # Navigate to download page
    driver.get(DOWNLOAD_URL)
    time.sleep(3)  # Let page load
    
    try:
        # Select Geography: "All" (usually first option or value="All")
        geo_select = Select(wait.until(EC.presence_of_element_located((By.ID, FIELD_IDS['geography']))))
        # Try to select "All" - may need to inspect actual option values
        for option in geo_select.options:
            if 'all' in option.text.lower() or option.get_attribute('value') == 'All':
                geo_select.select_by_visible_text(option.text)
                logger.info(f"Selected geography: {option.text}")
                break
        else:
            geo_select.select_by_index(0)  # Default to first option
            logger.info(f"Selected geography (default): {geo_select.first_selected_option.text}")
        
        time.sleep(1)
        
        # Select Year
        year_select = Select(wait.until(EC.presence_of_element_located((By.ID, FIELD_IDS['year']))))
        year_select.select_by_visible_text(str(year))
        logger.info(f"Selected year: {year}")
        time.sleep(1)
        
        # Select Period (Month)
        period_select = Select(wait.until(EC.presence_of_element_located((By.ID, FIELD_IDS['period']))))
        # Months are typically "January", "February", etc. or "1", "2", etc.
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        month_name = month_names[month - 1]
        try:
            period_select.select_by_visible_text(month_name)
        except NoSuchElementException:
            # Try numeric
            period_select.select_by_value(str(month))
        logger.info(f"Selected month: {month_name}")
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
        
        # Rename to include year/month for clarity
        new_name = f"T_T100D_SEGMENT_ALL_CARRIER_{year}_{month:02d}.zip"
        new_path = download_dir / new_name
        if new_path.exists():
            new_path.unlink()
        zip_path.rename(new_path)
        logger.info(f"Renamed to: {new_name}")
        
        return new_path
        
    except TimeoutException as e:
        logger.error(f"Timeout downloading {year}-{month:02d}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error downloading {year}-{month:02d}: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description="Download T-100 Domestic Segment data from BTS TranStats")
    parser.add_argument('--year', type=int, default=2024, help='Year to download (default: 2024)')
    parser.add_argument('--months', type=int, nargs='+', default=list(range(1, 13)), 
                        help='Months to download (default: 1-12)')
    parser.add_argument('--output-dir', type=Path, default=Path('data/raw'), 
                        help='Output directory (default: data/raw)')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting T-100 download for {args.year}, months: {args.months}")
    logger.info(f"Output directory: {args.output_dir.absolute()}")
    
    driver = None
    try:
        driver = setup_driver(args.output_dir, headless=args.headless)
        wait = WebDriverWait(driver, 30)
        
        downloaded_files = []
        failed_months = []
        
        for month in args.months:
            try:
                zip_path = download_t100_month(driver, wait, args.year, month, args.output_dir)
                downloaded_files.append(zip_path)
                # Be nice to the server
                time.sleep(5)
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
            logger.warning("You may need to download these manually from:")
            logger.warning(DOWNLOAD_URL)
        
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    main()