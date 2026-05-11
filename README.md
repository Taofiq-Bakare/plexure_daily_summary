# Plexure Data Engineering

This repository contains a take-home technical exercise for processing store daily sales summaries.

## Prerequisites

This project uses [uv](https://github.com/astral-sh/uv) to manage Python dependencies.

You can install `uv` by following the instructions on their [official documentation](https://docs.astral.sh/uv/getting-started/installation/):

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Setup

1. **Sync dependencies**: Create a virtual environment and install required packages (`pandas`, `jupyter`, `ipython`):
   ```bash
   uv sync
   ```

## Running the Notebooks

The core logic and data exploration are located in the `notebooks/` directory.

### Option 1: Visual Studio Code (Recommended)
1. Open the project in VS Code.
2. Ensure the **Python** and **Jupyter** extensions are installed.
3. Open `notebooks/01_generate_daily_summary_report.ipynb`.
4. Select the `.venv` kernel created by `uv` (top right corner).
5. Click **Run All**.

### Option 2: Jupyter Notebook Server
1. Start the server using `uv`:
   ```bash
   uv run jupyter notebook
   ```
2. In the Jupyter interface, navigate to the `notebooks/` folder.
3. Open and run `01_generate_daily_summary_report.ipynb`.

## Project Structure

- `data/raw/`: Input datasets (`stores.csv`, `sales_transactions.json`).
- `data/results/`: Output directory for generated reports.
- `docs/`: Original interview task description and requirements.
- `notebooks/`:
    - `00_eda.ipynb`: Exploratory Data Analysis.
    - `01_generate_daily_summary_report.ipynb`: Main data processing pipeline.
- `pyproject.toml` & `uv.lock`: Dependency and environment definitions.
- `src/` & `tests/`: Placeholders for structured Python application and unit tests.

## Business Rules & Requirements
The processing pipeline implements the following:
- Deduplication of transactions via `transaction_id`.
- Filtering of transactions to only include known stores.
- Calculation of daily sales, unique customers, and invoice statistics (mean, max, min) in NZD.
