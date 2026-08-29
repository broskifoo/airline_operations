"""
Utility Functions
Common helpers for the airline analytics project.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_logging(log_file: Optional[Path] = None, level: int = logging.INFO):
    """Setup logging to console and optionally file."""
    global logger
    logger = logging.getLogger("airline_analytics")
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(ch)
    
    # File handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(fh)
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """Get logger instance."""
    return logging.getLogger(name or "airline_analytics")


def timer(func):
    """Decorator to time function execution."""
    import time
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logger.info(f"{func.__name__} completed in {elapsed:.2f}s")
        return result
    return wrapper


def save_json(data: Dict[str, Any], path: Path):
    """Save dictionary as JSON with datetime handling."""
    path.parent.mkdir(parents=True, exist_ok=True)
    
    def default_serializer(obj):
        if isinstance(obj, (pd.Timestamp, datetime)):
            return obj.isoformat()
        if isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, default=default_serializer)
    logger.info(f"Saved JSON to {path}")


def load_json(path: Path) -> Dict[str, Any]:
    """Load JSON file."""
    with open(path, 'r') as f:
        return json.load(f)


def memory_usage_mb(df: pd.DataFrame) -> float:
    """Get DataFrame memory usage in MB."""
    return df.memory_usage(deep=True).sum() / 1024**2


def optimize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Optimize DataFrame dtypes for memory efficiency."""
    df = df.copy()
    
    for col in df.columns:
        if df[col].dtype == 'object':
            # Try to convert to category if low cardinality
            nunique = df[col].nunique()
            if nunique / len(df) < 0.5:  # Less than 50% unique
                df[col] = df[col].astype('category')
        elif df[col].dtype == 'int64':
            # Downcast integers
            df[col] = pd.to_numeric(df[col], downcast='integer')
        elif df[col].dtype == 'float64':
            # Downcast floats
            df[col] = pd.to_numeric(df[col], downcast='float')
    
    return df


def print_df_info(df: pd.DataFrame, name: str = "DataFrame"):
    """Print DataFrame info summary."""
    print(f"\n{'='*50}")
    print(f"{name} Info")
    print(f"{'='*50}")
    print(f"Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"Memory: {memory_usage_mb(df):.1f} MB")
    print(f"\nDtypes:")
    print(df.dtypes.value_counts())
    print(f"\nMissing values:")
    missing = df.isnull().sum()
    missing = missing[missing > 0].sort_values(ascending=False)
    if len(missing) > 0:
        print(missing.to_string())
    else:
        print("None")
    print(f"{'='*50}\n")


def chunk_dataframe(df: pd.DataFrame, chunk_size: int = 100000) -> List[pd.DataFrame]:
    """Split DataFrame into chunks."""
    return [df[i:i+chunk_size] for i in range(0, len(df), chunk_size)]


def safe_divide(numerator: pd.Series, denominator: pd.Series, fill_value: float = 0.0) -> pd.Series:
    """Safe division with fill for divide-by-zero."""
    result = numerator / denominator.replace(0, np.nan)
    return result.fillna(fill_value)


def percentile_rank(series: pd.Series) -> pd.Series:
    """Calculate percentile rank (0-100)."""
    return series.rank(pct=True) * 100


def winsorize(series: pd.Series, lower: float = 0.01, upper: float = 0.99) -> pd.Series:
    """Winsorize series at given percentiles."""
    lower_bound = series.quantile(lower)
    upper_bound = series.quantile(upper)
    return series.clip(lower_bound, upper_bound)


def add_surrogate_key(df: pd.DataFrame, key_name: str = "id") -> pd.DataFrame:
    """Add surrogate key column."""
    df = df.copy()
    df[key_name] = range(1, len(df) + 1)
    cols = [key_name] + [c for c in df.columns if c != key_name]
    return df[cols]


def hash_columns(df: pd.DataFrame, columns: List[str], new_col: str = "hash_key") -> pd.DataFrame:
    """Create hash key from multiple columns."""
    df = df.copy()
    df[new_col] = pd.util.hash_pandas_object(df[columns], index=False)
    return df


def ensure_directory(path: Path):
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)


def get_file_size_mb(path: Path) -> float:
    """Get file size in MB."""
    return path.stat().st_size / 1024**2


class ProgressTracker:
    """Simple progress tracker for long-running operations."""
    
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = datetime.now()
    
    def update(self, n: int = 1):
        self.current += n
        if self.current % max(1, self.total // 20) == 0 or self.current == self.total:
            pct = self.current / self.total * 100
            elapsed = (datetime.now() - self.start_time).total_seconds()
            if self.current > 0:
                eta = elapsed / self.current * (self.total - self.current)
                logger.info(f"{self.description}: {self.current:,}/{self.total:,} ({pct:.1f}%) - ETA: {eta:.0f}s")
            else:
                logger.info(f"{self.description}: {self.current:,}/{self.total:,} ({pct:.1f}%)")
    
    def finish(self):
        elapsed = (datetime.now() - self.start_time).total_seconds()
        logger.info(f"{self.description} completed in {elapsed:.1f}s")


def load_carrier_lookup(path: Path) -> pd.DataFrame:
    """Load carrier code to name mapping."""
    if path.exists():
        return pd.read_csv(path)
    # Return default from config
    from .config import CARRIER_NAMES
    return pd.DataFrame({
        "code": list(CARRIER_NAMES.keys()),
        "name": list(CARRIER_NAMES.values())
    })


def load_airport_master(path: Path) -> pd.DataFrame:
    """Load BTS Master Coordinate airport data."""
    if path.exists():
        return pd.read_csv(path)
    # Return empty with expected columns
    return pd.DataFrame(columns=["iata_code", "airport_name", "latitude", "longitude", "city", "state"])