from dataclasses import replace
from datetime import date
from pathlib import Path

from banking_analytics.readiness import (
    assess_live_readiness,
    write_readiness_controls,
)
from banking_analytics.sources.cosif import DownloadRecord, ProfileRecord
from banking_analytics.sources.sgs import EXPECTED_SERIES_CODES, MacroProfile


def _download() -> DownloadRecord:
    return DownloadRecord(
        period="202501",
        source_url="https://www.bcb.gov.br/202501.zip",
        status="complete",
        http_status=200,
        retrieved_at_utc="2025-02-01T00:00:00+00:00",
        sha256="a" * 64,
        compressed_bytes=100,
        archive_path="data/downloads/cosif/202501/archive.zip",
        member_count=1,
        error=None,
    )


def _cosif_profile() -> ProfileRecord:
    return ProfileRecord(
        period="202501",
        source_url="https://www.bcb.gov.br/202501.zip",
        sha256="a" * 64,
        compressed_bytes=100,
        member_name="202501BANCOS.csv",
        uncompressed_bytes=500,
        encoding="cp1252",
        delimiter=";",
        header_line_number=4,
        metadata_line_count=3,
        columns=(
            "DATA_BASE|DOCUMENTO|CNPJ|AGENCIA|NOME_INSTITUICAO|COD_CONGL|"
            "NOME_CONGL|TAXONOMIA|CONTA|NOME_CONTA|SALDO"
        ),
        row_count=10,
        malformed_row_count=0,
        document_count=1,
        institution_count=2,
        account_count=5,
        declared_period_count=1,
        declared_periods="202501",
        period_matches=True,
        source_generated_at="2025-01-31",
    )


def _macro_profiles() -> list[MacroProfile]:
    return [
        MacroProfile(
            series_code=code,
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
            max_expected_lag_months=1,
            error=None,
        )
        for code in sorted(EXPECTED_SERIES_CODES, key=int)
    ]


def test_complete_evidence_is_ready_and_writes_contract(tmp_path: Path) -> None:
    controls = assess_live_readiness(
        [_download()],
        [_cosif_profile()],
        _macro_profiles(),
        "202501",
        "202501",
        date(2025, 1, 1),
        date(2025, 1, 31),
    )

    assert len(controls) == 9
    assert all(control.passed for control in controls)
    output = tmp_path / "readiness.csv"
    assert write_readiness_controls(controls, output) == 9
    assert "bounded_official_load_ready" in output.read_text(encoding="utf-8")


def test_failed_sources_are_blocked_with_specific_controls() -> None:
    failed_download = replace(
        _download(),
        status="error",
        http_status=502,
        sha256=None,
        compressed_bytes=None,
        archive_path=None,
        member_count=None,
        error="HTTP 502",
    )
    failed_macro = [
        replace(profile, status="error", row_count=0, error="HTTP 502")
        for profile in _macro_profiles()
    ]

    controls = assess_live_readiness(
        [failed_download],
        [],
        failed_macro,
        "202501",
        "202501",
        date(2025, 1, 1),
        date(2025, 1, 31),
    )
    by_name = {control.control_name: control for control in controls}

    assert by_name["manifest_period_coverage"].passed
    assert not by_name["all_downloads_complete"].passed
    assert "202501:502:error" in by_name["all_downloads_complete"].detail
    assert not by_name["all_series_complete"].passed
    assert by_name["bounded_official_load_ready"].actual_value == "blocked"
