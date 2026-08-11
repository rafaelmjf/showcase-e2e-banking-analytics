"""Load verified official acquisition evidence through the production dlt contracts."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from pathlib import Path

import dlt
from dlt.destinations import postgres

from banking_analytics.pipelines.cosif import cosif_landing_source
from banking_analytics.pipelines.macro import macro_landing_source
from banking_analytics.settings import WarehouseSettings
from banking_analytics.sources.cosif import (
    DownloadRecord,
    ProfileRecord,
    build_cosif_landing_records,
)
from banking_analytics.sources.sgs import (
    MacroObservation,
    MacroProfile,
    MacroSeries,
    build_macro_landing_records,
)


def run_official_pipelines(
    project_root: Path,
    cosif_downloads: Iterable[DownloadRecord],
    cosif_profiles: Iterable[ProfileRecord],
    macro_registry: Iterable[MacroSeries],
    macro_observations: Iterable[MacroObservation],
    macro_profiles: Iterable[MacroProfile],
    macro_start_date: date,
    macro_end_date: date,
    settings: WarehouseSettings | None = None,
) -> tuple[dlt.common.pipeline.LoadInfo, dlt.common.pipeline.LoadInfo]:
    """Validate and land source-derived COSIF and SGS records in PostgreSQL."""
    settings = settings or WarehouseSettings()
    destination = postgres(credentials=settings.dsn)
    pipelines_dir = project_root / "data" / "work" / "dlt"
    cosif_manifests, cosif_rows = build_cosif_landing_records(
        cosif_downloads, cosif_profiles
    )
    macro_metadata, macro_rows, macro_fetches = build_macro_landing_records(
        macro_registry,
        macro_observations,
        macro_profiles,
        macro_start_date,
        macro_end_date,
    )

    cosif_pipeline = dlt.pipeline(
        pipeline_name="banking_cosif",
        pipelines_dir=str(pipelines_dir),
        destination=destination,
        dataset_name="raw_cosif",
    )
    cosif_info = cosif_pipeline.run(
        cosif_landing_source(cosif_manifests, cosif_rows),
        loader_file_format="insert_values",
    )

    macro_pipeline = dlt.pipeline(
        pipeline_name="banking_macro",
        pipelines_dir=str(pipelines_dir),
        destination=destination,
        dataset_name="raw_macro",
    )
    macro_info = macro_pipeline.run(
        macro_landing_source(macro_metadata, macro_rows, macro_fetches),
        loader_file_format="insert_values",
    )
    return cosif_info, macro_info
