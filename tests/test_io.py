import json
import pytest
import pandas as pd
from pathlib import Path

from plexure.io import load_stores, load_transactions, write_output


@pytest.fixture
def stores_csv(tmp_path):
    p = tmp_path / "stores.csv"
    p.write_text("store_id,store_name,region\nakl-001,Auckland Central,Auckland\n")
    return p


@pytest.fixture
def transactions_json(tmp_path):
    data = [
        {"transaction_id": "tx-001", "store_id": "akl-001",
         "timestamp": "2026-04-01T10:00:00+13:00", "customer_id": "cust-001", "net_amount": 100.0},
        {"transaction_id": "tx-002", "store_id": "akl-001",
         "timestamp": "2026-04-01T11:00:00+13:00", "customer_id": "cust-002", "net_amount": "twenty"},
    ]
    p = tmp_path / "transactions.json"
    p.write_text(json.dumps(data))
    return p


@pytest.fixture
def sample_df():
    import datetime
    return pd.DataFrame({
        "date": [datetime.date(2026, 4, 1)],
        "store_id": ["akl-001"],
        "store_name": ["Auckland Central"],
        "total_sales_nzd": [172.5],
        "unique_customers": [2],
        "average_invoice_nzd": [86.25],
        "max_invoice_nzd": [115.0],
        "min_invoice_nzd": [57.5],
    })


class TestLoadStores:
    def test_returns_expected_columns(self, stores_csv):
        df = load_stores(stores_csv)
        assert list(df.columns) == ["store_id", "store_name", "region"]

    def test_row_count(self, stores_csv):
        assert len(load_stores(stores_csv)) == 1

    def test_store_id_value(self, stores_csv):
        assert load_stores(stores_csv).loc[0, "store_id"] == "akl-001"


class TestLoadTransactions:
    def test_adds_rejection_reason_column(self, transactions_json):
        df = load_transactions(transactions_json)
        assert "_rejection_reason" in df.columns
        assert df["_rejection_reason"].eq("").all()

    def test_non_numeric_amount_coerced_to_na(self, transactions_json):
        df = load_transactions(transactions_json)
        assert pd.isna(df.loc[1, "net_amount"])

    def test_timestamp_parsed_as_datetime(self, transactions_json):
        df = load_transactions(transactions_json)
        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])

    def test_row_count(self, transactions_json):
        assert len(load_transactions(transactions_json)) == 2


class TestWriteOutput:
    def test_writes_csv_no_index(self, tmp_path, sample_df):
        out = tmp_path / "out.csv"
        write_output(sample_df, out, fmt="csv")
        first_line = out.read_text().splitlines()[0]
        assert first_line.startswith("date,")

    def test_csv_contains_data(self, tmp_path, sample_df):
        out = tmp_path / "out.csv"
        write_output(sample_df, out, fmt="csv")
        assert "akl-001" in out.read_text()

    def test_writes_json(self, tmp_path, sample_df):
        out = tmp_path / "out.json"
        write_output(sample_df, out, fmt="json")
        assert out.exists()

    def test_creates_parent_dirs(self, tmp_path, sample_df):
        out = tmp_path / "nested" / "dir" / "out.csv"
        write_output(sample_df, out, fmt="csv")
        assert out.exists()

    def test_invalid_format_raises(self, tmp_path, sample_df):
        with pytest.raises(ValueError, match="Unknown format"):
            write_output(sample_df, tmp_path / "out.xyz", fmt="xyz")
