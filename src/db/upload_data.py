"""
src/db/upload_data.py
Utility script to migrate local processed data and raw dimensions to an online PostgreSQL database.
Usage:
    python -m src.db.upload_data
"""

import sys
from pathlib import Path
import pandas as pd
import logging

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from db.database import get_db_engine, is_db_available, get_database_url

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def upload_all_data():
    """Migrates all raw dimensions and processed tables to the online PostgreSQL database."""
    engine = get_db_engine()
    if not engine or not is_db_available():
        logger.error(
            "Cannot connect to online database! Please verify DATABASE_URL is set in environment or .env file.\n"
            f"Current URL: {get_database_url()}"
        )
        return False

    raw_dir = PROJECT_ROOT / "data" / "raw"
    proc_dir = PROJECT_ROOT / "data" / "processed"

    tables_to_upload = [
        ("dim_supplier", raw_dir / "suppliers.csv", "csv"),
        ("dim_product", raw_dir / "products.csv", "csv"),
        ("dim_warehouse", raw_dir / "warehouses.csv", "csv"),
        ("fact_supplier_product", raw_dir / "supplier_products.csv", "csv"),
        ("fact_shipments", proc_dir / "shipments_enriched.parquet", "parquet"),
        ("fact_inventory", proc_dir / "inventory_enriched.parquet", "parquet"),
        ("fact_demand", proc_dir / "demand_enriched.parquet", "parquet"),
        ("supplier_risk", proc_dir / "supplier_risk.parquet", "parquet"),
        ("inventory_summary", proc_dir / "inventory_summary.parquet", "parquet"),
        ("monte_carlo_summary", proc_dir / "monte_carlo_summary.parquet", "parquet"),
        ("forecast_comparison", proc_dir / "forecast_comparison.parquet", "parquet"),
        ("best_forecast_model_per_product", proc_dir / "best_forecast_model_per_product.parquet", "parquet"),
    ]

    logger.info("Starting online database upload...")
    success_count = 0

    for table_name, file_path, file_type in tables_to_upload:
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}, skipping.")
            continue

        try:
            if file_type == "csv":
                df = pd.read_csv(file_path)
            else:
                df = pd.read_parquet(file_path)

            logger.info(f"Uploading {len(df):,} records into table '{table_name}'...")
            df.to_sql(table_name, con=engine, if_exists="replace", index=False, chunksize=5000)
            logger.info(f"✓ Table '{table_name}' uploaded successfully.")
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to upload table '{table_name}': {e}")

    logger.info(f"\nMigration completed: {success_count}/{len(tables_to_upload)} tables uploaded to online database.")
    return True


if __name__ == "__main__":
    upload_all_data()
