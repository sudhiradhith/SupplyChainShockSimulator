"""
Supplier Risk Engine
Calculates a weighted composite risk score (0-100) per supplier and
classifies into LOW / MEDIUM / HIGH / CRITICAL bands.
"""

import pandas as pd
import numpy as np


def normalize_0_100(series: pd.Series, higher_is_riskier: bool = True) -> pd.Series:
    """
    Min-max normalize a series to 0-100.
    If higher_is_riskier=False, the scale is inverted so that
    a "good" raw value (e.g. high reliability) maps to a LOW risk score.
    """
    min_val, max_val = series.min(), series.max()
    if max_val == min_val:
        return pd.Series(0, index=series.index)  # no variation = no differentiating risk

    scaled = (series - min_val) / (max_val - min_val) * 100
    if not higher_is_riskier:
        scaled = 100 - scaled
    return scaled


def calculate_delay_risk(shipments_df: pd.DataFrame) -> pd.DataFrame:
    """
    Delay Risk: based on average shipment delay per supplier.
    Higher average delay = higher risk.
    """
    avg_delay = shipments_df.groupby("supplier_id")["calculated_delay_days"].mean().reset_index()
    avg_delay.columns = ["supplier_id", "avg_delay_days"]
    avg_delay["delay_risk"] = normalize_0_100(avg_delay["avg_delay_days"], higher_is_riskier=True)
    return avg_delay


def calculate_reliability_risk(suppliers_df: pd.DataFrame) -> pd.DataFrame:
    """
    Reliability Risk: inverse of on_time_delivery_rate.
    Higher on-time rate = lower risk.
    """
    df = suppliers_df[["supplier_id", "on_time_delivery_rate"]].copy()
    df["reliability_risk"] = normalize_0_100(df["on_time_delivery_rate"], higher_is_riskier=False)
    return df


def calculate_capacity_risk(suppliers_df: pd.DataFrame, supplier_product_df: pd.DataFrame) -> pd.DataFrame:
    """
    Capacity Risk: suppliers with low capacity_per_day relative to
    how many products they're responsible for are riskier
    (higher chance of being a bottleneck under a shock).
    """
    product_count = supplier_product_df.groupby("supplier_id")["product_id"].nunique().reset_index()
    product_count.columns = ["supplier_id", "product_count"]

    df = suppliers_df[["supplier_id", "capacity_per_day"]].merge(product_count, on="supplier_id", how="left")
    df["product_count"] = df["product_count"].fillna(0)

    # capacity per product supplied - lower is riskier (thinner buffer per product)
    df["capacity_per_product"] = df["capacity_per_day"] / df["product_count"].replace(0, np.nan)
    df["capacity_risk"] = normalize_0_100(df["capacity_per_product"].fillna(df["capacity_per_product"].median()), higher_is_riskier=False)
    return df[["supplier_id", "capacity_risk"]]


def calculate_quality_risk(suppliers_df: pd.DataFrame) -> pd.DataFrame:
    """
    Quality Risk: inverse of quality_score.
    Higher quality score = lower risk.
    """
    df = suppliers_df[["supplier_id", "quality_score"]].copy()
    df["quality_risk"] = normalize_0_100(df["quality_score"], higher_is_riskier=False)
    return df


def calculate_dependency_risk(supplier_product_df: pd.DataFrame, products_df: pd.DataFrame) -> pd.DataFrame:
    """
    Dependency Risk: how much of a supplier's product portfolio is
    "High" criticality AND single-sourced (this supplier is the only one).
    Suppliers carrying many sole-sourced critical products are riskier
    to the business if they fail.
    """
    # count of suppliers per product, to detect single-sourced products
    supplier_counts = supplier_product_df.groupby("product_id")["supplier_id"].nunique().reset_index()
    supplier_counts.columns = ["product_id", "supplier_count"]

    merged = supplier_product_df.merge(supplier_counts, on="product_id")
    merged = merged.merge(products_df[["product_id", "criticality"]], on="product_id")

    merged["is_sole_sourced_critical"] = (
        (merged["supplier_count"] == 1) & (merged["criticality"] == "High")
    ).astype(int)

    dependency = merged.groupby("supplier_id")["is_sole_sourced_critical"].sum().reset_index()
    dependency.columns = ["supplier_id", "sole_sourced_critical_count"]
    dependency["dependency_risk"] = normalize_0_100(dependency["sole_sourced_critical_count"], higher_is_riskier=True)
    return dependency


def calculate_supplier_risk(
    suppliers_df: pd.DataFrame,
    shipments_df: pd.DataFrame,
    supplier_product_df: pd.DataFrame,
    products_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Master function: computes all five risk components, applies the
    weighted formula, and classifies each supplier into a risk band.
    """
    delay = calculate_delay_risk(shipments_df)
    reliability = calculate_reliability_risk(suppliers_df)
    capacity = calculate_capacity_risk(suppliers_df, supplier_product_df)
    quality = calculate_quality_risk(suppliers_df)
    dependency = calculate_dependency_risk(supplier_product_df, products_df)

    risk_df = suppliers_df[["supplier_id", "supplier_name"]].copy()
    risk_df = risk_df.merge(delay[["supplier_id", "delay_risk"]], on="supplier_id", how="left")
    risk_df = risk_df.merge(reliability[["supplier_id", "reliability_risk"]], on="supplier_id", how="left")
    risk_df = risk_df.merge(capacity, on="supplier_id", how="left")
    risk_df = risk_df.merge(quality[["supplier_id", "quality_risk"]], on="supplier_id", how="left")
    risk_df = risk_df.merge(dependency[["supplier_id", "dependency_risk"]], on="supplier_id", how="left")

    # fill any supplier missing a component (e.g. no shipments yet) with median, not zero,
    # so a data gap doesn't artificially look "safe"
    for col in ["delay_risk", "reliability_risk", "capacity_risk", "quality_risk", "dependency_risk"]:
        risk_df[col] = risk_df[col].fillna(risk_df[col].median())

    risk_df["supplier_risk_score"] = (
        0.30 * risk_df["delay_risk"] +
        0.25 * risk_df["reliability_risk"] +
        0.20 * risk_df["capacity_risk"] +
        0.15 * risk_df["quality_risk"] +
        0.10 * risk_df["dependency_risk"]
    )

    risk_df["risk_band"] = pd.cut(
        risk_df["supplier_risk_score"],
        bins=[-0.01, 30, 60, 80, 100],
        labels=["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    )

    return risk_df.sort_values("supplier_risk_score", ascending=False).reset_index(drop=True)