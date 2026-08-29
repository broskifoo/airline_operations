import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request
import shutil

OUTPUT_DIR = Path("data/raw")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def download_with_progress(url, output_file, chunk_size=1024*1024):
    """Download with progress bar."""
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urlopen(req, timeout=60) as response:
            total = response.length
            if total is None:
                print(f"  Downloading (size unknown)...")
            else:
                print(f"  Size: {total / 1024 / 1024:.1f} MB")
            
            downloaded = 0
            with open(output_file, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded * 100 / total
                        sys.stdout.write(f"\r  Progress: {pct:.1f}% ({downloaded / 1024 / 1024:.1f} MB)")
                        sys.stdout.flush()
            print(f"\n  [OK] Saved: {output_file.name} ({downloaded / 1024 / 1024:.1f} MB)")
            return True
    except Exception as e:
        print(f"\n  [FAIL] {e}")
        if output_file.exists():
            output_file.unlink()
        return False


# DB1B Market Q3, Q4
print("=" * 60)
print("DOWNLOADING DB1B MARKET Q3, Q4")
print("=" * 60)

for quarter in [3, 4]:
    url = f"https://transtats.bts.gov/PREZIP/Origin_and_Destination_Survey_DB1BMarket_2024_{quarter}.zip"
    output_file = OUTPUT_DIR / f"DB1B_Market_2024_Q{quarter}.zip"
    print(f"\nQ{quarter}: {url}")
    if output_file.exists():
        print(f"  Already exists: {output_file.name} ({output_file.stat().st_size / 1024 / 1024:.1f} MB)")
        continue
    download_with_progress(url, output_file)

# DB1B Coupon Q2, Q3, Q4
print("\n" + "=" * 60)
print("DOWNLOADING DB1B COUPON Q2, Q3, Q4")
print("=" * 60)

# Try different URL patterns for coupon
coupon_urls = {
    2: [
        "https://transtats.bts.gov/PREZIP/Origin_and_Destination_Survey_DB1BCoupon_2024_2.zip",
        "https://transtats.bts.gov/PREZIP/Origin_and_Destination_Survey_DB1BCoupon_2024_Q2.zip",
    ],
    3: [
        "https://transtats.bts.gov/PREZIP/Origin_and_Destination_Survey_DB1BCoupon_2024_3.zip",
        "https://transtats.bts.gov/PREZIP/Origin_and_Destination_Survey_DB1BCoupon_2024_Q3.zip",
    ],
    4: [
        "https://transtats.bts.gov/PREZIP/Origin_and_Destination_Survey_DB1BCoupon_2024_4.zip",
        "https://transtats.bts.gov/PREZIP/Origin_and_Destination_Survey_DB1BCoupon_2024_Q4.zip",
    ],
}

for quarter in [2, 3, 4]:
    output_file = OUTPUT_DIR / f"DB1B_Coupon_2024_Q{quarter}.zip"
    if output_file.exists():
        print(f"\nQ{quarter} Coupon: Already exists ({output_file.stat().st_size / 1024 / 1024:.1f} MB)")
        continue
    
    print(f"\nQ{quarter} Coupon: Trying URLs...")
    for url in coupon_urls[quarter]:
        print(f"  Trying: {url}")
        if download_with_progress(url, output_file):
            break
    else:
        print(f"  [FAIL] All URLs failed for Q{quarter} Coupon")

print("\n" + "=" * 60)
print("DOWNLOAD COMPLETE")
print("=" * 60)