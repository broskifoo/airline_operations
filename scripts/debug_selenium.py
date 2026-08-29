#!/usr/bin/env python3
"""Debug Selenium to find actual form elements."""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

DOWNLOAD_URL = "https://www.transtats.bts.gov/DL_SelectFields.aspx?Table_ID=259&DBShortName=Air%20Carriers"

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

driver = setup_driver(".")
wait = WebDriverWait(driver, 30)

try:
    print("Loading page...")
    driver.get(DOWNLOAD_URL)
    time.sleep(5)
    
    print("\n=== Page Title ===")
    print(driver.title)
    
    print("\n=== All SELECT elements ===")
    selects = driver.find_elements(By.TAG_NAME, "select")
    for s in selects:
        print(f"  ID: {s.get_attribute('id')}, Name: {s.get_attribute('name')}")
        options = s.find_elements(By.TAG_NAME, "option")
        for opt in options[:5]:
            print(f"    Option: {opt.get_attribute('value')} = {opt.text}")
        if len(options) > 5:
            print(f"    ... and {len(options)-5} more")
    
    print("\n=== All INPUT elements (type=button, submit, checkbox) ===")
    inputs = driver.find_elements(By.XPATH, "//input[@type='button' or @type='submit' or @type='checkbox' or @type='image']")
    for inp in inputs:
        print(f"  ID: {inp.get_attribute('id')}, Name: {inp.get_attribute('name')}, Type: {inp.get_attribute('type')}, Value: {inp.get_attribute('value')}")
    
    print("\n=== All BUTTON elements ===")
    buttons = driver.find_elements(By.TAG_NAME, "button")
    for btn in buttons:
        print(f"  ID: {btn.get_attribute('id')}, Name: {btn.get_attribute('name')}, Text: {btn.text}")
    
    print("\n=== All A elements with 'download' in text/href ===")
    links = driver.find_elements(By.XPATH, "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'download') or contains(@href, 'download')]")
    for link in links:
        print(f"  ID: {link.get_attribute('id')}, Text: {link.text}, Href: {link.get_attribute('href')}")
    
    print("\n=== Form elements ===")
    forms = driver.find_elements(By.TAG_NAME, "form")
    for form in forms:
        print(f"  Form action: {form.get_attribute('action')}, method: {form.get_attribute('method')}")
        inputs = form.find_elements(By.TAG_NAME, "input")
        for inp in inputs:
            print(f"    Input: {inp.get_attribute('id')} / {inp.get_attribute('name')} = {inp.get_attribute('value')}")
    
    print("\n=== Page source (first 5000 chars) ===")
    print(driver.page_source[:5000])
    
    input("\nPress Enter to close browser...")
    
finally:
    driver.quit()