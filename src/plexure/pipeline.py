from typing import List
import pandas as pd
from pandas import DataFrame


def validate_transaction_id(data: DataFrame, col: str = "transaction_id") -> DataFrame:
    df = data.copy()
    empty_mask = df["_rejection_reason"].eq("") & df[col].astype(str).str.strip().eq("")
    duplicate_mask = df["_rejection_reason"].eq("") & ~empty_mask & df[col].duplicated(keep="first")
    df.loc[empty_mask, "_rejection_reason"] = "missing_transaction_id"
    df.loc[duplicate_mask, "_rejection_reason"] = "duplicate_transaction_id"
    return df


def validate_store_id(data: DataFrame, valid_stores: List[str], col: str = "store_id") -> DataFrame:
    df = data.copy()
    missing_mask = df["_rejection_reason"].eq("") & (
        df[col].isna() | df[col].astype(str).str.strip().eq("")
    )
    invalid_mask = df["_rejection_reason"].eq("") & ~missing_mask & ~df[col].isin(valid_stores)
    df.loc[missing_mask, "_rejection_reason"] = "missing_store"
    df.loc[invalid_mask, "_rejection_reason"] = "invalid_store_id"
    return df


def validate_timestamp(data: DataFrame, col: str = "timestamp") -> DataFrame:
    df = data.copy()
    mask = df["_rejection_reason"].eq("") & df[col].isna()
    df.loc[mask, "_rejection_reason"] = "invalid_timestamp"
    return df


def validate_net_amount(data: DataFrame, col: str = "net_amount") -> DataFrame:
    df = data.copy()
    mask = df["_rejection_reason"].eq("") & pd.to_numeric(df[col], errors="coerce").isna()
    df.loc[mask, "_rejection_reason"] = "non_numeric_amount"
    return df


def run_pipeline(data: DataFrame, valid_stores: List[str]) -> DataFrame:
    df = data.copy()
    df = validate_transaction_id(df)
    df = validate_store_id(df, valid_stores)
    df = validate_timestamp(df)
    df = validate_net_amount(df)
    return df


def aggregate_data(transaction_data: DataFrame, stores_data: DataFrame) -> DataFrame:
    valid = transaction_data[transaction_data["_rejection_reason"].eq("")].copy()
    valid["date"] = pd.to_datetime(valid["timestamp"], errors="coerce").dt.date

    df_agg = (
        valid.groupby(["date", "store_id"])
        .agg(
            total_sales_nzd=("net_amount", "sum"),
            unique_customers=("customer_id", "nunique"),
            average_invoice_nzd=("net_amount", "mean"),
            max_invoice_nzd=("net_amount", "max"),
            min_invoice_nzd=("net_amount", "min"),
        )
        .reset_index()
    )

    df_fact = (
        df_agg
        .merge(stores_data[["store_id", "store_name"]], on="store_id", how="left")
        .sort_values(["date", "store_id"])
    )
    return df_fact[["date", "store_id", "store_name", "total_sales_nzd",
                     "unique_customers", "average_invoice_nzd", "max_invoice_nzd", "min_invoice_nzd"]]


def build_quality_report(data: DataFrame) -> dict:
    total = len(data)
    breakdown = (
        data[data["_rejection_reason"].ne("")]
        ["_rejection_reason"]
        .value_counts()
        .to_dict()
    )
    n_rejected = sum(breakdown.values())
    n_valid = total - n_rejected
    return {
        "total": total,
        "valid": n_valid,
        "rejected": n_rejected,
        "pass_rate": round(n_valid / total * 100, 2) if total > 0 else 0.0,
        "breakdown": breakdown,
    }
