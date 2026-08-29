#!/usr/bin/env python3
"""Debug Selenium with correct TranStats URL."""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Try different URL patterns
URLS = [
    "https://www.transtats.bts.gov/DL_SelectFields.aspx?Table_ID=259&DBShortName=Air%20Carriers",
    "https://transtats.bts.gov/DL_SelectFields.aspx?Table_ID=259&DBShortName=Air%20Carriers",
    "https://www.transtats.bts.gov/Table.asp?Table_ID=259",
    "https://transtats.bts.gov/Table.asp?Table_ID=259",
]

def setup_driver(download_dir):
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    
    prefs = {
        "download.default_directory": str(download_dir),
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

for url in URLS:
    print(f"\n{'='*60}")
    print(f"Trying: {url}")
    print(f"{'='*60}")
    
    driver = setup_driver(".")
    wait = WebDriverWait(driver, 30)
    
    try:
        driver.get(url)
        time.sleep(3)
        
        print(f"Title: {driver.title}")
        print(f"Current URL: {driver.current_url}")
        
        # Check for select elements
        selects = driver.find_elements(By.TAG_NAME, "select")
        if selects:
            print(f"Found {len(selects)} SELECT elements:")
            for s in selects:
                print(f"  ID: {s.get_attribute('id')}, Name: {s.get_attribute('name')}")
        else:
            print("No SELECT elements found")
        
        # Check for download-related elements
        buttons = driver.find_elements(By.XPATH, "//input[@type='button' or @type='submit' or @type='image'] | //button | //a[contains(@href, 'download') or contains(@href, 'Download')]")
        if buttons:
            print(f"Found {len(buttons)} potential download elements:")
            for btn in buttons:
                print(f"  Tag: {btn.tag_name}, ID: {btn.get_attribute('id')}, Name: {btn.get_attribute('name')}, Text: {btn.text[:50]}, Href: {btn.get_attribute('href')[:80] if btn.get_attribute('href') else 'N/A'}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()