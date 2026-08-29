from pathlib import Path
from urllib.request import urlretrieve

# Create data/raw folder if it doesn't exist
OUTPUT_DIR = Path("data/raw")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Quarters we need
quarters = [2, 3, 4]

BASE_URL = (
    "https://transtats.bts.gov/PREZIP/"
    "Origin_and_Destination_Survey_DB1BMarket_2024_{}.zip"
)

for quarter in quarters:
    url = BASE_URL.format(quarter)

    # Desired filename for your project
    output_file = OUTPUT_DIR / f"DB1B_Market_2024_Q{quarter}.zip"

    print(f"\nDownloading Q{quarter}...")
    print(f"From: {url}")

    try:
        urlretrieve(url, output_file)
        print(f"[OK] Saved: {output_file}")

    except Exception as e:
        print(f"[FAIL] Failed to download Q{quarter}")
        print(e)

print("\nAll downloads completed!")