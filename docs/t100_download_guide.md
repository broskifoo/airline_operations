# T-100 Segment Data Download Guide

## Overview
The T-100 Domestic Segment (All Carriers) data is required for revenue modeling in the Airline Operations & Revenue Analytics platform. This data provides carrier-level segment data including seats, departures, passengers, and distance - essential for calculating load factors and operating costs.

## Automated Download (Recommended)

### Prerequisites
```bash
pip install selenium>=4.15.0
# Also need ChromeDriver matching your Chrome version
```

### Run Download Script
```bash
# Download all 12 months of 2024
python scripts/download_t100.py --year 2024 --output-dir data/raw

# Download specific months
python scripts/download_t100.py --year 2024 --months 1 2 3 --output-dir data/raw

# Run headless (no browser UI)
python scripts/download_t100.py --year 2024 --headless
```

### Output
Files will be saved as:
```
data/raw/T_T100D_SEGMENT_ALL_CARRIER_2024_01.zip
data/raw/T_T100D_SEGMENT_ALL_CARRIER_2024_02.zip
...
data/raw/T_T100D_SEGMENT_ALL_CARRIER_2024_12.zip
```

## Manual Download (Alternative)

If automated download fails, follow these steps:

### 1. Navigate to Download Page
Open browser to:
```
https://www.transtats.bts.gov/DL_SelectFields.aspx?QO_fu146_anzr=Nv4+Pn44vr45&gnoyr_VQ=GEE
```

### 2. Configure Query
- **Geography**: Select "All" 
- **Year**: Select "2024"
- **Period**: Select month (January through December)
- **Fields**: Click "Select All Fields" checkbox
- **Format**: CSV (default)

### 3. Download
Click "Download" button. A ZIP file will download with a name like:
`896816367_T_T100D_SEGMENT_ALL_CARRIER.zip`

### 4. Rename and Move
Rename the file to include year/month:
`T_T100D_SEGMENT_ALL_CARRIER_2024_01.zip`

Move to:
```
data/raw/T_T100D_SEGMENT_ALL_CARRIER_2024_01.zip
```

Repeat for all 12 months.

## Data Structure

The T-100 ZIP contains a CSV with these key columns:
| Column | Description |
|--------|-------------|
| UNIQUE_CARRIER | Carrier code (e.g., WN, DL, AA) |
| YEAR | Year (2024) |
| MONTH | Month (1-12) |
| ORIGIN | Origin airport (3-letter IATA) |
| DEST | Destination airport (3-letter IATA) |
| SERVICE_CLASS | F=Scheduled Passenger, G=All Cargo, etc. |
| AIRCRAFT_TYPE | Aircraft type code |
| DEPARTURES_PERFORMED | Actual departures |
| DEPARTURES_SCHEDULED | Scheduled departures |
| AVAILABLE_SEATS | Seats available for sale |
| PASSENGERS | Passengers transported |
| DISTANCE | Segment distance (miles) |
| AVAILABLE_CAPACITY | Payload capacity (lbs) |
| FREIGHT | Freight transported (lbs) |
| MAIL | Mail transported (lbs) |

## Verification

After downloading, verify the data loads correctly:
```bash
python -c "
from src.data_loader import find_t100_files, load_t100_all_months
files = find_t100_files()
print(f'Found {len(files)} files:')
for f in files:
    print(f'  {f.name}')
df = load_t100_all_months()
print(f'Total rows: {len(df):,}')
print(f'Columns: {list(df.columns)}')
"
```

## Running Full ETL with T-100

Once T-100 data is downloaded:
```bash
python src/etl_pipeline.py --full
```

This will:
1. Load and clean T-100 data
2. Build FACT_REVENUE with modeled revenue/profit estimates
3. Run validation on all tables
4. Generate updated validation report

## Troubleshooting

### Selenium Issues
- Ensure ChromeDriver version matches Chrome browser version
- Try running with `--headless` flag
- Check download directory permissions

### Missing Data
- Some months may not be available yet (2-3 month lag)
- Check "Latest Available Data" on TranStats table info page
- Adjust months parameter accordingly

### Large Files
- Each monthly ZIP is ~10-50 MB
- Extracted CSV can be 100-500 MB
- Ensure sufficient disk space (2-5 GB for full year)

## Manual Verification Query

To verify data quality in the downloaded CSV:
```python
import pandas as pd

df = pd.read_csv('data/raw/extracted/T_T100D_SEGMENT_ALL_CARRIER_2024_01.csv')
print(df.columns.tolist())
print(df.dtypes)
print(df[['UNIQUE_CARRIER', 'ORIGIN', 'DEST', 'PASSENGERS', 'AVAILABLE_SEATS', 'DISTANCE']].head())
print(f"Unique carriers: {df['UNIQUE_CARRIER'].nunique()}")
print(f"Unique routes: {(df['ORIGIN'] + '-' + df['DEST']).nunique()}")
print(f"Date range: {df['YEAR'].min()}-{df['MONTH'].min()} to {df['YEAR'].max()}-{df['MONTH'].max()}")
```