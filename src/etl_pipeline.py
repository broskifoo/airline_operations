#!/usr/bin/env python3
"""
Main ETL Pipeline Orchestrator
Airline Operations & Revenue Intelligence Platform

Usage:
    python src/etl_pipeline.py --full              # Full rebuild
    python src/etl_pipeline.py --incremental       # Incremental load (new month)
    python src/etl_pipeline.py --sample            # Run on sample data only
    python src/etl_pipeline.py --validate-only     # Run validation only
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.config import (
    PROJECT_ROOT, RAW_DATA_DIR, PROCESSED_DATA_DIR, REPORTS_DIR, OUTPUTS_DIR,
    KAGGLE_2024_SAMPLE, KAGGLE_2024_FULL, KAGGLE_DICT,
    DB1B_MARKET_ALL, DB1B_COUPON_ALL,
    BTS_AIRPORTS, BTS_CARRIERS,
    DIM_DATE, DIM_AIRLINE, DIM_AIRPORT, DIM_ROUTE,
    FACT_FLIGHTS, FACT_REVENUE,
    STAGING_DIR,
    DEFAULT_CASM, DB1B_SAMPLE_RATE
)
from src.data_loader import (
    load_kaggle_sample, load_kaggle_full_chunked, load_kaggle_full_duckdb,
    load_db1b_market_chunked, load_db1b_coupon_chunked,
    load_db1b_market_duckdb, load_db1b_coupon_duckdb,
    load_data_dictionary, save_parquet, read_parquet,
    load_t100_all_months, find_t100_files
)
from src.data_cleaning import (
    clean_flights, clean_db1b_market,
    generate_data_quality_report
)
from src.feature_engineering import (
    create_dim_date, create_dim_airline, create_dim_airport,
    create_dim_route, create_fact_flights, create_fact_revenue,
    add_airport_efficiency_score, add_route_profitability_classification,
    clean_t100_segment
)
from src.validation import (
    run_all_validations, print_validation_summary, save_validation_report
)
from src.utils import (
    setup_logging, get_logger, timer, print_df_info,
    memory_usage_mb, ensure_directory, ProgressTracker
)

logger = get_logger(__name__)


class ETLPipeline:
    """Main ETL Pipeline orchestrator."""

    def __init__(self, sample_mode: bool = False, incremental: bool = False,
                 year: int = None, month: int = None):
        self.sample_mode = sample_mode
        self.incremental = incremental
        self.year = year or datetime.now().year
        self.month = month
        self.start_time = datetime.now()

        # Ensure output directories exist
        ensure_directory(PROCESSED_DATA_DIR)
        ensure_directory(REPORTS_DIR)
        ensure_directory(OUTPUTS_DIR)
        ensure_directory(STAGING_DIR)
        ensure_directory(PROCESSED_DATA_DIR / "staging")

        # Initialize cleaning reports storage
        self.cleaning_reports = {}
        self.dimensions = {}
        self.facts = {}
        
        # For incremental mode: track what's new
        self.new_date_ids = set()
        self.new_airports = set()
        self.new_airlines = set()
        self.new_routes = set()

    @timer
    def run(self):
        """Execute the full ETL pipeline."""
        logger.info("=" * 60)
        logger.info("Starting ETL Pipeline")
        logger.info(f"Mode: {'Sample' if self.sample_mode else 'Full'}"
                    f"{' | Incremental' if self.incremental else ''}")
        logger.info("=" * 60)

        try:
            # Phase 1: Extract & Clean
            self._phase1_extract_clean()

            # Phase 2: Build Dimensions
            self._phase2_build_dimensions()

            # Phase 3: Build Fact Tables
            self._phase3_build_facts()

            # Phase 4: Enhancements (efficiency scores, profitability)
            self._phase4_enhancements()

            # Phase 5: Validation
            self._phase5_validation()

            # Phase 6: Save Outputs
            self._phase6_save_outputs()

            logger.info("=" * 60)
            logger.info(f"ETL Pipeline completed successfully in "
                        f"{(datetime.now() - self.start_time).total_seconds():.1f}s")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"ETL Pipeline failed: {e}")
            raise

    def _phase1_extract_clean(self):
        """Phase 1: Extract raw data and clean."""
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 1: EXTRACT & CLEAN")
        logger.info("=" * 60)

        # Load and clean Kaggle flights data
        if self.sample_mode:
            logger.info("Loading Kaggle sample dataset...")
            raw_flights = load_kaggle_sample()
            print_df_info(raw_flights, "Raw Flights")
            logger.info("Cleaning flights data...")
            clean_flights_df, flight_report = clean_flights(raw_flights)
            self.cleaning_reports["flights"] = flight_report
            self.dimensions["clean_flights"] = clean_flights_df
            print_df_info(clean_flights_df, "Clean Flights")
        elif self.incremental:
            logger.info(f"Loading Kaggle data for {self.year}-{self.month:02d} (incremental)...")
            raw_flights = self._load_kaggle_incremental()
            print_df_info(raw_flights, f"Raw Flights {self.year}-{self.month:02d}")
            logger.info("Cleaning flights data...")
            clean_flights_df, flight_report = clean_flights(raw_flights)
            self.cleaning_reports["flights"] = flight_report
            self.dimensions["clean_flights"] = clean_flights_df
            print_df_info(clean_flights_df, f"Clean Flights {self.year}-{self.month:02d}")
        else:
            logger.info("Loading Kaggle full dataset in chunks...")
            # Process full dataset in chunks
            total_rows = 0
            clean_chunks = []
            
            for i, chunk in enumerate(load_kaggle_full_chunked(chunksize=100000)):
                logger.info(f"Processing chunk {i+1} ({len(chunk):,} rows)...")
                print_df_info(chunk, f"Raw Flights Chunk {i+1}")
                
                clean_chunk, chunk_report = clean_flights(chunk)
                clean_chunks.append(clean_chunk)
                total_rows += len(clean_chunk)
                
                # Merge cleaning reports
                if i == 0:
                    self.cleaning_reports["flights"] = chunk_report
                else:
                    # Aggregate report stats
                    self.cleaning_reports["flights"]["final_rows"] += chunk_report["final_rows"]
                    self.cleaning_reports["flights"]["rows_removed"] += chunk_report["rows_removed"]
                    self.cleaning_reports["flights"]["steps"].extend(chunk_report["steps"])
            
            # Combine all cleaned chunks
            logger.info(f"Combining {len(clean_chunks)} chunks ({total_rows:,} total rows)...")
            clean_flights_df = pd.concat(clean_chunks, ignore_index=True)
            self.dimensions["clean_flights"] = clean_flights_df
            print_df_info(clean_flights_df, "Clean Flights (Full)")
            logger.info(f"Total cleaned flights: {len(clean_flights_df):,}")

        # Load and clean DB1B Market (always full refresh for now - quarterly)
        logger.info("Loading DB1B Market data...")
        market_chunks = list(load_db1b_market_chunked(chunksize=50000))
        raw_market = pd.concat(market_chunks, ignore_index=True) if market_chunks else pd.DataFrame()
        if not raw_market.empty:
            logger.info("Cleaning DB1B Market...")
            clean_market, market_report = clean_db1b_market(raw_market)
            self.cleaning_reports["db1b_market"] = market_report
            self.dimensions["clean_db1b_market"] = clean_market
            print_df_info(clean_market, "Clean DB1B Market")

        # DB1B Coupon data is not used in current revenue model (only Market is used)
        # Skipping to avoid memory issues - Coupon data is ~47M rows
        logger.info("Skipping DB1B Coupon data (not used in revenue model)")
        self.dimensions["clean_db1b_coupon"] = pd.DataFrame()
        self.cleaning_reports["db1b_coupon"] = {"initial_rows": 0, "final_rows": 0, "rows_removed": 0, "steps": ["Skipped - not used in revenue model"]}

        # Save cleaning report
        report_path = REPORTS_DIR / "data_quality_report.md"
        report_path.write_text(generate_data_quality_report(self.cleaning_reports))
        logger.info(f"Data quality report saved to {report_path}")

    def _phase2_build_dimensions(self):
        """Phase 2: Build dimension tables."""
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 2: BUILD DIMENSIONS")
        logger.info("=" * 60)

        clean_flights = self.dimensions["clean_flights"]

        if self.incremental:
            # Load existing dimensions
            self._load_existing_dimensions()
            
            # Extend dimensions with new data
            dim_date = self._extend_dim_date(clean_flights)
            dim_airline = self._extend_dim_airline(clean_flights)
            dim_airport = self._extend_dim_airport(clean_flights)
            dim_route = self._rebuild_dim_route(clean_flights)
        else:
            # Load reference data
            airport_master = self._load_airport_master()
            carrier_lookup = self._load_carrier_lookup()

            # DIM_DATE
            logger.info("Building DIM_DATE...")
            date_range = self._get_date_range(clean_flights)
            dim_date = create_dim_date(date_range[0], date_range[1])
            self.dimensions["dim_date"] = dim_date
            save_parquet(dim_date, DIM_DATE)
            print_df_info(dim_date, "DIM_DATE")

            # DIM_AIRLINE
            logger.info("Building DIM_AIRLINE...")
            dim_airline = create_dim_airline(clean_flights, carrier_lookup)
            self.dimensions["dim_airline"] = dim_airline
            save_parquet(dim_airline, DIM_AIRLINE)
            print_df_info(dim_airline, "DIM_AIRLINE")

            # DIM_AIRPORT
            logger.info("Building DIM_AIRPORT...")
            dim_airport = create_dim_airport(clean_flights, airport_master)
            self.dimensions["dim_airport"] = dim_airport
            save_parquet(dim_airport, DIM_AIRPORT)
            print_df_info(dim_airport, "DIM_AIRPORT")

            # DIM_ROUTE - build preliminary (will be rebuilt in phase 3 after fact_flights)
            logger.info("Building preliminary DIM_ROUTE...")
            preliminary_routes = clean_flights[["origin_airport", "dest_airport", "distance_miles"]].drop_duplicates()
            preliminary_routes["route"] = preliminary_routes["origin_airport"] + "-" + preliminary_routes["dest_airport"]
            self.dimensions["preliminary_routes"] = preliminary_routes
            
            # Build initial dim_route for phase 3 to use
            dim_route = create_dim_route(clean_flights, dim_airport)
            self.dimensions["dim_route"] = dim_route
            save_parquet(dim_route, DIM_ROUTE)
            print_df_info(dim_route, "DIM_ROUTE (initial)")

        self.dimensions["dim_date"] = dim_date
        self.dimensions["dim_airline"] = dim_airline
        self.dimensions["dim_airport"] = dim_airport
        self.dimensions["dim_route"] = dim_route

    def _phase3_build_facts(self):
        """Phase 3: Build fact tables."""
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 3: BUILD FACTS")
        logger.info("=" * 60)

        clean_flights = self.dimensions["clean_flights"]
        dim_date = self.dimensions["dim_date"]
        dim_airline = self.dimensions["dim_airline"]
        dim_airport = self.dimensions["dim_airport"]
        dim_route = self.dimensions["dim_route"]

        # dim_route already built in phase 2 for non-incremental
        # For incremental, it was rebuilt in _rebuild_dim_route
        if self.incremental:
            logger.info("Using rebuilt DIM_ROUTE for incremental load")
        else:
            logger.info("Using DIM_ROUTE built in phase 2")

        # FACT_FLIGHTS
        logger.info("Building FACT_FLIGHTS...")
        fact_flights = create_fact_flights(
            clean_flights, dim_date, dim_airline, dim_airport, dim_route
        )
        self.facts["fact_flights"] = fact_flights
        
        if self.incremental:
            # Append to existing partitioned fact_flights
            logger.info("Appending to existing FACT_FLIGHTS (partitioned by date_id)...")
            save_parquet(fact_flights, FACT_FLIGHTS, partition_cols=["date_id"], mode="append")
        else:
            save_parquet(fact_flights, FACT_FLIGHTS, partition_cols=["date_id"])
        print_df_info(fact_flights, "FACT_FLIGHTS")

        # FACT_REVENUE
        logger.info("Building FACT_REVENUE...")
        clean_market = self.dimensions.get("clean_db1b_market", pd.DataFrame())
        clean_coupon = self.dimensions.get("clean_db1b_coupon", pd.DataFrame())
        t100_segment = self._load_t100_segment()

        if self.incremental:
            # For incremental, rebuild revenue for affected carrier-route-months
            fact_revenue = self._build_incremental_revenue(
                clean_market, clean_coupon, t100_segment,
                dim_date, dim_airline, dim_route
            )
        else:
            fact_revenue = create_fact_revenue(
                clean_market, clean_coupon, t100_segment,
                dim_date, dim_airline, dim_route,
                casm=DEFAULT_CASM
            )

        if not fact_revenue.empty:
            fact_revenue = add_route_profitability_classification(fact_revenue)
            self.facts["fact_revenue"] = fact_revenue
            
            if self.incremental:
                # Update existing fact_revenue (replace affected partitions)
                logger.info("Updating FACT_REVENUE for affected carrier-route-months...")
                self._merge_incremental_revenue(fact_revenue)
            else:
                save_parquet(fact_revenue, FACT_REVENUE)
            print_df_info(fact_revenue, "FACT_REVENUE")
        else:
            logger.warning("FACT_REVENUE is empty - T-100 data not available")
            self.facts["fact_revenue"] = pd.DataFrame()

    def _build_incremental_revenue(self, clean_market: pd.DataFrame, clean_coupon: pd.DataFrame,
                                   t100_segment: pd.DataFrame, dim_date: pd.DataFrame,
                                   dim_airline: pd.DataFrame, dim_route: pd.DataFrame) -> pd.DataFrame:
        """Build revenue for new month only (incremental)."""
        logger.info("Building incremental revenue for new month...")
        
        # Filter T-100 to the new month only
        if t100_segment.empty:
            return pd.DataFrame()
        
        t100 = clean_t100_segment(t100_segment)
        t100 = t100[(t100["year"] == self.year) & (t100["month"] == self.month)]
        
        if t100.empty:
            logger.warning(f"No T-100 data for {self.year}-{self.month:02d}")
            return pd.DataFrame()
        
        # Build revenue for this month using the same logic as full build
        # but only for the specific year/month
        from src.config import DEFAULT_CASM
        
        # We need to create a temporary fact_revenue for just this month
        # This is a simplified version - in production you'd want more sophisticated incremental logic
        return create_fact_revenue(
            clean_market, clean_coupon, t100_segment,
            dim_date, dim_airline, dim_route,
            casm=DEFAULT_CASM
        )

    def _merge_incremental_revenue(self, new_revenue: pd.DataFrame):
        """Merge new revenue data with existing fact_revenue."""
        if new_revenue.empty:
            return
        
        # For incremental updates, we need to replace the affected partitions
        # Since fact_revenue is not partitioned, we read existing, remove affected, append new
        if FACT_REVENUE.exists():
            existing = read_parquet(FACT_REVENUE)
            # Remove rows for the same year/month that we're updating
            mask = (existing["year"] == self.year) & (existing["month"] == self.month)
            existing = existing[~mask]
            combined = pd.concat([existing, new_revenue], ignore_index=True)
        else:
            combined = new_revenue
        
        save_parquet(combined, FACT_REVENUE)
        logger.info(f"Updated FACT_REVENUE: {len(combined):,} total rows")

    def _phase4_enhancements(self):
        """Phase 4: Add analytical enhancements."""
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 4: ENHANCEMENTS")
        logger.info("=" * 60)

        dim_airport = self.dimensions["dim_airport"]
        fact_flights = self.facts["fact_flights"]

        # Add airport efficiency scores
        logger.info("Calculating airport efficiency scores...")
        enhanced_airport = add_airport_efficiency_score(fact_flights, dim_airport)
        self.dimensions["dim_airport"] = enhanced_airport
        save_parquet(enhanced_airport, DIM_AIRPORT)
        print_df_info(enhanced_airport, "DIM_AIRPORT (Enhanced)")

        # Route profitability (if revenue fact exists)
        fact_revenue = self.facts.get("fact_revenue")
        if fact_revenue is not None and not fact_revenue.empty:
            logger.info("Adding route profitability classification...")
            enhanced_revenue = add_route_profitability_classification(fact_revenue)
            self.facts["fact_revenue"] = enhanced_revenue
            save_parquet(enhanced_revenue, FACT_REVENUE)

    def _phase5_validation(self):
        """Phase 5: Run validation checks."""
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 5: VALIDATION")
        logger.info("=" * 60)

        dim_date = self.dimensions["dim_date"]
        dim_airline = self.dimensions["dim_airline"]
        dim_airport = self.dimensions["dim_airport"]
        dim_route = self.dimensions["dim_route"]
        fact_flights = self.facts["fact_flights"]
        fact_revenue = self.facts.get("fact_revenue", pd.DataFrame())

        summary = run_all_validations(
            dim_date, dim_airline, dim_airport, dim_route,
            fact_flights, fact_revenue
        )

        print_validation_summary(summary)

        # Save validation report
        report_path = REPORTS_DIR / "validation_report.md"
        save_validation_report(summary, report_path)

        if summary["failed"] > 0:
            logger.warning(f"Validation completed with {summary['failed']} failures")
        else:
            logger.info("All validation checks passed!")

    def _phase6_save_outputs(self):
        """Phase 6: Final outputs and summary."""
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 6: FINAL OUTPUTS")
        logger.info("=" * 60)

        # Print summary
        logger.info("\n--- PIPELINE SUMMARY ---")
        for name, df in self.dimensions.items():
            if hasattr(df, 'shape'):
                logger.info(f"  {name}: {df.shape[0]:,} rows x {df.shape[1]} cols "
                            f"({memory_usage_mb(df):.1f} MB)")

        for name, df in self.facts.items():
            if hasattr(df, 'shape') and not df.empty:
                logger.info(f"  {name}: {df.shape[0]:,} rows x {df.shape[1]} cols "
                            f"({memory_usage_mb(df):.1f} MB)")

        logger.info(f"\nOutputs saved to: {PROCESSED_DATA_DIR}")
        logger.info(f"Reports saved to: {REPORTS_DIR}")

    def _load_airport_master(self) -> pd.DataFrame:
        """Load BTS Master Coordinate airport reference data."""
        if BTS_AIRPORTS.exists():
            logger.info(f"Loading airport master from {BTS_AIRPORTS}")
            return pd.read_csv(BTS_AIRPORTS)
        logger.warning(f"Airport master file not found at {BTS_AIRPORTS}")
        return pd.DataFrame()

    def _load_carrier_lookup(self) -> pd.DataFrame:
        """Load BTS Carrier lookup reference data."""
        if BTS_CARRIERS.exists():
            logger.info(f"Loading carrier lookup from {BTS_CARRIERS}")
            return pd.read_csv(BTS_CARRIERS)
        logger.warning(f"Carrier lookup file not found at {BTS_CARRIERS}")
        return pd.DataFrame()

    def _load_kaggle_incremental(self) -> pd.DataFrame:
        """Load Kaggle data for specific year/month (incremental)."""
        # Calculate date range for the month
        import calendar
        _, last_day = calendar.monthrange(self.year, self.month)
        start_date = f"{self.year}-{self.month:02d}-01"
        end_date = f"{self.year}-{self.month:02d}-{last_day}"
        
        logger.info(f"Filtering data for {start_date} to {end_date}")
        
        # Read full file but filter by date (more efficient for single month)
        # For true incremental, we'd use the chunked reader with date filtering
        chunks = []
        for chunk in load_kaggle_full_chunked(chunksize=100000):
            # Column is already renamed to 'flight_date' by load_kaggle_full_chunked
            mask = (chunk["flight_date"] >= start_date) & (chunk["flight_date"] <= end_date)
            filtered = chunk[mask]
            if not filtered.empty:
                chunks.append(filtered)
        
        if chunks:
            result = pd.concat(chunks, ignore_index=True)
            logger.info(f"Loaded {len(result):,} rows for {self.year}-{self.month:02d}")
            return result
        else:
            logger.warning(f"No data found for {self.year}-{self.month:02d}")
            return pd.DataFrame()

    def _load_t100_segment(self) -> pd.DataFrame:
        """Load T-100 Segment data for revenue modeling."""
        t100_files = find_t100_files()
        if t100_files:
            logger.info(f"Found {len(t100_files)} T-100 segment files")
            return load_t100_all_months()
        
        # Fallback: check for single CSV file
        t100_path = RAW_DATA_DIR / "T100_Segment_2024.csv"
        if t100_path.exists():
            logger.info(f"Loading T-100 Segment from {t100_path}")
            return pd.read_csv(t100_path, low_memory=False)
        
        logger.warning("T-100 Segment files not found. Download from:")
        logger.warning("https://www.transtats.bts.gov/DL_SelectFields.aspx?QO_fu146_anzr=Nv4+Pn44vr45&gnoyr_VQ=GEE")
        return pd.DataFrame()

    def _load_existing_dimensions(self):
        """Load existing dimension tables for incremental updates."""
        logger.info("Loading existing dimensions for incremental update...")
        
        # Load existing dim_date (extend if needed)
        if DIM_DATE.exists():
            self.dimensions["dim_date"] = read_parquet(DIM_DATE)
        else:
            logger.warning("DIM_DATE not found, will create new")
            self.dimensions["dim_date"] = pd.DataFrame()
        
        # Load existing dim_airline
        if DIM_AIRLINE.exists():
            self.dimensions["dim_airline"] = read_parquet(DIM_AIRLINE)
        else:
            self.dimensions["dim_airline"] = pd.DataFrame()
        
        # Load existing dim_airport
        if DIM_AIRPORT.exists():
            self.dimensions["dim_airport"] = read_parquet(DIM_AIRPORT)
        else:
            self.dimensions["dim_airport"] = pd.DataFrame()
        
        # Load existing dim_route
        if DIM_ROUTE.exists():
            self.dimensions["dim_route"] = read_parquet(DIM_ROUTE)
        else:
            self.dimensions["dim_route"] = pd.DataFrame()

    def _extend_dim_date(self, new_flights: pd.DataFrame):
        """Extend DIM_DATE with new dates if needed."""
        if "dim_date" not in self.dimensions or self.dimensions["dim_date"].empty:
            # Create new dim_date
            date_range = self._get_date_range(new_flights)
            dim_date = create_dim_date(date_range[0], date_range[1])
        else:
            dim_date = self.dimensions["dim_date"]
            existing_max = dim_date["date"].max()
            new_max = new_flights["flight_date"].max()
            if new_max > existing_max:
                # Extend dim_date
                new_start = (existing_max + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
                new_end = new_max.strftime("%Y-%m-%d")
                extension = create_dim_date(new_start, new_end)
                dim_date = pd.concat([dim_date, extension], ignore_index=True)
                logger.info(f"Extended DIM_DATE from {existing_max} to {new_max}")
        
        self.dimensions["dim_date"] = dim_date
        save_parquet(dim_date, DIM_DATE)
        return dim_date

    def _extend_dim_airline(self, new_flights: pd.DataFrame):
        """Extend DIM_AIRLINE with new carriers if needed."""
        if "dim_airline" not in self.dimensions or self.dimensions["dim_airline"].empty:
            airport_master = self._load_airport_master()
            carrier_lookup = self._load_carrier_lookup()
            dim_airline = create_dim_airline(new_flights, carrier_lookup)
        else:
            dim_airline = self.dimensions["dim_airline"]
            existing_carriers = set(dim_airline["carrier_code"])
            new_carriers = set(new_flights["carrier_code"].unique()) - existing_carriers
            if new_carriers:
                carrier_lookup = self._load_carrier_lookup()
                new_dim = create_dim_airline(new_flights[new_flights["carrier_code"].isin(new_carriers)], carrier_lookup)
                # Adjust airline_id to continue from max
                max_id = dim_airline["airline_id"].max()
                new_dim["airline_id"] = range(max_id + 1, max_id + 1 + len(new_dim))
                dim_airline = pd.concat([dim_airline, new_dim], ignore_index=True)
                self.new_airlines.update(new_carriers)
                logger.info(f"Added {len(new_carriers)} new carriers to DIM_AIRLINE: {new_carriers}")
        
        self.dimensions["dim_airline"] = dim_airline
        save_parquet(dim_airline, DIM_AIRLINE)
        return dim_airline

    def _extend_dim_airport(self, new_flights: pd.DataFrame):
        """Extend DIM_AIRPORT with new airports if needed."""
        if "dim_airport" not in self.dimensions or self.dimensions["dim_airport"].empty:
            airport_master = self._load_airport_master()
            dim_airport = create_dim_airport(new_flights, airport_master)
        else:
            dim_airport = self.dimensions["dim_airport"]
            existing_airports = set(dim_airport["airport_code"])
            # Get unique airports from new flights
            origins = new_flights[["origin_airport", "origin_city", "origin_state"]].drop_duplicates()
            origins.columns = ["airport_code", "city", "state"]
            dests = new_flights[["dest_airport", "dest_city", "dest_state"]].drop_duplicates()
            dests.columns = ["airport_code", "city", "state"]
            all_new = pd.concat([origins, dests]).drop_duplicates(subset=["airport_code"])
            new_airports = set(all_new["airport_code"]) - existing_airports
            if new_airports:
                airport_master = self._load_airport_master()
                new_dim = create_dim_airport(all_new[all_new["airport_code"].isin(new_airports)], airport_master)
                # Adjust airport_id to continue from max
                max_id = dim_airport["airport_id"].max()
                new_dim["airport_id"] = range(max_id + 1, max_id + 1 + len(new_dim))
                dim_airport = pd.concat([dim_airport, new_dim], ignore_index=True)
                self.new_airports.update(new_airports)
                logger.info(f"Added {len(new_airports)} new airports to DIM_AIRPORT")
        
        self.dimensions["dim_airport"] = dim_airport
        save_parquet(dim_airport, DIM_AIRPORT)
        return dim_airport

    def _rebuild_dim_route(self, clean_flights: pd.DataFrame):
        """Extend DIM_ROUTE with new routes from incremental data."""
        logger.info("Extending DIM_ROUTE with new routes...")
        dim_airport = self.dimensions["dim_airport"]
        
        # Load existing dim_route
        existing_route = self.dimensions.get("dim_route")
        if existing_route is None or existing_route.empty:
            # No existing routes, create new
            logger.info("No existing DIM_ROUTE, creating new...")
            dim_route = create_dim_route(clean_flights, dim_airport)
        else:
            # Extend with new routes
            dim_route = existing_route.copy()
            max_route_id = dim_route["route_id"].max()
            
            # Get unique routes from new flights
            new_routes = clean_flights[["origin_airport", "dest_airport", "distance_miles"]].drop_duplicates()
            new_routes["route"] = new_routes["origin_airport"] + "-" + new_routes["dest_airport"]
            
            # Map to airport_ids
            airport_map = dim_airport.set_index("airport_code")["airport_id"].to_dict()
            new_routes["origin_airport_id"] = new_routes["origin_airport"].map(airport_map)
            new_routes["dest_airport_id"] = new_routes["dest_airport"].map(airport_map)
            new_routes = new_routes.dropna(subset=["origin_airport_id", "dest_airport_id"])
            new_routes["origin_airport_id"] = new_routes["origin_airport_id"].astype(int)
            new_routes["dest_airport_id"] = new_routes["dest_airport_id"].astype(int)
            
            # Aggregate distance (median)
            new_routes = new_routes.groupby(["origin_airport_id", "dest_airport_id"])["distance_miles"].median().reset_index()
            
            # Find routes not in existing dim_route
            existing_pairs = set(zip(dim_route["origin_airport_id"], dim_route["dest_airport_id"]))
            new_routes["pair"] = list(zip(new_routes["origin_airport_id"], new_routes["dest_airport_id"]))
            truly_new = new_routes[~new_routes["pair"].isin(existing_pairs)].copy()
            
            if len(truly_new) > 0:
                logger.info(f"Adding {len(truly_new)} new routes to DIM_ROUTE")
                truly_new["route_id"] = range(max_route_id + 1, max_route_id + 1 + len(truly_new))
                
                # Add codes for readability
                code_map = dim_airport.set_index("airport_id")["airport_code"].to_dict()
                truly_new["origin_code"] = truly_new["origin_airport_id"].map(code_map)
                truly_new["dest_code"] = truly_new["dest_airport_id"].map(code_map)
                truly_new["route_code"] = truly_new["origin_code"] + "-" + truly_new["dest_code"]
                
                # Distance category
                def dist_cat(d):
                    if d < 500: return "Short Haul"
                    elif d < 1500: return "Medium Haul"
                    elif d < 3000: return "Long Haul"
                    else: return "Ultra Long Haul"
                truly_new["distance_category"] = truly_new["distance_miles"].apply(dist_cat)
                
                truly_new = truly_new[["route_id", "origin_airport_id", "dest_airport_id",
                                       "origin_code", "dest_code", "route_code",
                                       "distance_miles", "distance_category"]]
                
                dim_route = pd.concat([dim_route, truly_new], ignore_index=True)
            else:
                logger.info("No new routes to add to DIM_ROUTE")
        
        self.dimensions["dim_route"] = dim_route
        save_parquet(dim_route, DIM_ROUTE)
        return dim_route

    def _get_date_range(self, df: pd.DataFrame) -> tuple:
        """Get min/max dates from flight data."""
        if "flight_date" in df.columns:
            min_date = df["flight_date"].min()
            max_date = df["flight_date"].max()
            return (min_date.strftime("%Y-%m-%d"), max_date.strftime("%Y-%m-%d"))
        return ("2024-01-01", "2024-12-31")


def run_full_etl():
    """Run full ETL pipeline."""
    pipeline = ETLPipeline(sample_mode=False, incremental=False)
    pipeline.run()


def run_sample_etl():
    """Run ETL on sample data for testing."""
    pipeline = ETLPipeline(sample_mode=True, incremental=False)
    pipeline.run()


def run_incremental_etl(year: int, month: int):
    """Run incremental ETL for a specific month."""
    pipeline = ETLPipeline(sample_mode=False, incremental=True, year=year, month=month)
    pipeline.run()


def run_validation_only():
    """Run validation on existing processed data."""
    logger.info("Loading processed data for validation...")
    dim_date = read_parquet(DIM_DATE)
    dim_airline = read_parquet(DIM_AIRLINE)
    dim_airport = read_parquet(DIM_AIRPORT)
    dim_route = read_parquet(DIM_ROUTE)
    fact_flights = read_parquet(FACT_FLIGHTS)

    fact_revenue = pd.DataFrame()
    if FACT_REVENUE.exists():
        fact_revenue = read_parquet(FACT_REVENUE)

    summary = run_all_validations(
        dim_date, dim_airline, dim_airport, dim_route,
        fact_flights, fact_revenue
    )
    print_validation_summary(summary)

    report_path = REPORTS_DIR / "validation_report.md"
    save_validation_report(summary, report_path)


def main():
    parser = argparse.ArgumentParser(
        description="Airline Operations & Revenue Analytics ETL Pipeline"
    )
    parser.add_argument("--full", action="store_true",
                        help="Run full ETL pipeline")
    parser.add_argument("--sample", action="store_true",
                        help="Run ETL on sample data only (for testing)")
    parser.add_argument("--incremental", action="store_true",
                        help="Run incremental load for a specific month")
    parser.add_argument("--year", type=int, default=2024,
                        help="Year for incremental load")
    parser.add_argument("--month", type=int,
                        help="Month for incremental load (1-12)")
    parser.add_argument("--validate-only", action="store_true",
                        help="Run validation only on existing processed data")
    parser.add_argument("--log-file", type=str,
                        help="Path to log file")

    args = parser.parse_args()

    # Setup logging
    log_file = Path(args.log_file) if args.log_file else None
    setup_logging(log_file=log_file)

    if args.validate_only:
        run_validation_only()
    elif args.sample:
        run_sample_etl()
    elif args.incremental:
        if not args.month:
            parser.error("--incremental requires --month")
        run_incremental_etl(args.year, args.month)
    elif args.full:
        run_full_etl()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()