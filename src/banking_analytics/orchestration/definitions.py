"""Executable fixture-backed Dagster asset graph."""

from pathlib import Path

from dagster import AssetExecutionContext, Definitions, define_asset_job
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets
from dagster_dlt import DagsterDltResource

from banking_analytics.orchestration.dlt_assets import build_fixture_dlt_assets

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


cosif_fixture_assets, macro_fixture_assets = build_fixture_dlt_assets(PROJECT_ROOT)
fixture_end_to_end = define_asset_job(name="fixture_end_to_end")

defs = Definitions(
    assets=[cosif_fixture_assets, macro_fixture_assets, banking_dbt_assets],
    jobs=[fixture_end_to_end],
    resources={
        "dlt": DagsterDltResource(),
        "dbt": DbtCliResource(project_dir=DBT_PROJECT),
    },
)
