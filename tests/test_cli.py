import json
import csv
import pytest
from pathlib import Path
from typer.testing import CliRunner

from plexure.cli import app

runner = CliRunner()


@pytest.fixture
def stores_csv(tmp_path):
    p = tmp_path / "stores.csv"
    p.write_text(
        "store_id,store_name,region\n"
        "akl-001,Auckland Central,Auckland\n"
        "wlg-001,Wellington Lambton Quay,Wellington\n"
    )
    return p


@pytest.fixture
def transactions_json(tmp_path):
    data = [
        {"transaction_id": "tx-001", "store_id": "akl-001",
         "timestamp": "2026-04-01T10:00:00+13:00", "customer_id": "cust-001", "net_amount": 115.0},
        {"transaction_id": "tx-002", "store_id": "akl-001",
         "timestamp": "2026-04-01T12:00:00+13:00", "customer_id": "cust-002", "net_amount": 57.5},
        {"transaction_id": "tx-003", "store_id": "unknown-999",
         "timestamp": "2026-04-01T14:00:00+13:00", "customer_id": "cust-003", "net_amount": 30.0},
    ]
    p = tmp_path / "transactions.json"
    p.write_text(json.dumps(data))
    return p


class TestCLIBasic:
    def test_exit_code_zero(self, tmp_path, stores_csv, transactions_json):
        result = runner.invoke(app, [
            "--stores", str(stores_csv),
            "--transactions", str(transactions_json),
            "--output", str(tmp_path / "out.csv"),
        ])
        assert result.exit_code == 0, result.output

    def test_output_file_created(self, tmp_path, stores_csv, transactions_json):
        out = tmp_path / "out.csv"
        runner.invoke(app, [
            "--stores", str(stores_csv),
            "--transactions", str(transactions_json),
            "--output", str(out),
        ])
        assert out.exists()


class TestCLIOutput:
    def test_csv_column_order(self, tmp_path, stores_csv, transactions_json):
        out = tmp_path / "out.csv"
        runner.invoke(app, [
            "--stores", str(stores_csv),
            "--transactions", str(transactions_json),
            "--output", str(out),
        ])
        with open(out) as f:
            cols = next(csv.reader(f))
        assert cols[0] == "date"
        assert cols[2] == "store_name"

    def test_no_index_column(self, tmp_path, stores_csv, transactions_json):
        out = tmp_path / "out.csv"
        runner.invoke(app, [
            "--stores", str(stores_csv),
            "--transactions", str(transactions_json),
            "--output", str(out),
        ])
        assert not out.read_text().splitlines()[0].startswith(",")

    def test_invalid_store_excluded(self, tmp_path, stores_csv, transactions_json):
        out = tmp_path / "out.csv"
        runner.invoke(app, [
            "--stores", str(stores_csv),
            "--transactions", str(transactions_json),
            "--output", str(out),
        ])
        assert "unknown-999" not in out.read_text()


class TestCLIQualityReport:
    def test_quality_report_file_written(self, tmp_path, stores_csv, transactions_json):
        out = tmp_path / "out.csv"
        qr = tmp_path / "quality.csv"
        result = runner.invoke(app, [
            "--stores", str(stores_csv),
            "--transactions", str(transactions_json),
            "--output", str(out),
            "--quality-report", str(qr),
        ])
        assert result.exit_code == 0
        assert qr.exists()

    def test_quality_report_contains_rejected_rows(self, tmp_path, stores_csv, transactions_json):
        out = tmp_path / "out.csv"
        qr = tmp_path / "quality.csv"
        runner.invoke(app, [
            "--stores", str(stores_csv),
            "--transactions", str(transactions_json),
            "--output", str(out),
            "--quality-report", str(qr),
        ])
        assert "unknown-999" in qr.read_text()
