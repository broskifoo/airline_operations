"""
Data Profiling Script for Airline Operations & Revenue Analytics
Profiles the Kaggle 2024 Flight Delay Dataset (sample and full)
"""
import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

SAMPLE_FILE = RAW_DATA_DIR / "flight_data_2024_sample.csv"
FULL_FILE = RAW_DATA_DIR / "flight_data_2024.csv"
DICT_FILE = RAW_DATA_DIR / "flight_data_2024_data_dictionary.csv"

OUTPUT_FILE = REPORTS_DIR / "data_profile_kaggle.md"


def profile_dataframe(df: pd.DataFrame, name: str) -> dict:
    """Generate comprehensive profile of a DataFrame."""
    profile = {
        "name": name,
        "shape": df.shape,
        "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024**2,
        "columns": {},
        "missing_summary": {},
        "duplicates": int(df.duplicated().sum()),
        "date_range": None,
    }
    
    for col in df.columns:
        col_profile = {
            "dtype": str(df[col].dtype),
            "non_null_count": int(df[col].notna().sum()),
            "null_count": int(df[col].isna().sum()),
            "null_pct": float(df[col].isna().mean() * 100),
            "unique_count": int(df[col].nunique()),
        }
        
        # Numeric stats
        if pd.api.types.is_numeric_dtype(df[col]):
            col_profile.update({
                "min": float(df[col].min()) if df[col].notna().any() else None,
                "max": float(df[col].max()) if df[col].notna().any() else None,
                "mean": float(df[col].mean()) if df[col].notna().any() else None,
                "std": float(df[col].std()) if df[col].notna().any() else None,
                "median": float(df[col].median()) if df[col].notna().any() else None,
                "q25": float(df[col].quantile(0.25)) if df[col].notna().any() else None,
                "q75": float(df[col].quantile(0.75)) if df[col].notna().any() else None,
            })
        
        # String/categorical stats
        elif pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_categorical_dtype(df[col]):
            if df[col].notna().any():
                top_values = df[col].value_counts().head(10).to_dict()
                col_profile["top_values"] = {str(k): int(v) for k, v in top_values.items()}
        
        # Date detection
        if "date" in col.lower() or "fl_date" == col:
            try:
                parsed = pd.to_datetime(df[col], errors="coerce")
                if parsed.notna().any():
                    col_profile["date_min"] = str(parsed.min())
                    col_profile["date_max"] = str(parsed.max())
                    profile["date_range"] = (str(parsed.min()), str(parsed.max()))
            except:
                pass
        
        profile["columns"][col] = col_profile
        profile["missing_summary"][col] = col_profile["null_pct"]
    
    return profile


def generate_markdown_report(profiles: list[dict], dict_df: pd.DataFrame) -> str:
    """Generate markdown report from profiles."""
    lines = [
        "# Data Profile Report: Kaggle Flight Delay Dataset 2024",
        f"\n**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Source**: {SAMPLE_FILE.name} (sample) + {FULL_FILE.name} (full)",
        "\n---\n",
    ]
    
    for profile in profiles:
        lines.extend([
            f"## {profile['name']}",
            f"\n**Rows**: {profile['shape'][0]:,} | **Columns**: {profile['shape'][1]} | **Memory**: {profile['memory_usage_mb']:.1f} MB",
            f"**Duplicate Rows**: {profile['duplicates']:,}",
        ])
        
        if profile["date_range"]:
            lines.append(f"**Date Range**: {profile['date_range'][0]} to {profile['date_range'][1]}")
        
        lines.append("\n### Column Summary\n")
        lines.append("| Column | Type | Non-Null | Null % | Unique | Min | Max | Mean | Std |")
        lines.append("|--------|------|----------|--------|--------|-----|-----|------|-----|")
        
        for col_name, col_info in profile["columns"].items():
            dtype = col_info["dtype"]
            non_null = col_info["non_null_count"]
            null_pct = f"{col_info['null_pct']:.1f}%"
            unique = col_info["unique_count"]
            
            min_val = col_info.get("min")
            max_val = col_info.get("max")
            mean_val = col_info.get("mean")
            std_val = col_info.get("std")
            
            min_str = f"{min_val:.2f}" if min_val is not None else "N/A"
            max_str = f"{max_val:.2f}" if max_val is not None else "N/A"
            mean_str = f"{mean_val:.2f}" if mean_val is not None else "N/A"
            std_str = f"{std_val:.2f}" if std_val is not None else "N/A"
            
            lines.append(f"| {col_name} | {dtype} | {non_null:,} | {null_pct} | {unique:,} | {min_str} | {max_str} | {mean_str} | {std_str} |")
        
        lines.append("\n### Missing Values Detail\n")
        missing_df = pd.DataFrame([
            {"Column": k, "Null %": f"{v:.2f}%"}
            for k, v in sorted(profile["missing_summary"].items(), key=lambda x: -x[1])
        ])
        lines.append(missing_df.to_markdown(index=False))
        
        lines.append("\n---\n")
    
    # Data Dictionary section
    if not dict_df.empty:
        lines.extend([
            "## Data Dictionary (from Kaggle)",
            "\n| Column | Description |\n|--------|-------------|"
        ])
        for _, row in dict_df.iterrows():
            lines.append(f"| {row.get('Column Name', row.iloc[0])} | {row.get('Description', row.iloc[1])} |")
    
    return "\n".join(lines)


def main():
    print("Loading data dictionary...")
    dict_df = pd.read_csv(DICT_FILE) if DICT_FILE.exists() else pd.DataFrame()
    
    print("Profiling sample dataset (10K rows)...")
    sample_df = pd.read_csv(SAMPLE_FILE)
    sample_profile = profile_dataframe(sample_df, "Sample Dataset (10,000 rows)")
    
    print("Profiling full dataset (first 100K rows for speed)...")
    # Read first 100K rows of full dataset for quick profiling
    full_df = pd.read_csv(FULL_FILE, nrows=100000)
    full_profile = profile_dataframe(full_df, "Full Dataset (First 100,000 rows)")
    
    # Also get full row count efficiently
    print("Counting total rows in full dataset...")
    with open(FULL_FILE, 'r') as f:
        total_lines = sum(1 for _ in f) - 1  # minus header
    full_profile["total_rows_estimate"] = total_lines
    
    print("Generating markdown report...")
    report = generate_markdown_report([sample_profile, full_profile], dict_df)
    
    OUTPUT_FILE.write_text(report)
    print(f"Report saved to: {OUTPUT_FILE}")
    
    # Also save JSON for programmatic use
    json_output = REPORTS_DIR / "data_profile_kaggle.json"
    with open(json_output, "w") as f:
        json.dump({"sample": sample_profile, "full": full_profile}, f, indent=2, default=str)
    print(f"JSON saved to: {json_output}")


if __name__ == "__main__":
    main()