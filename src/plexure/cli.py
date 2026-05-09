from enum import Enum
from pathlib import Path
from typing import Optional

import typer

from plexure.io import load_stores, load_transactions, write_output
from plexure.pipeline import aggregate_data, build_quality_report, run_pipeline

app = typer.Typer(add_completion=False)


class OutputFormat(str, Enum):
    csv = "csv"
    json = "json"
    table = "table"


@app.command()
def main(
    stores: Path = typer.Option(..., help="Path to stores CSV"),
    transactions: Path = typer.Option(..., help="Path to transactions JSON"),
    output: Path = typer.Option(..., help="Output file path"),
    fmt: OutputFormat = typer.Option(OutputFormat.csv, "--format", help="Output format"),
    quality_report: Optional[Path] = typer.Option(None, help="Write rejection log to this path"),
    verbose: bool = typer.Option(False, help="Print quality report summary to stderr"),
) -> None:
    df_stores = load_stores(stores)
    df_txn = load_transactions(transactions)

    valid_stores = df_stores["store_id"].tolist()
    processed = run_pipeline(df_txn, valid_stores)
    report = build_quality_report(processed)

    if verbose:
        _print_quality_report(report)

    if quality_report:
        rejected = processed[processed["_rejection_reason"].ne("")].copy()
        write_output(rejected, quality_report, fmt="csv")

    result = aggregate_data(processed, df_stores)
    write_output(result, output, fmt=fmt.value)
    typer.echo(f"Written to {output}")


def _print_quality_report(report: dict) -> None:
    typer.echo("", err=True)
    typer.echo("Data Quality Report", err=True)
    typer.echo("─" * 40, err=True)
    typer.echo(f"Total records loaded:  {report['total']}", err=True)
    typer.echo(f"  ✓ Valid:             {report['valid']}  ({report['pass_rate']}%)", err=True)
    typer.echo(f"  ✗ Rejected:          {report['rejected']}", err=True)
    if report["breakdown"]:
        typer.echo("", err=True)
        typer.echo("Rejection breakdown:", err=True)
        for reason, count in report["breakdown"].items():
            typer.echo(f"  {reason:<32} {count}", err=True)
    typer.echo("", err=True)
