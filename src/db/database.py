"""
src/db/database.py
Cloud database engine management and online query utilities.
Supports Render Postgres, Supabase, Neon, AWS RDS, and local PostgreSQL.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from dotenv import load_dotenv

# Load local .env if present
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

logger = logging.getLogger(__name__)

_engine: Optional[Engine] = None


def get_database_url() -> Optional[str]:
    """
    Retrieves and normalizes the PostgreSQL connection URL from environment variables.
    Handles Render / Heroku 'postgres://' schema by converting to 'postgresql://'.
    """
    url = os.getenv("DATABASE_URL")
    if not url:
        # Check individual connection components
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "supply_chain_db")
        if user and host:
            url = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"

    if url:
        # SQLAlchemy 1.4+ requires postgresql:// instead of postgres://
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)

    return url


def get_db_engine() -> Optional[Engine]:
    """
    Returns a cached SQLAlchemy Engine instance or None if DATABASE_URL is not configured.
    """
    global _engine
    if _engine is not None:
        return _engine

    url = get_database_url()
    if not url:
        return None

    try:
        _engine = create_engine(
            url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            connect_args={"connect_timeout": 5}
        )
        return _engine
    except Exception as e:
        logger.warning(f"Failed to create database engine: {e}")
        return None


def is_db_available() -> bool:
    """Checks if the online database is reachable."""
    engine = get_db_engine()
    if engine is None:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.info(f"Database unreachable or not configured: {e}")
        return False


def load_table(table_name: str) -> Optional[pd.DataFrame]:
    """
    Loads a specific table from the cloud database into a pandas DataFrame.
    Returns None if database is unavailable or table does not exist.
    """
    engine = get_db_engine()
    if engine is None:
        return None

    try:
        query = f'SELECT * FROM "{table_name}"'
        df = pd.read_sql(query, con=engine)
        return df
    except Exception as e:
        logger.warning(f"Error loading table '{table_name}' from cloud DB: {e}")
        return None
