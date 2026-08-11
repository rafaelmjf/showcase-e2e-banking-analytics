"""Command-line entry point for the banking analytics project."""

import zipfile
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Annotated

import httpx
import psycopg
import typer
import yaml

from banking_analytics.bcb.cosif import (
    build_source_catalog,
    build_source_inventory,
    read_active_catalog_urls,
    write_source_catalog,
    write_source_inventory,
)
from banking_analytics.mart_certification import (
    assess_reporting_mart_snapshot,
    collect_reporting_mart_snapshot,
    write_reporting_mart_certification,
)
from banking_analytics.official_certification import (
    assess_official_snapshot,
    collect_official_snapshot,
    write_official_certification,
)
from banking_analytics.pipelines.fixtures import (
    run_fixture_pipelines,
    verify_fixture_landing,
    write_fixture_controls,
)
from banking_analytics.pipelines.official import run_official_pipelines
from banking_analytics.readiness import assess_live_readiness, write_readiness_controls
from banking_analytics.settings import WarehouseSettings
from banking_analytics.source_decision import (
    assess_source_profile_files,
    write_source_profile_decision,
)
from banking_analytics.sources.cosif import (
    download_catalog_files,
    profile_downloads,
    read_complete_downloads,
    read_download_manifest,
    read_source_profiles,
    write_download_manifest,
    write_source_profile,
)
from banking_analytics.sources.cosif_population import (
    profile_cosif_population,
    write_population_analysis,
)
from banking_analytics.sources.sgs import (
    profile_macro_series,
    read_macro_observations,
    read_macro_profiles,
    read_macro_registry,
    write_macro_observations,
    write_macro_profile,
)

app = typer.Typer(help="Brazilian banking analytics data tools.")


@app.command()
def status() -> None:
    """Show the current implementation status."""
    typer.echo("Official reporting marts are implemented; Power BI is the next delivery layer.")


@app.command()
def about() -> None:
    """Describe the project domain."""
    typer.echo("Official BCB balance-sheet and macroeconomic analytics showcase.")


@app.command("source-inventory")
def source_inventory(
    start_period: Annotated[str, typer.Option("--start", help="First YYYYMM period.")] = ("202501"),
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
    download_dir: Annotated[Path, typer.Option("--download-dir")] = Path("data/downloads/cosif"),
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
        f"Wrote {written} file profiles to {output}; rows={rows}, malformed_rows={malformed}."
    )
    if malformed or not all(record.period_matches for record in records):
        raise typer.Exit(code=1)


@app.command("profile-cosif-population")
def profile_cosif_population_command(
    manifest: Annotated[Path, typer.Option("--manifest")],
    profile: Annotated[Path, typer.Option("--profile")],
    freeze_period: Annotated[str | None, typer.Option("--freeze-period")] = None,
    output_dir: Annotated[Path, typer.Option("--output-dir")] = Path(
        "artifacts/generated/checkpoint-0c"
    ),
    population_size: Annotated[int, typer.Option("--population-size", min=1)] = 15,
    reconciliation_tolerance: Annotated[str, typer.Option("--reconciliation-tolerance")] = "1.00",
) -> None:
    """Certify total assets and freeze the stable individual-bank population."""
    try:
        analysis = profile_cosif_population(
            read_download_manifest(manifest),
            read_source_profiles(profile),
            freeze_period=freeze_period,
            population_size=population_size,
            reconciliation_tolerance_brl=Decimal(reconciliation_tolerance),
        )
        written = write_population_analysis(analysis, output_dir)
    except (ArithmeticError, OSError, ValueError, zipfile.BadZipFile) as exc:
        typer.echo(f"COSIF population profiling failed: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    failures = sum(not control.passed for control in analysis.controls[:-1])
    typer.echo(
        f"Wrote checkpoint 0C evidence to {output_dir}; "
        f"periods={written['period_profile']}, population={written['population']}, "
        f"monthly_rows={written['monthly_balances']}, "
        f"status={'ready' if analysis.passed else 'blocked'}, failed_controls={failures}."
    )
    if not analysis.passed:
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


@app.command("load-official")
def load_official(
    cosif_manifest: Annotated[Path, typer.Option("--cosif-manifest")],
    cosif_profile: Annotated[Path, typer.Option("--cosif-profile")],
    macro_observations: Annotated[Path, typer.Option("--macro-observations")],
    macro_profile: Annotated[Path, typer.Option("--macro-profile")],
    macro_start_date: Annotated[str, typer.Option("--macro-start")],
    macro_end_date: Annotated[str, typer.Option("--macro-end")],
    macro_registry: Annotated[Path, typer.Option("--macro-registry")] = Path(
        "config/macro_series_registry.csv"
    ),
    project_root: Annotated[Path, typer.Option("--project-root")] = Path("."),
) -> None:
    """Land only acquisition outputs that passed every official-source profile."""
    try:
        start_date = date.fromisoformat(macro_start_date)
        end_date = date.fromisoformat(macro_end_date)
        cosif_info, macro_info = run_official_pipelines(
            project_root.resolve(),
            read_download_manifest(cosif_manifest),
            read_source_profiles(cosif_profile),
            read_macro_registry(macro_registry),
            read_macro_observations(macro_observations),
            read_macro_profiles(macro_profile),
            start_date,
            end_date,
        )
    except Exception as exc:
        typer.echo(f"Official load failed: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"COSIF load: {cosif_info}")
    typer.echo(f"Macro load: {macro_info}")


@app.command("assess-readiness")
def assess_readiness(
    cosif_manifest: Annotated[Path, typer.Option("--cosif-manifest")],
    cosif_profile: Annotated[Path, typer.Option("--cosif-profile")],
    macro_profile: Annotated[Path, typer.Option("--macro-profile")],
    cosif_start_period: Annotated[str, typer.Option("--cosif-start")],
    cosif_end_period: Annotated[str, typer.Option("--cosif-end")],
    macro_start_date: Annotated[str, typer.Option("--macro-start")],
    macro_end_date: Annotated[str, typer.Option("--macro-end")],
    output: Annotated[Path, typer.Option("--output")] = Path(
        "artifacts/generated/live_readiness.csv"
    ),
) -> None:
    """Publish ready/blocked controls without loading the warehouse."""
    try:
        parsed_macro_start = date.fromisoformat(macro_start_date)
        parsed_macro_end = date.fromisoformat(macro_end_date)
        downloads = read_download_manifest(cosif_manifest) if cosif_manifest.is_file() else []
        cosif_profiles = read_source_profiles(cosif_profile) if cosif_profile.is_file() else []
        macro_profiles = read_macro_profiles(macro_profile) if macro_profile.is_file() else []
        controls = assess_live_readiness(
            downloads,
            cosif_profiles,
            macro_profiles,
            cosif_start_period,
            cosif_end_period,
            parsed_macro_start,
            parsed_macro_end,
        )
    except (OSError, ValueError) as exc:
        typer.echo(f"Readiness assessment failed: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    written = write_readiness_controls(controls, output)
    ready = controls[-1].passed
    failures = sum(not control.passed for control in controls[:-1])
    typer.echo(
        f"Wrote {written} readiness controls to {output}; "
        f"status={'ready' if ready else 'blocked'}, failed_controls={failures}."
    )
    if not ready:
        raise typer.Exit(code=1)


@app.command("assess-source-profile")
def assess_source_profile(
    catalog: Annotated[Path, typer.Option("--catalog")] = Path("artifacts/source_catalog.csv"),
    cosif_manifest: Annotated[Path, typer.Option("--cosif-manifest")] = Path(
        "artifacts/generated/cosif_download_manifest.csv"
    ),
    cosif_profile: Annotated[Path, typer.Option("--cosif-profile")] = Path(
        "artifacts/cosif_source_profile.csv"
    ),
    macro_observations: Annotated[Path, typer.Option("--macro-observations")] = Path(
        "artifacts/generated/macro_observations.csv"
    ),
    macro_profile: Annotated[Path, typer.Option("--macro-profile")] = Path(
        "artifacts/macro_source_profile.csv"
    ),
    readiness: Annotated[Path, typer.Option("--readiness")] = Path(
        "artifacts/live_readiness_full_202501_202603.csv"
    ),
    population_controls: Annotated[Path, typer.Option("--population-controls")] = Path(
        "artifacts/checkpoint_0c_controls.csv"
    ),
    population: Annotated[Path, typer.Option("--population")] = Path(
        "artifacts/top15_population.csv"
    ),
    population_monthly: Annotated[Path, typer.Option("--population-monthly")] = Path(
        "artifacts/top15_total_assets_by_month.csv"
    ),
    period_profile: Annotated[Path, typer.Option("--period-profile")] = Path(
        "artifacts/total_assets_period_profile.csv"
    ),
    reporting_line_draft: Annotated[Path, typer.Option("--reporting-line-draft")] = Path(
        "config/reporting_line_draft.csv"
    ),
    start_period: Annotated[str, typer.Option("--start")] = "202501",
    end_period: Annotated[str, typer.Option("--end")] = "202603",
    freeze_period: Annotated[str, typer.Option("--freeze-period")] = "202603",
    population_size: Annotated[int, typer.Option("--population-size", min=1)] = 15,
    output_dir: Annotated[Path, typer.Option("--output-dir")] = Path(
        "artifacts/generated/checkpoint-0e"
    ),
) -> None:
    """Freeze the final source contract without mutating the warehouse."""
    try:
        decision = assess_source_profile_files(
            catalog=catalog,
            cosif_manifest=cosif_manifest,
            cosif_profile=cosif_profile,
            macro_observations=macro_observations,
            macro_profile=macro_profile,
            readiness=readiness,
            population_controls=population_controls,
            population=population,
            population_monthly=population_monthly,
            period_profile=period_profile,
            reporting_line_draft=reporting_line_draft,
            start_period=start_period,
            end_period=end_period,
            freeze_period=freeze_period,
            population_size=population_size,
        )
        written = write_source_profile_decision(decision, output_dir)
    except (OSError, ValueError) as exc:
        typer.echo(f"Source-profile assessment failed: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    failures = sum(not control.passed for control in decision.controls[:-1])
    typer.echo(
        f"Wrote checkpoint 0E evidence to {output_dir}; "
        f"controls={written['controls']}, contract_rows={written['contract']}, "
        f"status={'ready' if decision.passed else 'blocked'}, failed_controls={failures}."
    )
    if not decision.passed:
        raise typer.Exit(code=1)


@app.command("certify-official-warehouse")
def certify_official_warehouse(
    expected_database: Annotated[str, typer.Option("--expected-database")],
    dagster_run_id: Annotated[str, typer.Option("--dagster-run-id")],
    dagster_status: Annotated[str, typer.Option("--dagster-status")] = "success",
    population_monthly: Annotated[Path, typer.Option("--population-monthly")] = Path(
        "artifacts/top15_total_assets_by_month.csv"
    ),
    dbt_run_results: Annotated[Path, typer.Option("--dbt-run-results")] = Path(
        "dbt/target/run_results.json"
    ),
    output: Annotated[Path, typer.Option("--output")] = Path(
        "artifacts/generated/official_warehouse_certification.csv"
    ),
) -> None:
    """Certify the official landing and canonical core after a successful run."""
    try:
        snapshot = collect_official_snapshot(
            WarehouseSettings(),
            population_monthly=population_monthly,
            dbt_run_results=dbt_run_results,
            dagster_run_id=dagster_run_id,
            dagster_status=dagster_status,
        )
        controls = assess_official_snapshot(snapshot, expected_database=expected_database)
        written = write_official_certification(controls, output)
    except (OSError, ValueError, psycopg.Error) as exc:
        typer.echo(
            f"Official warehouse certification failed: {type(exc).__name__}: {exc}",
            err=True,
        )
        raise typer.Exit(code=1) from exc
    failures = sum(not control.passed for control in controls[:-1])
    typer.echo(
        f"Wrote {written} official certification controls to {output}; "
        f"status={'certified' if controls[-1].passed else 'blocked'}, "
        f"failed_controls={failures}."
    )
    if not controls[-1].passed:
        raise typer.Exit(code=1)


@app.command("certify-reporting-marts")
def certify_reporting_marts(
    expected_database: Annotated[str, typer.Option("--expected-database")],
    dagster_run_id: Annotated[str, typer.Option("--dagster-run-id")],
    dagster_status: Annotated[str, typer.Option("--dagster-status")] = "success",
    population_monthly: Annotated[Path, typer.Option("--population-monthly")] = Path(
        "artifacts/top15_total_assets_by_month.csv"
    ),
    dbt_run_results: Annotated[Path, typer.Option("--dbt-run-results")] = Path(
        "dbt/target/run_results.json"
    ),
    contract: Annotated[Path, typer.Option("--contract")] = Path(
        "contracts/mart-schema.yml"
    ),
    output: Annotated[Path, typer.Option("--output")] = Path(
        "artifacts/generated/reporting_mart_certification.csv"
    ),
) -> None:
    """Certify the frozen official reporting marts after an expanded Dagster run."""
    try:
        snapshot = collect_reporting_mart_snapshot(
            WarehouseSettings(),
            population_monthly=population_monthly,
            dbt_run_results=dbt_run_results,
            contract=contract,
            dagster_run_id=dagster_run_id,
            dagster_status=dagster_status,
        )
        controls = assess_reporting_mart_snapshot(
            snapshot, expected_database=expected_database
        )
        written = write_reporting_mart_certification(controls, output)
    except (OSError, ValueError, psycopg.Error, yaml.YAMLError) as exc:
        typer.echo(
            f"Reporting-mart certification failed: {type(exc).__name__}: {exc}",
            err=True,
        )
        raise typer.Exit(code=1) from exc
    failures = sum(not control.passed for control in controls[:-1])
    typer.echo(
        f"Wrote {written} reporting-mart certification controls to {output}; "
        f"status={'certified' if controls[-1].passed else 'blocked'}, "
        f"failed_controls={failures}."
    )
    if not controls[-1].passed:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
