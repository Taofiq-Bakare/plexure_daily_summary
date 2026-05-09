# Solution Analysis: Store Daily Sales Summary

## Project Overview

Interview take-home task. Reads `stores.csv` + `sales_transactions.json`, joins them, produces daily sales summary per store.

## Data Quality Issues in Source JSON

Intentional traps in `sales_transactions.json`:

| Row | Issue | Type |
|-----|-------|------|
| tx-1007 | Timestamp `2026-13-01` (month 13 invalid) | invalid_timestamp |
| tx-1011 | Field named `"store"` not `"store_id"` → store_id is null | missing_store |
| tx-1008 | `store_id = "unknown-999"` not in stores | invalid_store_id |
| tx-1010 | `net_amount = "twenty"` (non-numeric string) | non_numeric_amount |
| row 9 | Empty `transaction_id` | missing_transaction_id |
| tx-1004 | Duplicated record | duplicate_transaction_id |
| tx-1009 | `net_amount = null` | non_numeric_amount |

## Solution Approach

Validate-then-aggregate pipeline. Each validator stamps `_rejection_reason` on bad rows. Valid rows flow into groupby aggregation, then left-join to stores for `store_name`.

Pipeline order: `validate_transaction_id` → `validate_store_id` → `validate_timestamp` → `validate_numeric_transactions`

## Output Correctness

Numbers verified manually against raw data:

| date | store_id | total_sales_nzd | unique_customers | avg_invoice | max_invoice | min_invoice |
|------|----------|-----------------|------------------|-------------|-------------|-------------|
| 2026-04-01 | akl-001 | 172.5 | 2 | 86.25 | 115.0 | 57.5 | ✅ |
| 2026-04-01 | wlg-001 | 92.0 | 1 | 92.0 | 92.0 | 92.0 | ✅ |
| 2026-04-02 | chc-001 | 46.0 | 1 | 46.0 | 46.0 | 46.0 | ✅ |
| 2026-04-02 | wlg-001 | 172.5 | 2 | 86.25 | 138.0 | 34.5 | ✅ |

Business rules applied correctly:
- ✅ Deduplicates by `transaction_id`
- ✅ Rejects transactions unmatched to a known store
- ✅ Uses `net_amount` as transaction value
- ✅ `unique_customers` = `nunique(customer_id)` per store per day

## Bugs Found

### Bug 1 — Dead column reorder in `aggregate_data` (`01_generate_daily_summary_report.ipynb`)

```python
# Result not assigned back — this line does nothing
df_fact[["date", "store_id", "store_name", "total_sales_nzd", ...]]
df_fact.to_csv(DAILY_SUMMARY_REPORT_PATH)  # writes wrong column order
```

`store_name` ends up as last column in CSV instead of 3rd. Fix:

```python
df_fact = df_fact[["date", "store_id", "store_name", "total_sales_nzd",
                   "unique_customers", "average_invoice_nzd",
                   "max_invoice_nzd", "min_invoice_nzd"]]
df_fact.to_csv(DAILY_SUMMARY_REPORT_PATH, index=False)
```

### Bug 2 — CSV written with unnamed index column

```python
df_fact.to_csv(DAILY_SUMMARY_REPORT_PATH)  # missing index=False
```

Output CSV has a spurious leading integer index column. Fix: add `index=False`.

## Minor Observations

- `validate_transaction_id` does not guard against overwriting an existing `_rejection_reason` (unlike all other validators). Harmless because it runs first in the pipeline, but inconsistent with the pattern.
- `tx-1011` uses field `"store"` instead of `"store_id"` — correctly rejected as `missing_store`. No attempt to normalise the field name. Pragmatic trade-off; worth discussing in follow-up.
- `valid_store_id = list(set(df_stores['store_id']))` — `set()` is unordered. Harmless here but unnecessary; `df_stores['store_id'].tolist()` is cleaner.
