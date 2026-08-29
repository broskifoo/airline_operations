"""
Profile DB1B Market and Coupon datasets (sample)
"""
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

MARKET_FILE = RAW_DIR / "DB1B_Market_2024_Q1" / "Origin_and_Destination_Survey_DB1BMarket_2024_1.csv"
COUPON_FILE = RAW_DIR / "DB1B_Coupon_2024_Q1" / "Origin_and_Destination_Survey_DB1BCoupon_2024_1.csv"


def profile_large_csv(filepath: Path, name: str, nrows: int = 50000):
    print(f"Profiling {name} (first {nrows:,} rows)...")
    df = pd.read_csv(filepath, nrows=nrows, low_memory=False)
    
    profile = {
        "name": name,
        "file_path": str(filepath),
        "sample_rows": len(df),
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "missing_pct": {col: float(df[col].isna().mean() * 100) for col in df.columns},
        "unique_counts": {col: int(df[col].nunique()) for col in df.columns},
    }
    
    # Numeric stats for key columns
    numeric_cols = df.select_dtypes(include=['number']).columns
    if len(numeric_cols) > 0:
        profile["numeric_stats"] = df[numeric_cols].describe().to_dict()
    
    # Top values for categorical
    cat_cols = df.select_dtypes(include=['object']).columns
    if len(cat_cols) > 0:
        profile["top_values"] = {}
        for col in cat_cols[:10]:  # Limit to first 10 categorical
            if df[col].notna().any():
                profile["top_values"][col] = df[col].value_counts().head(10).to_dict()
    
    return profile, df


def generate_db1b_report(market_profile, coupon_profile):
    lines = [
        "# Data Profile Report: BTS DB1B 2024 Q1",
        f"\n**Source**: DB1B Market (10% sample) & Coupon (10% sample)",
        f"**Quarter**: 2024 Q1",
        "\n---\n",
    ]
    
    for profile in [market_profile, coupon_profile]:
        lines.extend([
            f"## {profile['name']}",
            f"\n**Sample Rows**: {profile['sample_rows']:,}",
            f"**Columns**: {len(profile['columns'])}",
            "\n### Columns & Types\n",
            "| Column | Type | Missing % | Unique |\n|--------|------|-----------|--------|"
        ])
        
        for col in profile['columns']:
            lines.append(f"| {col} | {profile['dtypes'][col]} | {profile['missing_pct'][col]:.2f}% | {profile['unique_counts'][col]:,} |")
        
        if 'numeric_stats' in profile:
            lines.append("\n### Numeric Column Statistics\n")
            for col, stats in profile['numeric_stats'].items():
                lines.append(f"\n**{col}**:")
                lines.append(f"- Mean: {stats.get('mean', 'N/A'):.2f}")
                lines.append(f"- Std: {stats.get('std', 'N/A'):.2f}")
                lines.append(f"- Min: {stats.get('min', 'N/A'):.2f}")
                lines.append(f"- Max: {stats.get('max', 'N/A'):.2f}")
        
        if 'top_values' in profile:
            lines.append("\n### Top Categorical Values\n")
            for col, vals in profile['top_values'].items():
                lines.append(f"\n**{col}**:")
                for val, count in list(vals.items())[:5]:
                    lines.append(f"  - {val}: {count:,}")
        
        lines.append("\n---\n")
    
    return "\n".join(lines)


def main():
    market_profile, market_df = profile_large_csv(MARKET_FILE, "DB1B Market 2024 Q1")
    coupon_profile, coupon_df = profile_large_csv(COUPON_FILE, "DB1B Coupon 2024 Q1")
    
    report = generate_db1b_report(market_profile, coupon_profile)
    output_file = REPORTS_DIR / "data_profile_db1b.md"
    output_file.write_text(report)
    print(f"Report saved to: {output_file}")
    
    # Quick sample for join key analysis
    print("\n=== JOIN KEY ANALYSIS ===")
    print("Market columns:", list(market_df.columns))
    print("Coupon columns:", list(coupon_df.columns))
    
    # Check key columns
    key_cols = ['ItinID', 'Year', 'Quarter', 'Origin', 'Dest', 'RPCarrier', 'TkCarrier', 'OpCarrier', 'Passengers', 'MktFare', 'MktDistance', 'MktMilesFlown']
    for col in key_cols:
        if col in market_df.columns:
            print(f"Market.{col}: dtype={market_df[col].dtype}, null%={market_df[col].isna().mean()*100:.2f}%, unique={market_df[col].nunique()}")
    
    key_cols_coupon = ['ItinID', 'MktID', 'SeqNum', 'Origin', 'Dest', 'OpCarrier', 'TkCarrier', 'Passengers', 'FareClass', 'Distance', 'DistanceGroup']
    for col in key_cols_coupon:
        if col in coupon_df.columns:
            print(f"Coupon.{col}: dtype={coupon_df[col].dtype}, null%={coupon_df[col].isna().mean()*100:.2f}%, unique={coupon_df[col].nunique()}")


if __name__ == "__main__":
    main()