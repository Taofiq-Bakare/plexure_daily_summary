from pathlib import Path
import pandas as pd
from pandas import DataFrame

_COL_TYPES = {
    "transaction_id": "str",
    "store_id": "str",
    "timestamp": "timestamp",
    "customer_id": "str",
    "net_amount": "float",
    "store": "str",
}


def load_stores(path: Path) -> DataFrame:
    return pd.read_csv(path)


def load_transactions(path: Path) -> DataFrame:
    df = pd.read_json(path)
    df["_rejection_reason"] = ""
    for col, target in _COL_TYPES.items():
        if col not in df.columns:
            continue
        if target == "str":
            df[col] = df[col].astype("string")
        elif target == "float":
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Float64")
        elif target == "timestamp":
            df[col] = pd.to_datetime(df[col], utc=False, errors="coerce")
    return df


def write_output(df: DataFrame, path: Path, fmt: str = "csv") -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "csv":
        df.to_csv(path, index=False)
    elif fmt == "json":
        df.to_json(path, orient="records", date_format="iso", indent=2)
    elif fmt == "table":
        print(df.to_string(index=False))
    else:
        raise ValueError(f"Unknown format: {fmt!r}")
