"""Command-line entry point for the banking analytics project."""

import zipfile
from datetime import date
from pathlib import Path
from typing import Annotated

import httpx
import psycopg
import typer

from banking_analytics.bcb.cosif import (
    build_source_catalog,
    build_source_inventory,
    read_active_catalog_urls,
    write_source_catalog,
    write_source_inventory,
)
from banking_analytics.pipelines.fixtures import (
    run_fixture_pipelines,
    verify_fixture_landing,
    write_fixture_controls,
)
from banking_analytics.settings import WarehouseSettings
from banking_analytics.sources.cosif import (
    download_catalog_files,
    profile_downloads,
    read_complete_downloads,
    write_download_manifest,
    write_source_profile,
)
from banking_analytics.sources.sgs import (
    profile_macro_series,
    read_macro_registry,
    write_macro_observations,
    write_macro_profile,
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


@app.command("download-cosif")
def download_cosif(
    start_period: Annotated[str, typer.Option("--start", help="First YYYYMM period.")],
    end_period: Annotated[str, typer.Option("--end", help="Last YYYYMM period.")],
    catalog: Annotated[Path, typer.Option("--catalog", help="Catalog CSV path.")],
    download_dir: Annotated[Path, typer.Option("--download-dir")] = Path(
        "data/downloads/cosif"
    ),
    manifest: Annotated[Path, typer.Option("--manifest")] = Path(
        "artifacts/generated/cosif_download_manifest.csv"
    ),
    timeout_seconds: Annotated[float, typer.Option("--timeout", min=1.0)] = 120.0,
    max_attempts: Annotated[int, typer.Option("--attempts", min=1)] = 3,
) -> None:
    """Download and validate catalog-selected COSIF bank archives."""
    try:
        urls = read_active_catalog_urls(catalog)
        records = download_catalog_files(
            urls,
            start_period,
            end_period,
            download_dir,
            timeout_seconds=timeout_seconds,
            max_attempts=max_attempts,
        )
    except (OSError, ValueError) as exc:
        typer.echo(f"COSIF download setup failed: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    written = write_download_manifest(records, manifest)
    complete = [record for record in records if record.status == "complete"]
    errors = [record for record in records if record.error]
    total_bytes = sum(record.compressed_bytes or 0 for record in complete)
    typer.echo(
        f"Wrote {written} manifest rows to {manifest}; complete={len(complete)}, "
        f"errors={len(errors)}, compressed_bytes={total_bytes}."
    )
    if errors:
        raise typer.Exit(code=1)


@app.command("profile-cosif")
def profile_cosif(
    manifest: Annotated[Path, typer.Option("--manifest")],
    output: Annotated[Path, typer.Option("--output")] = Path(
        "artifacts/generated/cosif_source_profile.csv"
    ),
) -> None:
    """Profile validated COSIF archives from a completed download manifest."""
    try:
        downloads = read_complete_downloads(manifest)
        if not downloads:
            raise ValueError("Manifest contains no complete downloads")
        records = profile_downloads(downloads)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        typer.echo(f"COSIF profiling failed: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    written = write_source_profile(records, output)
    rows = sum(record.row_count for record in records)
    malformed = sum(record.malformed_row_count for record in records)
    typer.echo(
        f"Wrote {written} file profiles to {output}; "
        f"rows={rows}, malformed_rows={malformed}."
    )
    if malformed or not all(record.period_matches for record in records):
        raise typer.Exit(code=1)


@app.command("profile-sgs")
def profile_sgs(
    registry: Annotated[Path, typer.Option("--registry")] = Path(
        "config/macro_series_registry.csv"
    ),
    start_date: Annotated[str, typer.Option("--start", help="First YYYY-MM-DD date.")] = (
        "2025-01-01"
    ),
    end_date: Annotated[str, typer.Option("--end", help="Last YYYY-MM-DD date.")] = ...,
    observations_output: Annotated[Path, typer.Option("--observations")] = Path(
        "artifacts/generated/macro_observations.csv"
    ),
    profile_output: Annotated[Path, typer.Option("--profile")] = Path(
        "artifacts/generated/macro_profile.csv"
    ),
    timeout_seconds: Annotated[float, typer.Option("--timeout", min=1.0)] = 30.0,
    max_attempts: Annotated[int, typer.Option("--attempts", min=1)] = 3,
) -> None:
    """Fetch and validate the five bounded official SGS macro series."""
    try:
        parsed_start = date.fromisoformat(start_date)
        parsed_end = date.fromisoformat(end_date)
        series = read_macro_registry(registry)
        observations, profiles = profile_macro_series(
            series,
            parsed_start,
            parsed_end,
            timeout_seconds=timeout_seconds,
            max_attempts=max_attempts,
        )
    except (OSError, ValueError) as exc:
        typer.echo(f"SGS profile setup failed: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    observation_count = write_macro_observations(observations, observations_output)
    profile_count = write_macro_profile(profiles, profile_output)
    failures = [profile for profile in profiles if profile.status != "complete"]
    typer.echo(
        f"Wrote {observation_count} observations and {profile_count} profiles; "
        f"complete={profile_count - len(failures)}, failures={len(failures)}."
    )
    if failures:
        raise typer.Exit(code=1)


@app.command("load-fixtures")
def load_fixtures(
    project_root: Annotated[Path, typer.Option("--project-root")] = Path("."),
) -> None:
    """Load synthetic COSIF and macro contracts into local PostgreSQL via dlt."""
    try:
        settings = WarehouseSettings()
        cosif_info, macro_info = run_fixture_pipelines(project_root.resolve(), settings)
    except Exception as exc:
        typer.echo(f"Fixture load failed: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"COSIF load: {cosif_info}")
    typer.echo(f"Macro load: {macro_info}")


@app.command("verify-fixtures")
def verify_fixtures(
    output: Annotated[Path, typer.Option("--output")] = Path(
        "artifacts/generated/fixture_landing_evidence.csv"
    ),
) -> None:
    """Verify fixture landing row identities and accounting reconciliation."""
    try:
        controls = verify_fixture_landing(WarehouseSettings())
    except (OSError, psycopg.Error) as exc:
        typer.echo(f"Fixture verification failed: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    written = write_fixture_controls(controls, output)
    failures = [control for control in controls if not control.passed]
    typer.echo(f"Wrote {written} controls to {output}; failures={len(failures)}.")
    if failures:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
