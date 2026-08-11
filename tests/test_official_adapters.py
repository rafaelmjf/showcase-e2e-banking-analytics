import io
import zipfile
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
from typer.testing import CliRunner

from banking_analytics.cli import app
from banking_analytics.pipelines.cosif import BALANCE_COLUMNS, MANIFEST_COLUMNS
from banking_analytics.pipelines.macro import (
    FETCH_COLUMNS,
    METADATA_COLUMNS,
    OBSERVATION_COLUMNS,
)
from banking_analytics.sources.cosif import (
    build_cosif_landing_records,
    download_catalog_files,
    profile_downloads,
    read_download_manifest,
    read_source_profiles,
    write_download_manifest,
    write_source_profile,
)
from banking_analytics.sources.sgs import (
    MacroObservation,
    MacroProfile,
    build_macro_landing_records,
    build_sgs_url,
    read_macro_observations,
    read_macro_profiles,
    read_macro_registry,
    write_macro_observations,
    write_macro_profile,
)


def _cosif_archive() -> bytes:
    lines = [
        "#Arquivo oficial de teste de contrato",
        "#Gerado em 31/01/2025",
        (
            "#DATA_BASE;DOCUMENTO;CNPJ;AGENCIA;NOME_INSTITUICAO;COD_CONGL;"
            "NOME_CONGL;TAXONOMIA;CONTA;NOME_CONTA;SALDO"
        ),
        "202501;4010;11111111;;BANCO UM;;;BANCO;1000000009;Ativo;1.234,56",
        "202501;4010;11111111;;BANCO UM;;;BANCO;2000000008;Passivo;234,56",
    ]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("202501BANCOS.csv", ("\r\n".join(lines) + "\r\n").encode("cp1252"))
    return buffer.getvalue()


def _verified_cosif(tmp_path: Path):
    body = _cosif_archive()
    url = "https://www.bcb.gov.br/content/cosif/Bancos/202501BANCOS.csv.zip"
    transport = httpx.MockTransport(lambda _: httpx.Response(200, content=body))
    downloads = download_catalog_files(
        {"202501": url},
        "202501",
        "202501",
        tmp_path / "downloads",
        max_attempts=1,
        retry_delay_seconds=0,
        transport=transport,
    )
    return downloads, profile_downloads(downloads)


def test_cosif_profile_evidence_builds_strict_official_landing(tmp_path: Path) -> None:
    downloads, profiles = _verified_cosif(tmp_path)
    manifest_path = tmp_path / "manifest.csv"
    profile_path = tmp_path / "profile.csv"
    write_download_manifest(downloads, manifest_path)
    write_source_profile(profiles, profile_path)

    manifests, row_iterator = build_cosif_landing_records(
        read_download_manifest(manifest_path), read_source_profiles(profile_path)
    )
    rows = list(row_iterator)

    assert manifests[0]["fixture"] is False
    assert manifests[0]["row_count"] == 2
    assert len(rows) == 2
    assert rows[0]["saldo_raw"] == "1.234,56"
    assert rows[0]["saldo"] == Decimal("1234.56")
    assert rows[0]["file_row_number"] == 1
    assert rows[0]["source_checksum"] == manifests[0]["source_checksum"]
    assert set(manifests[0]) == set(MANIFEST_COLUMNS)
    assert set(rows[0]) == set(BALANCE_COLUMNS)


def test_cosif_landing_rejects_a_failed_profile_before_iteration(tmp_path: Path) -> None:
    downloads, profiles = _verified_cosif(tmp_path)

    with pytest.raises(ValueError, match="malformed rows"):
        build_cosif_landing_records(
            downloads, [replace(profiles[0], malformed_row_count=1)]
        )


def _verified_macro():
    registry = read_macro_registry(Path("config/macro_series_registry.csv"))
    retrieved_at = "2025-02-10T12:00:00+00:00"
    observations = [
        MacroObservation(
            series_code=series.series_code,
            source_observation_date="2025-01-31",
            report_month="202501",
            value="1.25",
            retrieved_at_utc=retrieved_at,
            source_url=build_sgs_url(
                series.series_code, date(2025, 1, 1), date(2025, 1, 31)
            ),
        )
        for series in registry
    ]
    profiles = [
        MacroProfile(
            series_code=series.series_code,
            status="complete",
            requested_start_month="202501",
            requested_end_month="202501",
            row_count=1,
            first_observation_date="2025-01-31",
            last_observation_date="2025-01-31",
            first_report_month="202501",
            last_report_month="202501",
            internal_missing_month_count=0,
            internal_missing_months="",
            duplicate_observation_date_count=0,
            duplicate_report_month_count=0,
            lag_months_to_requested_end=0,
            max_expected_lag_months=series.max_expected_lag_months,
            error=None,
        )
        for series in registry
    ]
    return registry, observations, profiles


def test_macro_profile_evidence_builds_strict_official_landing(tmp_path: Path) -> None:
    registry, observations, profiles = _verified_macro()
    observations_path = tmp_path / "observations.csv"
    profiles_path = tmp_path / "profiles.csv"
    write_macro_observations(observations, observations_path)
    write_macro_profile(profiles, profiles_path)

    metadata, rows, fetches = build_macro_landing_records(
        registry,
        read_macro_observations(observations_path),
        read_macro_profiles(profiles_path),
        date(2025, 1, 1),
        date(2025, 1, 31),
    )

    assert len(metadata) == len(rows) == len(fetches) == 5
    assert all(row["fixture"] is False for row in rows)
    assert all(row["fixture"] is False for row in fetches)
    assert rows[0]["value"] == Decimal("1.25")
    assert fetches[0]["response_count"] == 1
    assert set(metadata[0]) == set(METADATA_COLUMNS)
    assert set(rows[0]) == set(OBSERVATION_COLUMNS)
    assert set(fetches[0]) == set(FETCH_COLUMNS)


def test_macro_landing_rejects_any_unpassed_series() -> None:
    registry, observations, profiles = _verified_macro()
    profiles[0] = replace(profiles[0], status="invalid", error="gap")

    with pytest.raises(ValueError, match="has not passed"):
        build_macro_landing_records(
            registry,
            observations,
            profiles,
            date(2025, 1, 1),
            date(2025, 1, 31),
        )


def test_official_load_command_is_registered() -> None:
    result = CliRunner().invoke(app, ["load-official", "--help"])

    assert result.exit_code == 0
    assert "--cosif-manifest" in result.output
    assert "--macro-observations" in result.output
