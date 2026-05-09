# Plexure Data Engineering — Project Instructions

## Task

Read `stores.csv` + `sales_transactions.json`, join them, produce a daily sales summary per store with a data quality report.

## Development Workflow: TDD

Follow strict red/green/refactor with a commit at each stage:

1. **Red** — write a failing test first. Commit it.
2. **Green** — write the minimal code to make it pass. Commit it.
3. **Refactor** — clean up without changing behaviour. Tests must still pass. Commit it.

Never write implementation before a test exists for it.

## Project Structure

```
plexure_data_engineering/
├── src/
│   └── plexure/
│       ├── __init__.py
│       ├── pipeline.py   # validation + aggregation — pure DataFrame → DataFrame, no file I/O
│       ├── io.py         # load_stores(), load_transactions(), write_output()
│       └── cli.py        # typer entry point
├── tests/
│   ├── test_pipeline.py
│   └── test_io.py
├── notebooks/            # EDA and reference only — do not put production logic here
├── data/                 # gitignored
└── pyproject.toml
```

## Tech Stack

- **CLI**: `typer` (built on Click — less boilerplate, type-hint driven)
- **Data**: `pandas`
- **Tests**: `pytest`
- **Package manager**: `uv`

## Business Rules (from spec)

- Use `net_amount` as transaction value
- Only include transactions matched to a known store
- Deduplicate by `transaction_id`
- `unique_customers` = distinct `customer_id` per store per day
- All amounts are NZD

## CLI Interface

```bash
plexure-summary \
  --stores data/raw/stores.csv \
  --transactions data/raw/sales_transactions.json \
  --output data/results/daily_summary.csv \
  --format csv \       # csv | json | table
  --verbose            # print quality report to stderr
```

Entry point registered in `pyproject.toml`:
```toml
[project.scripts]
plexure-summary = "plexure.cli:app"
```

## Quality Report

Pipeline tags every rejected row with `_rejection_reason`. Before filtering, emit a summary:
- Total records loaded
- Valid / rejected counts + %
- Breakdown by rejection reason
- Full rejection log optionally written to `--quality-report <path>`

## Layering Rules

- `pipeline.py` — no file paths, no CLI concerns; takes DataFrames, returns DataFrames
- `io.py` — all file I/O; knows nothing about validation logic
- `cli.py` — orchestrates io + pipeline; owns exit codes and user-facing output
- Notebooks may import from `plexure.*` but production logic must not live in notebooks
