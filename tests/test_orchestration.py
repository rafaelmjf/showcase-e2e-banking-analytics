from pathlib import Path

import dlt
import pytest
from dagster import AssetKey
from dagster_dlt.translator import DltResourceTranslatorData
from dlt.destinations import postgres

from banking_analytics.orchestration.config import (
    OfficialEvidenceConfig,
    resolve_source_mode,
)
from banking_analytics.orchestration.definitions import build_definitions
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


def test_fixture_mode_is_safe_default_with_stable_graph() -> None:
    definitions = build_definitions(environment={})

    assert len(definitions.resolve_asset_graph().get_all_asset_keys()) == 16
    assert definitions.resolve_job_def("fixture_end_to_end").name == "fixture_end_to_end"


def test_official_mode_requires_every_explicit_evidence_path(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="BANKING_OFFICIAL_COSIF_MANIFEST"):
        OfficialEvidenceConfig.from_environment(tmp_path, {})


def test_official_mode_resolves_bounded_relative_evidence(tmp_path: Path) -> None:
    filenames = {
        "BANKING_OFFICIAL_COSIF_MANIFEST": "manifest.csv",
        "BANKING_OFFICIAL_COSIF_PROFILE": "cosif-profile.csv",
        "BANKING_OFFICIAL_MACRO_OBSERVATIONS": "macro-observations.csv",
        "BANKING_OFFICIAL_MACRO_PROFILE": "macro-profile.csv",
        "BANKING_OFFICIAL_MACRO_REGISTRY": "macro-registry.csv",
    }
    for filename in filenames.values():
        (tmp_path / filename).touch()
    environment = {
        **filenames,
        "BANKING_OFFICIAL_MACRO_START": "2025-01-01",
        "BANKING_OFFICIAL_MACRO_END": "2025-03-31",
    }

    config = OfficialEvidenceConfig.from_environment(tmp_path, environment)

    assert config.cosif_manifest == (tmp_path / "manifest.csv").resolve()
    assert config.macro_registry == (tmp_path / "macro-registry.csv").resolve()
    assert config.macro_start_date.isoformat() == "2025-01-01"
    assert config.macro_end_date.isoformat() == "2025-03-31"


def test_source_mode_rejects_implicit_or_unknown_values() -> None:
    assert resolve_source_mode(environment={}) == "fixture"
    assert resolve_source_mode(environment={"BANKING_SOURCE_MODE": "OFFICIAL"}) == "official"
    with pytest.raises(ValueError, match="must be one of"):
        resolve_source_mode("live")
