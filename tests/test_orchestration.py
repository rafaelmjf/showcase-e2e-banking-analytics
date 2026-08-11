from pathlib import Path

import dlt
from dagster import AssetKey
from dagster_dlt.translator import DltResourceTranslatorData
from dlt.destinations import postgres

from banking_analytics.orchestration.dlt_assets import RawDatasetDltTranslator
from banking_analytics.pipelines.cosif import cosif_balance_row


def test_dlt_asset_key_matches_dbt_source_key(tmp_path: Path) -> None:
    pipeline = dlt.pipeline(
        pipeline_name="translator_test",
        pipelines_dir=str(tmp_path),
        destination=postgres(credentials="postgresql://user:pass@example.test/db"),
        dataset_name="raw_cosif",
    )
    resource = cosif_balance_row([])

    spec = RawDatasetDltTranslator().get_asset_spec(
        DltResourceTranslatorData(resource=resource, pipeline=pipeline)
    )

    assert spec.key == AssetKey(["raw_cosif", "cosif_balance_row"])
    assert list(spec.deps) == []
    assert spec.group_name == "raw_landing"
