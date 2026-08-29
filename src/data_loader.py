"""
Data Loader Module
Handles reading raw data files with chunking support for large files.
"""
import pandas as pd
from pathlib import Path
from typing import Iterator, Optional, List
import duckdb
import zipfile
import glob
import logging
from .config import (
    KAGGLE_2024_FULL, KAGGLE_2024_SAMPLE, KAGGLE_DICT,
    DB1B_MARKET_Q1, DB1B_MARKET_Q2, DB1B_MARKET_Q3, DB1B_MARKET_Q4,
    DB1B_COUPON_Q1, DB1B_COUPON_Q2, DB1B_COUPON_Q3, DB1B_COUPON_Q4,
    DB1B_MARKET_ALL, DB1B_COUPON_ALL,
    T100_SEGMENT_DIR, T100_SEGMENT_PATTERN,
    KAGGLE_COLUMN_RENAME,
    STAGING_DIR
)

logger = logging.getLogger(__name__)


def load_kaggle_sample(nrows: Optional[int] = None) -> pd.DataFrame:
    """Load Kaggle 2024 sample dataset."""
    df = pd.read_csv(KAGGLE_2024_SAMPLE, nrows=nrows, low_memory=False)
    df = df.rename(columns=KAGGLE_COLUMN_RENAME)
    return df


def load_kaggle_full_chunked(chunksize: int = 100000) -> Iterator[pd.DataFrame]:
    """Load Kaggle 2024 full dataset in chunks."""
    for chunk in pd.read_csv(KAGGLE_2024_FULL, chunksize=chunksize, low_memory=False):
        chunk = chunk.rename(columns=KAGGLE_COLUMN_RENAME)
        yield chunk


def load_kaggle_full_duckdb() -> duckdb.DuckDBPyRelation:
    """Load Kaggle 2024 full dataset directly into DuckDB for SQL queries."""
    conn = duckdb.connect()
    conn.execute(f"""
        CREATE OR REPLACE VIEW stg_flights AS
        SELECT * FROM read_csv_auto('{KAGGLE_2024_FULL}', 
            header=true, 
            sample_size=10000,
            types={{
                'year': 'INTEGER', 'month': 'INTEGER', 'day_of_month': 'INTEGER',
                'day_of_week': 'INTEGER', 'op_unique_carrier': 'VARCHAR',
                'op_carrier_fl_num': 'DOUBLE', 'origin': 'VARCHAR',
                'origin_city_name': 'VARCHAR', 'origin_state_nm': 'VARCHAR',
                'dest': 'VARCHAR', 'dest_city_name': 'VARCHAR', 'dest_state_nm': 'VARCHAR',
                'crs_dep_time': 'INTEGER', 'dep_time': 'DOUBLE', 'dep_delay': 'DOUBLE',
                'taxi_out': 'DOUBLE', 'wheels_off': 'DOUBLE', 'wheels_on': 'DOUBLE',
                'taxi_in': 'DOUBLE', 'crs_arr_time': 'INTEGER', 'arr_time': 'DOUBLE',
                'arr_delay': 'DOUBLE', 'cancelled': 'INTEGER', 'cancellation_code': 'VARCHAR',
                'diverted': 'INTEGER', 'crs_elapsed_time': 'DOUBLE', 'actual_elapsed_time': 'DOUBLE',
                'air_time': 'DOUBLE', 'distance': 'DOUBLE', 'carrier_delay': 'INTEGER',
                'weather_delay': 'INTEGER', 'nas_delay': 'INTEGER', 'security_delay': 'INTEGER',
                'late_aircraft_delay': 'INTEGER'
            }}
        )
    """)
    return conn.table("stg_flights")


def load_db1b_market_chunked(chunksize: int = 100000) -> Iterator[pd.DataFrame]:
    """Load DB1B Market data from all 4 quarters in chunks."""
    for market_file in DB1B_MARKET_ALL:
        if market_file.exists():
            logger.info(f"Loading DB1B Market from {market_file.name}")
            for chunk in pd.read_csv(market_file, chunksize=chunksize, low_memory=False):
                chunk = chunk.loc[:, ~chunk.columns.str.contains('^Unnamed')]
                yield chunk
        else:
            logger.warning(f"DB1B Market file not found: {market_file}")


def load_db1b_coupon_chunked(chunksize: int = 100000) -> Iterator[pd.DataFrame]:
    """Load DB1B Coupon data from all 4 quarters in chunks."""
    for coupon_file in DB1B_COUPON_ALL:
        if coupon_file.exists():
            logger.info(f"Loading DB1B Coupon from {coupon_file.name}")
            for chunk in pd.read_csv(coupon_file, chunksize=chunksize, low_memory=False):
                chunk = chunk.loc[:, ~chunk.columns.str.contains('^Unnamed')]
                yield chunk
        else:
            logger.warning(f"DB1B Coupon file not found: {coupon_file}")


def load_db1b_market_duckdb() -> duckdb.DuckDBPyRelation:
    """Load DB1B Market (all quarters) into DuckDB."""
    conn = duckdb.connect()
    files = [str(f) for f in DB1B_MARKET_ALL if f.exists()]
    if not files:
        raise FileNotFoundError("No DB1B Market files found")
    file_list = "', '".join(files)
    conn.execute(f"""
        CREATE OR REPLACE VIEW stg_db1b_market AS
        SELECT * FROM read_csv_auto(['{file_list}'],
            header=true,
            sample_size=10000
        )
    """)
    return conn.table("stg_db1b_market")


def load_db1b_coupon_duckdb() -> duckdb.DuckDBPyRelation:
    """Load DB1B Coupon (all quarters) into DuckDB."""
    conn = duckdb.connect()
    files = [str(f) for f in DB1B_COUPON_ALL if f.exists()]
    if not files:
        raise FileNotFoundError("No DB1B Coupon files found")
    file_list = "', '".join(files)
    conn.execute(f"""
        CREATE OR REPLACE VIEW stg_db1b_coupon AS
        SELECT * FROM read_csv_auto(['{file_list}'],
            header=true,
            sample_size=10000
        )
    """)
    return conn.table("stg_db1b_coupon")


def load_data_dictionary() -> pd.DataFrame:
    """Load Kaggle data dictionary."""
    return pd.read_csv(KAGGLE_DICT)


def save_parquet(df: pd.DataFrame, path: Path, partition_cols: Optional[List[str]] = None, mode: str = "overwrite"):
    """Save DataFrame to Parquet with optional partitioning."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if partition_cols:
        if mode == "append":
            df.to_parquet(path, partition_cols=partition_cols, index=False, existing_data_behavior="delete_matching")
        else:
            df.to_parquet(path, partition_cols=partition_cols, index=False)
    else:
        if mode == "append" and path.exists():
            # For non-partitioned, read existing and combine
            existing = read_parquet(path)
            combined = pd.concat([existing, df], ignore_index=True)
            combined.to_parquet(path, index=False)
            print(f"Appended {len(df):,} rows to {path} (total: {len(combined):,})")
        else:
            df.to_parquet(path, index=False)
            print(f"Saved {len(df):,} rows to {path}")


def read_parquet(path: Path) -> pd.DataFrame:
    """Read Parquet file."""
    return pd.read_parquet(path)


def get_duckdb_connection() -> duckdb.DuckDBPyConnection:
    """Get a DuckDB connection with staging views registered."""
    conn = duckdb.connect()
    # Register views for staged data
    return conn


def find_t100_files(t100_dir: Path = None) -> List[Path]:
    """Find all T-100 segment ZIP files in the raw data directory."""
    if t100_dir is None:
        t100_dir = T100_SEGMENT_DIR
    pattern = str(t100_dir / T100_SEGMENT_PATTERN)
    files = sorted(glob.glob(pattern))
    return [Path(f) for f in files]


def extract_t100_zip(zip_path: Path, extract_dir: Path = None) -> Path:
    """Extract T-100 ZIP file and return path to CSV."""
    if extract_dir is None:
        extract_dir = zip_path.parent / "extracted"
    extract_dir.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(zip_path, 'r') as zf:
        # Find CSV file in zip
        csv_files = [f for f in zf.namelist() if f.endswith('.csv')]
        if not csv_files:
            raise ValueError(f"No CSV file found in {zip_path}")
        csv_file = csv_files[0]
        zf.extract(csv_file, extract_dir)
        return extract_dir / csv_file


def load_t100_segment(zip_path: Path) -> pd.DataFrame:
    """Load T-100 Segment data from ZIP file."""
    extract_dir = zip_path.parent / "extracted"
    csv_path = extract_t100_zip(zip_path, extract_dir)
    
    logger.info(f"Loading T-100 from {csv_path}")
    df = pd.read_csv(csv_path, low_memory=False)
    logger.info(f"Loaded {len(df):,} rows from {zip_path.name}")
    return df


def load_t100_all_months(t100_dir: Path = None) -> pd.DataFrame:
    """Load and concatenate all T-100 segment files for a year."""
    files = find_t100_files(t100_dir)
    if not files:
        logger.warning(f"No T-100 files found in {t100_dir or T100_SEGMENT_DIR}")
        return pd.DataFrame()
    
    logger.info(f"Found {len(files)} T-100 files")
    dfs = []
    for f in files:
        try:
            df = load_t100_segment(f)
            dfs.append(df)
        except Exception as e:
            logger.error(f"Failed to load {f.name}: {e}")
    
    if dfs:
        combined = pd.concat(dfs, ignore_index=True)
        logger.info(f"Combined T-100 data: {len(combined):,} rows")
        return combined
    return pd.DataFrame()