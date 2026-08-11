"""Executable Dagster asset graph with explicit fixture or official inputs."""

from collections.abc import Mapping
from pathlib import Path

from dagster import AssetExecutionContext, Definitions, define_asset_job, in_process_executor
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets
from dagster_dlt import DagsterDltResource

from banking_analytics.orchestration.config import (
    OfficialEvidenceConfig,
    resolve_source_mode,
)
from banking_analytics.orchestration.dlt_assets import (
    build_fixture_dlt_assets,
    build_official_dlt_assets,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DBT_PROJECT = DbtProject(
    project_dir=PROJECT_ROOT / "dbt",
    profiles_dir=PROJECT_ROOT / "dbt",
)
DBT_PROJECT.prepare_if_dev()


@dbt_assets(
    manifest=DBT_PROJECT.manifest_path,
    project=DBT_PROJECT,
    name="banking_dbt_assets",
)
def banking_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    """Build selected dbt models and emit their tests as Dagster asset checks."""
    yield from dbt.cli(["build"], context=context).stream()


def build_definitions(
    source_mode: str | None = None,
    environment: Mapping[str, str] | None = None,
) -> Definitions:
    """Build one graph with stable keys and a fail-closed selected source mode."""
    mode = resolve_source_mode(source_mode, environment)
    if mode == "official":
        evidence = OfficialEvidenceConfig.from_environment(PROJECT_ROOT, environment)
        cosif_assets, macro_assets = build_official_dlt_assets(PROJECT_ROOT, evidence)
    else:
        cosif_assets, macro_assets = build_fixture_dlt_assets(PROJECT_ROOT)
    # Both dlt multi-assets persist local pipeline state below one project directory.
    # A deterministic in-process job prevents concurrent code-location imports from
    # racing while dlt initializes those shared schema-storage paths on Windows.
    end_to_end_job = define_asset_job(
        name=f"{mode}_end_to_end",
        executor_def=in_process_executor,
    )
    return Definitions(
        assets=[cosif_assets, macro_assets, banking_dbt_assets],
        jobs=[end_to_end_job],
        resources={
            "dlt": DagsterDltResource(),
            "dbt": DbtCliResource(project_dir=DBT_PROJECT),
        },
    )


defs = build_definitions()
