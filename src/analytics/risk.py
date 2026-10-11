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
    delay_col = "calculated_delay_days" if "calculated_delay_days" in shipments_df.columns else "delay_days"
    if delay_col not in shipments_df.columns:
        if "actual_delivery" in shipments_df.columns and "expected_delivery" in shipments_df.columns:
            shipments_df = shipments_df.copy()
            shipments_df["calculated_delay_days"] = (
                pd.to_datetime(shipments_df["actual_delivery"]) - pd.to_datetime(shipments_df["expected_delivery"])
            ).dt.days.clip(lower=0)
            delay_col = "calculated_delay_days"
        elif "actual_delivery_date" in shipments_df.columns and "estimated_delivery_date" in shipments_df.columns:
            shipments_df = shipments_df.copy()
            shipments_df["calculated_delay_days"] = (
                pd.to_datetime(shipments_df["actual_delivery_date"]) - pd.to_datetime(shipments_df["estimated_delivery_date"])
            ).dt.days.clip(lower=0)
            delay_col = "calculated_delay_days"
        else:
            return pd.DataFrame({"supplier_id": shipments_df["supplier_id"].unique(), "avg_delay_days": 0.0, "delay_risk": 0.0})

    avg_delay = shipments_df.groupby("supplier_id")[delay_col].mean().reset_index()
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
    Dependency Risk: measures the supplier's exposure based on product criticality
    and sourcing concentration (fewer suppliers per critical SKU = higher dependency risk).
    """
    supplier_counts = supplier_product_df.groupby("product_id")["supplier_id"].nunique().reset_index()
    supplier_counts.columns = ["product_id", "supplier_count"]

    merged = supplier_product_df.merge(supplier_counts, on="product_id")
    merged = merged.merge(products_df[["product_id", "criticality"]], on="product_id")

    crit_map = {"critical": 3.0, "high": 2.0, "medium": 1.0, "low": 0.5}
    merged["crit_weight"] = merged["criticality"].astype(str).str.lower().map(lambda c: crit_map.get(c, 1.0))
    merged["dependency_points"] = merged["crit_weight"] / merged["supplier_count"].clip(lower=1)

    dependency = merged.groupby("supplier_id")["dependency_points"].sum().reset_index()
    dependency["dependency_risk"] = normalize_0_100(dependency["dependency_points"], higher_is_riskier=True)
    return dependency[["supplier_id", "dependency_risk"]]


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
        bins=[-0.01, 45, 65, 80, 100],
        labels=["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    )

    return risk_df.sort_values("supplier_risk_score", ascending=False).reset_index(drop=True)