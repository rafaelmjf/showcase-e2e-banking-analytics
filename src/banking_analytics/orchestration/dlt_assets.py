"""Dagster-dlt assets whose keys match the physical raw datasets."""

from pathlib import Path

import dlt
from dagster import AssetExecutionContext, AssetKey, AssetSpec
from dagster_dlt import (
    DagsterDltResource,
    DagsterDltTranslator,
    dlt_assets,
)
from dagster_dlt.translator import DltResourceTranslatorData
from dlt.destinations import postgres

from banking_analytics.fixtures import (
    build_cosif_fixture_manifests,
    build_macro_metadata_fixture,
    read_cosif_fixture,
    read_macro_fixture,
)
from banking_analytics.orchestration.config import OfficialEvidenceConfig
from banking_analytics.pipelines.cosif import cosif_landing_source
from banking_analytics.pipelines.fixtures import build_macro_fixture_fetches
from banking_analytics.pipelines.macro import macro_landing_source
from banking_analytics.settings import WarehouseSettings
from banking_analytics.sources.cosif import (
    build_cosif_landing_records,
    read_download_manifest,
    read_source_profiles,
)
from banking_analytics.sources.sgs import (
    build_macro_landing_records,
    read_macro_observations,
    read_macro_profiles,
    read_macro_registry,
)


class RawDatasetDltTranslator(DagsterDltTranslator):
    """Use `[dataset, table]` so dbt source dependencies join the dlt outputs."""

    def get_asset_spec(self, data: DltResourceTranslatorData) -> AssetSpec:
        spec = super().get_asset_spec(data)
        if data.pipeline is None or data.pipeline.dataset_name is None:
            raise ValueError("A dlt dataset name is required for a raw asset key")
        return spec.replace_attributes(
            key=AssetKey([data.pipeline.dataset_name, data.resource.name]),
            deps=[],
            group_name="raw_landing",
        )


def build_fixture_dlt_assets(project_root: Path):
    """Build the two executable fixture landing multi-assets."""
    cosif_rows = read_cosif_fixture(project_root / "fixtures" / "cosif_balance_rows.csv")
    cosif_manifests = build_cosif_fixture_manifests(cosif_rows)
    cosif_source = cosif_landing_source(cosif_manifests, cosif_rows)
    macro_rows = read_macro_fixture(project_root / "fixtures" / "macro_observations.csv")
    macro_metadata = build_macro_metadata_fixture(
        project_root / "config" / "macro_series_registry.csv"
    )
    macro_fetches = build_macro_fixture_fetches(macro_rows)
    macro_source = macro_landing_source(macro_metadata, macro_rows, macro_fetches)
    return _build_dlt_assets(project_root, cosif_source, macro_source, mode="fixture")


def build_official_dlt_assets(
    project_root: Path, evidence: OfficialEvidenceConfig
):
    """Build raw assets from profiler evidence that passed every source gate."""
    cosif_manifests, cosif_rows = build_cosif_landing_records(
        read_download_manifest(evidence.cosif_manifest),
        read_source_profiles(evidence.cosif_profile),
    )
    macro_metadata, macro_rows, macro_fetches = build_macro_landing_records(
        read_macro_registry(evidence.macro_registry),
        read_macro_observations(evidence.macro_observations),
        read_macro_profiles(evidence.macro_profile),
        evidence.macro_start_date,
        evidence.macro_end_date,
    )
    return _build_dlt_assets(
        project_root,
        cosif_landing_source(cosif_manifests, cosif_rows),
        macro_landing_source(macro_metadata, macro_rows, macro_fetches),
        mode="official",
    )


def _build_dlt_assets(project_root: Path, cosif_source, macro_source, *, mode: str):
    """Attach a selected pair of dlt sources to stable physical asset keys."""
    settings = WarehouseSettings()
    destination = postgres(credentials=settings.dsn)
    pipelines_dir = project_root / "data" / "work" / "dagster_dlt"
    pipeline_suffix = "" if mode == "fixture" else f"_{mode}"
    cosif_pipeline = dlt.pipeline(
        pipeline_name=f"dagster_banking_cosif{pipeline_suffix}",
        pipelines_dir=str(pipelines_dir),
        destination=destination,
        dataset_name="raw_cosif",
    )
    macro_pipeline = dlt.pipeline(
        pipeline_name=f"dagster_banking_macro{pipeline_suffix}",
        pipelines_dir=str(pipelines_dir),
        destination=destination,
        dataset_name="raw_macro",
    )
    translator = RawDatasetDltTranslator()

    @dlt_assets(
        dlt_source=cosif_source,
        dlt_pipeline=cosif_pipeline,
        name=f"cosif_{mode}_landing",
        dagster_dlt_translator=translator,
    )
    def cosif_assets(context: AssetExecutionContext, dlt: DagsterDltResource):
        yield from dlt.run(context=context)

    @dlt_assets(
        dlt_source=macro_source,
        dlt_pipeline=macro_pipeline,
        name=f"macro_{mode}_landing",
        dagster_dlt_translator=translator,
    )
    def macro_assets(context: AssetExecutionContext, dlt: DagsterDltResource):
        yield from dlt.run(context=context)

    return cosif_assets, macro_assets
