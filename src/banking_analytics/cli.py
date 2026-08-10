"""Command-line entry point for the banking analytics project."""

from pathlib import Path
from typing import Annotated

import httpx
import typer

from banking_analytics.bcb.cosif import (
    build_source_catalog,
    build_source_inventory,
    read_active_catalog_urls,
    write_source_catalog,
    write_source_inventory,
)

app = typer.Typer(help="Brazilian banking analytics data tools.")


@app.command()
def status() -> None:
    """Show the current implementation status."""
    typer.echo("WP0 source profiling is in progress; checkpoint 0A inventories BCB files.")


@app.command()
def about() -> None:
    """Describe the project domain."""
    typer.echo("Official BCB balance-sheet and macroeconomic analytics showcase.")


@app.command("source-inventory")
def source_inventory(
    start_period: Annotated[str, typer.Option("--start", help="First YYYYMM period.")] = (
        "202501"
    ),
    end_period: Annotated[str, typer.Option("--end", help="Last YYYYMM period.")] = ...,
    output: Annotated[Path, typer.Option("--output", help="Inventory CSV path.")] = Path(
        "artifacts/source_inventory.csv"
    ),
    timeout_seconds: Annotated[float, typer.Option("--timeout", min=1.0)] = 20.0,
    catalog: Annotated[
        Path | None,
        typer.Option("--catalog", help="Catalog CSV used for active source URLs."),
    ] = None,
) -> None:
    """Probe official COSIF bank files and publish an availability inventory."""
    try:
        url_by_period = read_active_catalog_urls(catalog) if catalog else None
        records = build_source_inventory(
            start_period,
            end_period,
            timeout_seconds=timeout_seconds,
            url_by_period=url_by_period,
        )
    except (OSError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc

    written = write_source_inventory(records, output)
    available = [record for record in records if record.available]
    errors = [record for record in records if record.error]
    latest = available[-1].period if available else "none"
    typer.echo(
        f"Wrote {written} periods to {output}; "
        f"available={len(available)}, errors={len(errors)}, latest={latest}."
    )
    if errors:
        raise typer.Exit(code=1)


@app.command("source-catalog")
def source_catalog(
    output: Annotated[Path, typer.Option("--output", help="Catalog CSV path.")] = Path(
        "artifacts/source_catalog.csv"
    ),
    timeout_seconds: Annotated[float, typer.Option("--timeout", min=1.0)] = 20.0,
) -> None:
    """Read the official BCB bank-file catalog and publish its records."""
    try:
        records = build_source_catalog(timeout_seconds=timeout_seconds)
    except (httpx.HTTPError, ValueError) as exc:
        typer.echo(f"BCB bank catalog failed: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    written = write_source_catalog(records, output)
    errors = [record for record in records if record.error]
    periods = [record.period for record in records if record.period]
    active = [record for record in records if record.is_active]
    duplicate_periods = len(records) - len(active)
    latest = max(periods) if periods else "none"
    typer.echo(
        f"Wrote {written} catalog records to {output}; "
        f"active={len(active)}, duplicate_versions={duplicate_periods}, "
        f"errors={len(errors)}, latest={latest}."
    )
    if errors or not periods:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
