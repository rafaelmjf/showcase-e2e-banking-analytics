import csv
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx
from typer.testing import CliRunner

from banking_analytics.cli import app
from banking_analytics.sources.sgs import (
    EXPECTED_SERIES_CODES,
    MacroSeries,
    build_sgs_url,
    profile_macro_series,
    read_macro_registry,
    write_macro_observations,
    write_macro_profile,
)

REGISTRY = Path("config/macro_series_registry.csv")


def _series(code: str = "433", max_lag: int = 1) -> MacroSeries:
    return MacroSeries(
        series_code=code,
        theme="test",
        display_name="Test",
        official_title="Test series",
        unit="Percentual",
        frequency="monthly",
        source_start_date=date(1980, 1, 1),
        observation_semantics="Native monthly value",
        monthly_alignment="Calendar month",
        derived_metric="None",
        max_expected_lag_months=max_lag,
        revision_policy="Replace republished month",
        source_url="https://example.test/dataset",
        metadata_url="https://example.test/metadata",
    )


def _payload(*months: tuple[str, str]) -> list[dict[str, str]]:
    return [{"data": observed, "valor": value} for observed, value in months]


def test_registry_contains_exact_five_monthly_series() -> None:
    registry = read_macro_registry(REGISTRY)

    assert {series.series_code for series in registry} == EXPECTED_SERIES_CODES
    assert all(series.frequency == "monthly" for series in registry)
    assert all(series.max_expected_lag_months >= 0 for series in registry)


def test_bounded_url_uses_official_date_parameters() -> None:
    url = build_sgs_url("433", date(2025, 1, 1), date(2025, 3, 31))
    parsed = urlparse(url)

    assert parsed.netloc == "api.bcb.gov.br"
    assert parsed.path.endswith("bcdata.sgs.433/dados")
    assert parse_qs(parsed.query) == {
        "formato": ["json"],
        "dataInicial": ["01/01/2025"],
        "dataFinal": ["31/03/2025"],
    }


def test_profile_aligns_native_dates_to_month_and_preserves_decimal(tmp_path: Path) -> None:
    body = _payload(
        ("31/01/2025", "0,16"),
        ("01/02/2025", "1.31"),
        ("31/03/2025", "-0.04"),
    )
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json=body))

    observations, profiles = profile_macro_series(
        [_series()],
        date(2025, 1, 1),
        date(2025, 3, 31),
        max_attempts=1,
        retry_delay_seconds=0,
        transport=transport,
    )

    assert [row.report_month for row in observations] == ["202501", "202502", "202503"]
    assert [row.value for row in observations] == ["0.16", "1.31", "-0.04"]
    assert profiles[0].status == "complete"
    assert profiles[0].internal_missing_month_count == 0
    assert profiles[0].lag_months_to_requested_end == 0

    observations_path = tmp_path / "observations.csv"
    profile_path = tmp_path / "profile.csv"
    assert write_macro_observations(observations, observations_path) == 3
    assert write_macro_profile(profiles, profile_path) == 1
    assert list(csv.DictReader(profile_path.open(encoding="utf-8")))[0]["status"] == "complete"


def test_profile_rejects_internal_gap_and_duplicate_month() -> None:
    body = _payload(
        ("01/01/2025", "1"),
        ("28/02/2025", "2"),
        ("01/02/2025", "3"),
        ("30/04/2025", "4"),
    )
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json=body))

    _, profiles = profile_macro_series(
        [_series(max_lag=0)],
        date(2025, 1, 1),
        date(2025, 4, 30),
        max_attempts=1,
        retry_delay_seconds=0,
        transport=transport,
    )

    profile = profiles[0]
    assert profile.status == "invalid"
    assert profile.duplicate_report_month_count == 1
    assert profile.internal_missing_months == "202503"


def test_profile_retains_http_failure_for_each_series() -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(502, text="bad gateway"))

    observations, profiles = profile_macro_series(
        [_series()],
        date(2025, 1, 1),
        date(2025, 1, 31),
        max_attempts=1,
        retry_delay_seconds=0,
        transport=transport,
    )

    assert observations == []
    assert profiles[0].status == "error"
    assert "502 Bad Gateway" in (profiles[0].error or "")


def test_profile_rejects_non_finite_value() -> None:
    transport = httpx.MockTransport(
        lambda _: httpx.Response(200, json=_payload(("31/01/2025", "NaN")))
    )

    observations, profiles = profile_macro_series(
        [_series()],
        date(2025, 1, 1),
        date(2025, 1, 31),
        max_attempts=1,
        retry_delay_seconds=0,
        transport=transport,
    )

    assert observations == []
    assert profiles[0].status == "error"
    assert "non-finite" in (profiles[0].error or "")


def test_cli_registers_and_validates_iso_dates() -> None:
    runner = CliRunner()

    help_result = runner.invoke(app, ["profile-sgs", "--help"])
    invalid_result = runner.invoke(
        app,
        ["profile-sgs", "--start", "not-a-date", "--end", "2026-07-31"],
    )

    assert help_result.exit_code == 0
    assert invalid_result.exit_code == 1
    assert "Invalid isoformat string" in invalid_result.output
