# Plexure Data Engineering

A CLI pipeline that reads store reference data and sales transactions, validates data quality, and produces a daily sales summary per store.

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)

## Installation

```bash
git clone <repo-url>
cd plexure_data_engineering
uv sync
```

## Usage

```bash
uv run plexure-summary \
  --stores data/raw/stores.csv \
  --transactions data/raw/sales_transactions.json \
  --output data/results/daily_summary.csv
```

### Options

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--stores` | Yes | — | Path to stores CSV |
| `--transactions` | Yes | — | Path to transactions JSON |
| `--output` | Yes | — | Output file path |
| `--format` | No | `csv` | Output format: `csv`, `json`, or `table` |
| `--quality-report` | No | — | Write rejected rows to this path |
| `--verbose` | No | `false` | Print data quality summary to stderr |

### Example with all options

```bash
uv run plexure-summary \
  --stores data/raw/stores.csv \
  --transactions data/raw/sales_transactions.json \
  --output data/results/daily_summary.csv \
  --format csv \
  --quality-report data/results/rejected.csv \
  --verbose
```

### Sample output

```
Data Quality Report
────────────────────────────────────────
Total records loaded:  13
  ✓ Valid:             6  (46.15%)
  ✗ Rejected:          7

Rejection breakdown:
  non_numeric_amount               2
  invalid_timestamp                1
  missing_store                    1
  invalid_store_id                 1
  missing_transaction_id           1
  duplicate_transaction_id         1
```

```csv
date,store_id,store_name,total_sales_nzd,unique_customers,average_invoice_nzd,max_invoice_nzd,min_invoice_nzd
2026-04-01,akl-001,Auckland Central,172.5,2,86.25,115.0,57.5
2026-04-01,wlg-001,Wellington Lambton Quay,92.0,1,92.0,92.0,92.0
2026-04-02,chc-001,Christchurch Riccarton,46.0,1,46.0,46.0,46.0
2026-04-02,wlg-001,Wellington Lambton Quay,172.5,2,86.25,138.0,34.5
```

## Inputs

### `stores.csv`

| Column | Type | Description |
|--------|------|-------------|
| `store_id` | string | Unique store identifier |
| `store_name` | string | Display name |
| `region` | string | Geographic region |

### `sales_transactions.json`

JSON array of transaction records.

| Field | Type | Description |
|-------|------|-------------|
| `transaction_id` | string | Unique transaction identifier |
| `store_id` | string | Store where transaction occurred |
| `timestamp` | ISO 8601 | Transaction datetime with timezone |
| `customer_id` | string | Customer identifier |
| `net_amount` | number | Transaction value in NZD |

## Business Rules

- Use `net_amount` as the transaction value (all amounts are NZD)
- Only include transactions matched to a known store
- Deduplicate transactions by `transaction_id` (keep first occurrence)
- `unique_customers` = distinct `customer_id` values per store per day

## Data Quality

Each transaction is validated before aggregation. Invalid rows are tagged with a rejection reason and excluded from the summary:

| Rejection reason | Cause |
|-----------------|-------|
| `missing_transaction_id` | Empty `transaction_id` |
| `duplicate_transaction_id` | Same `transaction_id` seen more than once |
| `missing_store` | Null or missing `store_id` |
| `invalid_store_id` | `store_id` not found in stores reference |
| `invalid_timestamp` | Unparseable timestamp |
| `non_numeric_amount` | `net_amount` is non-numeric or null |

Use `--quality-report` to export all rejected rows with their rejection reasons.

## Project Structure

```
plexure_data_engineering/
├── src/
│   └── plexure/
│       ├── pipeline.py   # validation and aggregation logic
│       ├── io.py         # file loading and writing
│       └── cli.py        # CLI entry point (typer)
├── tests/
│   ├── test_pipeline.py
│   ├── test_io.py
│   └── test_cli.py
├── notebooks/            # EDA and reference
├── docs/
│   ├── intervew_task.pdf
│   └── solution_analysis.md
└── pyproject.toml
```

## Development

```bash
# Install with dev dependencies
uv sync

# Run tests
uv run pytest

# Run tests with output
uv run pytest -v
```

Tests follow a TDD red/green/refactor cycle with a commit at each stage.
