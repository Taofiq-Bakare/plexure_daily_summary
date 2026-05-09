import pytest
import pandas as pd
from pandas import DataFrame

from plexure.pipeline import (
    validate_transaction_id,
    validate_store_id,
    validate_timestamp,
    validate_net_amount,
    run_pipeline,
    aggregate_data,
    build_quality_report,
)

VALID_STORES = ["akl-001", "akl-002", "wlg-001", "chc-001", "dun-001"]


def make_df(**overrides) -> DataFrame:
    data = {
        "transaction_id": pd.array(["tx-001"], dtype="string"),
        "store_id": pd.array(["akl-001"], dtype="string"),
        "timestamp": pd.to_datetime(["2026-04-01T10:00:00+13:00"], utc=False, errors="coerce"),
        "customer_id": pd.array(["cust-001"], dtype="string"),
        "net_amount": pd.array([100.0], dtype="Float64"),
        "_rejection_reason": [""],
    }
    data.update(overrides)
    return DataFrame(data)


class TestValidateTransactionId:
    def test_flags_empty_string(self):
        df = make_df(transaction_id=pd.array([""], dtype="string"))
        result = validate_transaction_id(df)
        assert result.loc[0, "_rejection_reason"] == "missing_transaction_id"

    def test_flags_duplicate_keeps_first(self):
        df = DataFrame({
            "transaction_id": pd.array(["tx-001", "tx-001"], dtype="string"),
            "store_id": pd.array(["akl-001", "akl-001"], dtype="string"),
            "timestamp": pd.to_datetime(["2026-04-01T10:00:00+13:00"] * 2, utc=False),
            "customer_id": pd.array(["cust-001", "cust-001"], dtype="string"),
            "net_amount": pd.array([100.0, 100.0], dtype="Float64"),
            "_rejection_reason": ["", ""],
        })
        result = validate_transaction_id(df)
        assert result.loc[0, "_rejection_reason"] == ""
        assert result.loc[1, "_rejection_reason"] == "duplicate_transaction_id"

    def test_does_not_overwrite_existing_rejection(self):
        df = make_df(_rejection_reason=["prior_error"])
        result = validate_transaction_id(df)
        assert result.loc[0, "_rejection_reason"] == "prior_error"

    def test_valid_row_unchanged(self):
        result = validate_transaction_id(make_df())
        assert result.loc[0, "_rejection_reason"] == ""


class TestValidateStoreId:
    def test_flags_null_store_id(self):
        df = make_df(store_id=pd.array([pd.NA], dtype="string"))
        result = validate_store_id(df, VALID_STORES)
        assert result.loc[0, "_rejection_reason"] == "missing_store"

    def test_flags_unknown_store_id(self):
        df = make_df(store_id=pd.array(["unknown-999"], dtype="string"))
        result = validate_store_id(df, VALID_STORES)
        assert result.loc[0, "_rejection_reason"] == "invalid_store_id"

    def test_does_not_overwrite_existing_rejection(self):
        df = make_df(store_id=pd.array(["unknown-999"], dtype="string"), _rejection_reason=["prior_error"])
        result = validate_store_id(df, VALID_STORES)
        assert result.loc[0, "_rejection_reason"] == "prior_error"

    def test_valid_store_unchanged(self):
        result = validate_store_id(make_df(), VALID_STORES)
        assert result.loc[0, "_rejection_reason"] == ""


class TestValidateTimestamp:
    def test_flags_nat(self):
        df = make_df(timestamp=pd.to_datetime([pd.NaT], utc=False, errors="coerce"))
        result = validate_timestamp(df)
        assert result.loc[0, "_rejection_reason"] == "invalid_timestamp"

    def test_does_not_overwrite_existing_rejection(self):
        df = make_df(
            timestamp=pd.to_datetime([pd.NaT], utc=False, errors="coerce"),
            _rejection_reason=["prior_error"],
        )
        result = validate_timestamp(df)
        assert result.loc[0, "_rejection_reason"] == "prior_error"

    def test_valid_timestamp_unchanged(self):
        result = validate_timestamp(make_df())
        assert result.loc[0, "_rejection_reason"] == ""


class TestValidateNetAmount:
    def test_flags_null_amount(self):
        df = make_df(net_amount=pd.array([pd.NA], dtype="Float64"))
        result = validate_net_amount(df)
        assert result.loc[0, "_rejection_reason"] == "non_numeric_amount"

    def test_does_not_overwrite_existing_rejection(self):
        df = make_df(net_amount=pd.array([pd.NA], dtype="Float64"), _rejection_reason=["prior_error"])
        result = validate_net_amount(df)
        assert result.loc[0, "_rejection_reason"] == "prior_error"

    def test_valid_amount_unchanged(self):
        result = validate_net_amount(make_df())
        assert result.loc[0, "_rejection_reason"] == ""


class TestRunPipeline:
    @pytest.fixture
    def raw_transactions(self):
        return DataFrame({
            "transaction_id": pd.array(
                ["tx-1001", "tx-1007", "tx-1003", "tx-1011", "tx-1002",
                 "tx-1008", "tx-1004", "tx-1010", "tx-1005", "",
                 "tx-1006", "tx-1004", "tx-1009"],
                dtype="string",
            ),
            "store_id": pd.array(
                ["akl-001", "akl-001", "wlg-001", pd.NA, "akl-001",
                 "unknown-999", "chc-001", "wlg-001", "wlg-001", "akl-001",
                 "wlg-001", "chc-001", "akl-002"],
                dtype="string",
            ),
            "timestamp": pd.to_datetime(
                ["2026-04-01T10:00:00+13:00", None, "2026-04-01T09:30:00+13:00",
                 "2026-04-02T12:00:00+13:00", "2026-04-01T12:00:00+13:00",
                 "2026-04-02T10:00:00+13:00", "2026-04-02T11:00:00+13:00",
                 "2026-04-02T18:00:00+13:00", "2026-04-02T14:30:00+13:00",
                 "2026-04-02T15:30:00+13:00", "2026-04-02T16:10:00+13:00",
                 "2026-04-02T11:00:00+13:00", "2026-04-02T15:00:00+13:00"],
                utc=False, errors="coerce",
            ),
            "customer_id": pd.array(
                ["cust-001", "cust-006", "cust-003", "cust-010", "cust-002",
                 "cust-007", "cust-004", "cust-009", "cust-003", "cust-011",
                 "cust-005", "cust-004", "cust-008"],
                dtype="string",
            ),
            "net_amount": pd.array(
                [115.0, 34.5, 92.0, 69.0, 57.5,
                 23.0, 46.0, pd.NA, 34.5, 11.5,
                 138.0, 46.0, pd.NA],
                dtype="Float64",
            ),
            "_rejection_reason": [""] * 13,
        })

    def test_valid_count(self, raw_transactions):
        result = run_pipeline(raw_transactions, VALID_STORES)
        assert result["_rejection_reason"].eq("").sum() == 6

    def test_rejected_count(self, raw_transactions):
        result = run_pipeline(raw_transactions, VALID_STORES)
        assert result["_rejection_reason"].ne("").sum() == 7

    def test_rejection_breakdown(self, raw_transactions):
        result = run_pipeline(raw_transactions, VALID_STORES)
        reasons = result[result["_rejection_reason"].ne("")]["_rejection_reason"].value_counts().to_dict()
        assert reasons["non_numeric_amount"] == 2
        assert reasons["duplicate_transaction_id"] == 1
        assert reasons["missing_transaction_id"] == 1
        assert reasons["invalid_timestamp"] == 1
        assert reasons["invalid_store_id"] == 1
        assert reasons["missing_store"] == 1


class TestAggregateData:
    @pytest.fixture
    def valid_transactions(self):
        return DataFrame({
            "transaction_id": pd.array(
                ["tx-1001", "tx-1002", "tx-1003", "tx-1004", "tx-1005", "tx-1006"],
                dtype="string",
            ),
            "store_id": pd.array(
                ["akl-001", "akl-001", "wlg-001", "chc-001", "wlg-001", "wlg-001"],
                dtype="string",
            ),
            "timestamp": pd.to_datetime(
                ["2026-04-01T10:00:00+13:00", "2026-04-01T12:00:00+13:00",
                 "2026-04-01T09:30:00+13:00", "2026-04-02T11:00:00+13:00",
                 "2026-04-02T14:30:00+13:00", "2026-04-02T16:10:00+13:00"],
                utc=False,
            ),
            "customer_id": pd.array(
                ["cust-001", "cust-002", "cust-003", "cust-004", "cust-003", "cust-005"],
                dtype="string",
            ),
            "net_amount": pd.array([115.0, 57.5, 92.0, 46.0, 34.5, 138.0], dtype="Float64"),
            "_rejection_reason": [""] * 6,
        })

    @pytest.fixture
    def stores(self):
        return DataFrame({
            "store_id": ["akl-001", "akl-002", "wlg-001", "chc-001", "dun-001"],
            "store_name": ["Auckland Central", "Auckland Newmarket",
                           "Wellington Lambton Quay", "Christchurch Riccarton",
                           "Dunedin George Street"],
            "region": ["Auckland", "Auckland", "Wellington", "Canterbury", "Otago"],
        })

    def test_output_columns(self, valid_transactions, stores):
        result = aggregate_data(valid_transactions, stores)
        expected = ["date", "store_id", "store_name", "total_sales_nzd",
                    "unique_customers", "average_invoice_nzd", "max_invoice_nzd", "min_invoice_nzd"]
        assert list(result.columns) == expected

    def test_row_count(self, valid_transactions, stores):
        assert len(aggregate_data(valid_transactions, stores)) == 4

    def test_akl001_metrics(self, valid_transactions, stores):
        row = aggregate_data(valid_transactions, stores).query("store_id == 'akl-001'").iloc[0]
        assert float(row["total_sales_nzd"]) == 172.5
        assert row["unique_customers"] == 2
        assert float(row["average_invoice_nzd"]) == 86.25
        assert float(row["max_invoice_nzd"]) == 115.0
        assert float(row["min_invoice_nzd"]) == 57.5

    def test_wlg001_apr02_metrics(self, valid_transactions, stores):
        result = aggregate_data(valid_transactions, stores)
        row = result[(result["store_id"] == "wlg-001") & (result["date"].astype(str) == "2026-04-02")].iloc[0]
        assert float(row["total_sales_nzd"]) == 172.5
        assert row["unique_customers"] == 2
        assert float(row["max_invoice_nzd"]) == 138.0
        assert float(row["min_invoice_nzd"]) == 34.5

    def test_store_name_present(self, valid_transactions, stores):
        result = aggregate_data(valid_transactions, stores)
        assert "Auckland Central" in result["store_name"].values


class TestBuildQualityReport:
    @pytest.fixture
    def processed(self):
        return DataFrame({
            "_rejection_reason": [
                "", "", "", "", "", "",
                "non_numeric_amount", "non_numeric_amount",
                "duplicate_transaction_id",
                "missing_transaction_id",
                "invalid_timestamp",
                "invalid_store_id",
                "missing_store",
            ]
        })

    def test_total(self, processed):
        assert build_quality_report(processed)["total"] == 13

    def test_valid_count(self, processed):
        assert build_quality_report(processed)["valid"] == 6

    def test_rejected_count(self, processed):
        assert build_quality_report(processed)["rejected"] == 7

    def test_pass_rate(self, processed):
        assert build_quality_report(processed)["pass_rate"] == round(6 / 13 * 100, 2)

    def test_breakdown(self, processed):
        bd = build_quality_report(processed)["breakdown"]
        assert bd["non_numeric_amount"] == 2
        assert bd["duplicate_transaction_id"] == 1
