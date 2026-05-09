# AI Usage

This document covers where, when, and how AI (Claude via Claude Code CLI) was used in this project, what was validated, and what was accepted or changed.

---

## 1. Original notebook solution — one AI-assisted snippet

**Where:** `notebooks/00_eda.ipynb` and `notebooks/01_generate_daily_summary_report.ipynb`

**What:** The notebook solution was written by hand. One exception: the type-enforcement loop that casts each column to its target dtype was AI-generated and is marked with a comment (`## used AI to create the below`).

**Validation:** Ran the cell and inspected `df_txn.dtypes` output to confirm each column landed on the correct type.

**Accepted as-is:** Yes — the loop handled all edge cases cleanly (unknown columns skipped, errors coerced).

---

## 2. Code review — bug identification

**When:** After the initial notebook solution was complete.

**What:** Asked AI to review the full solution against the spec. It identified two bugs in `aggregate_data`:

| Bug | Detail |
|-----|--------|
| Dead column reorder | `df_fact[["date", "store_id", "store_name", ...]]` result was not assigned back, so `store_name` ended up last in the CSV |
| Missing `index=False` | `to_csv()` wrote a spurious leading integer index column |

It also flagged three minor observations: `validate_transaction_id` not guarding existing rejections, `tx-1011` being unrecoverable without field normalisation, and an unnecessary `list(set(...))` call.

**Validation:** Manually cross-checked the CSV output before and after the fix. Confirmed column order and absence of index column.

**Accepted:** Both bugs fixed. Minor observations noted in `docs/solution_analysis.md` but not acted on — they are either harmless or acceptable trade-offs within the time constraint.

---

## 3. CLI architecture — design and structure

**When:** After deciding to extend the solution with a CLI tool.

**What:** Asked AI to outline a CLI approach without writing code. It proposed:
- A `src/plexure/` package split into `pipeline.py`, `io.py`, and `cli.py`
- `typer` as the CLI framework (over `click`) for its type-hint driven interface
- A `--quality-report` flag to export rejected rows
- A `--verbose` flag to print a quality summary to stderr
- Entry point wired via `pyproject.toml`

**Validation:** Reviewed the outline before approving implementation. Asked a follow-up question on typer vs click before proceeding.

**Changes made:** Accepted the structure and framework choice. The quality report idea was added after asking about it separately — it was not in the original outline.

---

## 4. TDD implementation — tests, code, refactor

**When:** Implementation phase, following the red/green/refactor cycle documented in `CLAUDE.md`.

### Red — failing tests

AI wrote all tests across three files (`test_pipeline.py`, `test_io.py`, `test_cli.py`) covering:
- Each validator in isolation, including the "does not overwrite existing rejection" guard that was missing from the original notebook
- `run_pipeline` integration test against a fixture mirroring the real 13-row dataset
- `aggregate_data` metrics verified per store per day
- `build_quality_report` totals and breakdown
- IO helpers: type coercion, missing columns, output format, parent directory creation
- CLI: exit code, column order, no index column, store filtering, quality report file

**Validation:** Confirmed all tests failed before any implementation existed (import errors = true red).

### Green — implementation

AI wrote `pipeline.py`, `io.py`, and `cli.py`. All 46 tests passed on first run.

**Validation:** Ran `uv run pytest -q` — 46/46 passed. Then smoke-tested the CLI against real data and confirmed the output matched the notebook results exactly.

**Changes made:** The `validate_transaction_id` function was improved over the notebook version — it now guards against overwriting existing rejection reasons (the notebook did not, relying on pipeline order instead).

### Refactor

AI proposed two changes:
1. Extract `_untagged(df)` helper to remove the repeated `df["_rejection_reason"].eq("")` pattern across all validators
2. Replace slice mutation (`valid["date"] = ...`) with `.assign()` to avoid `SettingWithCopyWarning`

**Validation:** Ran tests again after refactor — still 46/46.

**Accepted:** Both changes accepted. Clean, no behaviour change.

---

## 5. Documentation

**What AI wrote:**
- `CLAUDE.md` — project conventions, TDD workflow, layering rules, CLI design, business rules for future AI agents working in this repo
- `docs/solution_analysis.md` — structured analysis of the notebook solution including bug findings
- `README.md` — full usage guide, input schemas, business rules, data quality table, project structure, dev instructions

**Validation:** Read each document and checked accuracy against the actual code and spec. CLI flags, column names, rejection reasons, and sample output were all verified against live runs.

**Changes made:** None — content was accurate on first pass.

---

## Summary

| Area | AI role | Validated by |
|------|---------|-------------|
| Type coercion loop | Generated snippet | Inspecting dtype output |
| Bug identification | Code review | Manual CSV inspection |
| CLI design | Architecture outline | Review before approving |
| Tests | Wrote all 46 | Confirmed red before green |
| Implementation | Wrote all three modules | 46/46 tests + smoke test |
| Refactor | Proposed two improvements | Tests still passing |
| Documentation | Wrote all docs | Manual read + live verification |
