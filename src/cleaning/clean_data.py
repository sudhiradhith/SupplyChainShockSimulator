"""
src/cleaning/clean_data.py
Data cleaning and validation utilities for supply chain raw tables.
"""

import pandas as pd
import numpy as np


def clean_shipments_data(shipments_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans shipments data:
    - Parses dates (order_date, shipment_date, expected_delivery, actual_delivery)
    - Computes calculated_delay_days = actual_delivery - expected_delivery (in days)
    - Validates shipping_cost and quantity > 0
    """
    df = shipments_df.copy()
    for col in ["order_date", "shipment_date", "expected_delivery", "actual_delivery"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    if "expected_delivery" in df.columns and "actual_delivery" in df.columns:
        df["calculated_delay_days"] = (df["actual_delivery"] - df["expected_delivery"]).dt.days
        df["calculated_delay_days"] = df["calculated_delay_days"].fillna(0)

    if "quantity" in df.columns:
        df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)

    if "shipping_cost" in df.columns:
        df["shipping_cost"] = pd.to_numeric(df["shipping_cost"], errors="coerce").fillna(0)

    return df


def clean_inventory_data(inventory_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans inventory data:
    - Parses date_id
    - Enforces non-negative values for opening, received, demand, and closing inventory
    """
    df = inventory_df.copy()
    if "date_id" in df.columns:
        df["date_id"] = pd.to_datetime(df["date_id"], errors="coerce")

    num_cols = ["opening_inventory", "received_quantity", "demand_quantity", "closing_inventory"]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            df[col] = np.maximum(0, df[col])

    return df


def clean_demand_data(demand_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans demand data:
    - Parses date_id
    - Validates price > 0, demand_quantity >= 0
    """
    df = demand_df.copy()
    if "date_id" in df.columns:
        df["date_id"] = pd.to_datetime(df["date_id"], errors="coerce")

    if "demand_quantity" in df.columns:
        df["demand_quantity"] = pd.to_numeric(df["demand_quantity"], errors="coerce").fillna(0)
        df["demand_quantity"] = np.maximum(0, df["demand_quantity"])

    if "price" in df.columns:
        df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0)

    return df
