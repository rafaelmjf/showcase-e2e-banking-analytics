"""Validate the macro registry and profile official BCB SGS observations."""

from __future__ import annotations

import csv
import time
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlencode

import httpx

from banking_analytics.bcb.cosif import DEFAULT_USER_AGENT

SGS_API_TEMPLATE = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados"
EXPECTED_SERIES_CODES = {"4189", "433", "24363", "20539", "21082"}


@dataclass(frozen=True)
class MacroSeries:
    """Authored semantic contract for one official monthly SGS series."""

    series_code: str
    theme: str
    display_name: str
    official_title: str
    unit: str
    frequency: str
    source_start_date: date
    observation_semantics: str
    monthly_alignment: str
    derived_metric: str
    max_expected_lag_months: int
    revision_policy: str
    source_url: str
    metadata_url: str


@dataclass(frozen=True)
class MacroObservation:
    """One native SGS value with its explicit report-month key."""

    series_code: str
    source_observation_date: str
    report_month: str
    value: str
    retrieved_at_utc: str
    source_url: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class MacroProfile:
    """Completeness and freshness evidence for one requested SGS series."""

    series_code: str
    status: str
    requested_start_month: str
    requested_end_month: str
    row_count: int
    first_observation_date: str | None
    last_observation_date: str | None
    first_report_month: str | None
    last_report_month: str | None
    internal_missing_month_count: int
    internal_missing_months: str
    duplicate_observation_date_count: int
    duplicate_report_month_count: int
    lag_months_to_requested_end: int | None
    max_expected_lag_months: int
    error: str | None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def read_macro_registry(path: Path) -> list[MacroSeries]:
    """Read and strictly validate the five-series authored registry."""
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    codes = [row.get("series_code", "").strip() for row in rows]
    if set(codes) != EXPECTED_SERIES_CODES or len(codes) != len(EXPECTED_SERIES_CODES):
        raise ValueError(
            "Macro registry must contain each required SGS code exactly once: "
            + ", ".join(sorted(EXPECTED_SERIES_CODES, key=int))
        )

    registry: list[MacroSeries] = []
    for row in rows:
        missing = [key for key, value in row.items() if value is None or not value.strip()]
        if missing:
            raise ValueError(f"Series {row.get('series_code')} has blank fields: {missing}")
        if row["frequency"].strip().lower() != "monthly":
            raise ValueError(f"Series {row['series_code']} is not monthly")
        try:
            source_start = date.fromisoformat(row["source_start_date"].strip())
            max_lag = int(row["max_expected_lag_months"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid registry metadata for {row['series_code']}: {exc}") from exc
        if max_lag < 0:
            raise ValueError(f"Negative expected lag for {row['series_code']}")
        for field in ("source_url", "metadata_url"):
            if not row[field].startswith("https://"):
                raise ValueError(f"Series {row['series_code']} has non-HTTPS {field}")
        registry.append(
            MacroSeries(
                series_code=row["series_code"].strip(),
                theme=row["theme"].strip(),
                display_name=row["display_name"].strip(),
                official_title=row["official_title"].strip(),
                unit=row["unit"].strip(),
                frequency="monthly",
                source_start_date=source_start,
                observation_semantics=row["observation_semantics"].strip(),
                monthly_alignment=row["monthly_alignment"].strip(),
                derived_metric=row["derived_metric"].strip(),
                max_expected_lag_months=max_lag,
                revision_policy=row["revision_policy"].strip(),
                source_url=row["source_url"].strip(),
                metadata_url=row["metadata_url"].strip(),
            )
        )
    return registry


def build_sgs_url(series_code: str, start_date: date, end_date: date) -> str:
    """Build a bounded official BCData JSON request URL."""
    if start_date > end_date:
        raise ValueError("start_date must not be after end_date")
    query = urlencode(
        {
            "formato": "json",
            "dataInicial": start_date.strftime("%d/%m/%Y"),
            "dataFinal": end_date.strftime("%d/%m/%Y"),
        }
    )
    return f"{SGS_API_TEMPLATE.format(code=series_code)}?{query}"


def profile_macro_series(
    registry: Iterable[MacroSeries],
    start_date: date,
    end_date: date,
    *,
    timeout_seconds: float = 30.0,
    max_attempts: int = 3,
    retry_delay_seconds: float = 1.0,
    transport: httpx.BaseTransport | None = None,
) -> tuple[list[MacroObservation], list[MacroProfile]]:
    """Fetch the five series while retaining success or failure evidence per series."""
    if start_date > end_date:
        raise ValueError("start_date must not be after end_date")
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    retrieved_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    observations: list[MacroObservation] = []
    profiles: list[MacroProfile] = []
    with httpx.Client(
        headers={"User-Agent": DEFAULT_USER_AGENT, "Accept": "application/json"},
        follow_redirects=True,
        timeout=timeout_seconds,
        transport=transport,
    ) as client:
        for series in registry:
            url = build_sgs_url(series.series_code, start_date, end_date)
            try:
                payload = _get_json_with_retries(
                    client,
                    url,
                    max_attempts=max_attempts,
                    retry_delay_seconds=retry_delay_seconds,
                )
                series_observations = _parse_observations(
                    series.series_code, payload, retrieved_at, url
                )
                profile = _build_profile(series, series_observations, start_date, end_date)
                observations.extend(series_observations)
                profiles.append(profile)
            except (httpx.HTTPError, TypeError, ValueError) as exc:
                profiles.append(
                    _error_profile(series, start_date, end_date, f"{type(exc).__name__}: {exc}")
                )
    return observations, profiles


def _get_json_with_retries(
    client: httpx.Client,
    url: str,
    *,
    max_attempts: int,
    retry_delay_seconds: float,
) -> object:
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = client.get(url)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            last_error = exc
            if isinstance(exc, httpx.HTTPStatusError):
                status = exc.response.status_code
                if status < 500 and status != httpx.codes.TOO_MANY_REQUESTS:
                    break
            if attempt < max_attempts and retry_delay_seconds:
                time.sleep(retry_delay_seconds * attempt)
    if last_error is None:  # pragma: no cover - loop is guarded by max_attempts
        raise RuntimeError("SGS request attempted no calls")
    raise last_error


def _parse_observations(
    series_code: str,
    payload: object,
    retrieved_at: str,
    source_url: str,
) -> list[MacroObservation]:
    if not isinstance(payload, list) or not payload:
        raise ValueError(f"Series {series_code} returned no observations")
    observations: list[MacroObservation] = []
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict) or "data" not in item or "valor" not in item:
            raise ValueError(f"Series {series_code} row {index} has an invalid shape")
        try:
            observed = datetime.strptime(str(item["data"]), "%d/%m/%Y").date()
            value = Decimal(str(item["valor"]).replace(",", "."))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(f"Series {series_code} row {index} has an invalid value") from exc
        if not value.is_finite():
            raise ValueError(f"Series {series_code} row {index} has a non-finite value")
        observations.append(
            MacroObservation(
                series_code=series_code,
                source_observation_date=observed.isoformat(),
                report_month=f"{observed.year:04d}{observed.month:02d}",
                value=format(value, "f"),
                retrieved_at_utc=retrieved_at,
                source_url=source_url,
            )
        )
    return observations


def _build_profile(
    series: MacroSeries,
    observations: list[MacroObservation],
    start_date: date,
    end_date: date,
) -> MacroProfile:
    dates = [date.fromisoformat(row.source_observation_date) for row in observations]
    months = [row.report_month for row in observations]
    duplicate_dates = len(dates) - len(set(dates))
    duplicate_months = len(months) - len(set(months))
    ordered_months = sorted(set(months))
    missing_months = _missing_months(ordered_months)
    first_month = ordered_months[0]
    last_month = ordered_months[-1]
    lag = _month_difference(last_month, f"{end_date.year:04d}{end_date.month:02d}")
    errors: list[str] = []
    requested_start = f"{start_date.year:04d}{start_date.month:02d}"
    if first_month != requested_start:
        errors.append(f"first month {first_month} does not match requested {requested_start}")
    if duplicate_dates:
        errors.append(f"{duplicate_dates} duplicate observation dates")
    if duplicate_months:
        errors.append(f"{duplicate_months} duplicate report months")
    if missing_months:
        errors.append(f"{len(missing_months)} internal missing months")
    if lag < 0:
        errors.append("series returned a month after the requested end")
    if lag > series.max_expected_lag_months:
        errors.append(
            f"freshness lag {lag} exceeds expected {series.max_expected_lag_months} months"
        )
    return MacroProfile(
        series_code=series.series_code,
        status="complete" if not errors else "invalid",
        requested_start_month=requested_start,
        requested_end_month=f"{end_date.year:04d}{end_date.month:02d}",
        row_count=len(observations),
        first_observation_date=min(dates).isoformat(),
        last_observation_date=max(dates).isoformat(),
        first_report_month=first_month,
        last_report_month=last_month,
        internal_missing_month_count=len(missing_months),
        internal_missing_months="|".join(missing_months),
        duplicate_observation_date_count=duplicate_dates,
        duplicate_report_month_count=duplicate_months,
        lag_months_to_requested_end=lag,
        max_expected_lag_months=series.max_expected_lag_months,
        error="; ".join(errors) or None,
    )


def _error_profile(
    series: MacroSeries, start_date: date, end_date: date, error: str
) -> MacroProfile:
    return MacroProfile(
        series_code=series.series_code,
        status="error",
        requested_start_month=f"{start_date.year:04d}{start_date.month:02d}",
        requested_end_month=f"{end_date.year:04d}{end_date.month:02d}",
        row_count=0,
        first_observation_date=None,
        last_observation_date=None,
        first_report_month=None,
        last_report_month=None,
        internal_missing_month_count=0,
        internal_missing_months="",
        duplicate_observation_date_count=0,
        duplicate_report_month_count=0,
        lag_months_to_requested_end=None,
        max_expected_lag_months=series.max_expected_lag_months,
        error=error,
    )


def _missing_months(ordered_months: list[str]) -> list[str]:
    expected: list[str] = []
    year, month = int(ordered_months[0][:4]), int(ordered_months[0][4:])
    end_year, end_month = int(ordered_months[-1][:4]), int(ordered_months[-1][4:])
    while (year, month) <= (end_year, end_month):
        expected.append(f"{year:04d}{month:02d}")
        month += 1
        if month == 13:
            year += 1
            month = 1
    return sorted(set(expected) - set(ordered_months))


def _month_difference(earlier: str, later: str) -> int:
    return (int(later[:4]) - int(earlier[:4])) * 12 + int(later[4:]) - int(earlier[4:])


def write_macro_observations(records: Iterable[MacroObservation], output_path: Path) -> int:
    """Write native values without performing semantic derivations."""
    materialized = list(records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(MacroObservation.__dataclass_fields__))
        writer.writeheader()
        writer.writerows(record.as_dict() for record in materialized)
    return len(materialized)


def write_macro_profile(records: Iterable[MacroProfile], output_path: Path) -> int:
    """Write per-series completeness and freshness evidence."""
    materialized = list(records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(MacroProfile.__dataclass_fields__))
        writer.writeheader()
        writer.writerows(record.as_dict() for record in materialized)
    return len(materialized)


def read_macro_observations(path: Path) -> list[MacroObservation]:
    """Read typed native observations produced by the bounded profiler."""
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [
        MacroObservation(
            series_code=row["series_code"],
            source_observation_date=row["source_observation_date"],
            report_month=row["report_month"],
            value=row["value"],
            retrieved_at_utc=row["retrieved_at_utc"],
            source_url=row["source_url"],
        )
        for row in rows
    ]


def read_macro_profiles(path: Path) -> list[MacroProfile]:
    """Read typed SGS completeness evidence produced by the bounded profiler."""
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [
        MacroProfile(
            series_code=row["series_code"],
            status=row["status"],
            requested_start_month=row["requested_start_month"],
            requested_end_month=row["requested_end_month"],
            row_count=int(row["row_count"]),
            first_observation_date=row["first_observation_date"] or None,
            last_observation_date=row["last_observation_date"] or None,
            first_report_month=row["first_report_month"] or None,
            last_report_month=row["last_report_month"] or None,
            internal_missing_month_count=int(row["internal_missing_month_count"]),
            internal_missing_months=row["internal_missing_months"],
            duplicate_observation_date_count=int(row["duplicate_observation_date_count"]),
            duplicate_report_month_count=int(row["duplicate_report_month_count"]),
            lag_months_to_requested_end=(
                int(row["lag_months_to_requested_end"])
                if row["lag_months_to_requested_end"]
                else None
            ),
            max_expected_lag_months=int(row["max_expected_lag_months"]),
            error=row["error"] or None,
        )
        for row in rows
    ]


def macro_metadata_records(registry: Iterable[MacroSeries]) -> list[dict[str, object]]:
    """Convert the accepted registry to the strict raw metadata contract."""
    return [
        {
            "series_code": row.series_code,
            "theme": row.theme,
            "display_name": row.display_name,
            "official_title": row.official_title,
            "unit": row.unit,
            "frequency": row.frequency,
            "source_start_date": row.source_start_date,
            "observation_semantics": row.observation_semantics,
            "monthly_alignment": row.monthly_alignment,
            "derived_metric": row.derived_metric,
            "max_expected_lag_months": row.max_expected_lag_months,
            "revision_policy": row.revision_policy,
            "source_url": row.source_url,
            "metadata_url": row.metadata_url,
        }
        for row in registry
    ]


def build_macro_landing_records(
    registry: Iterable[MacroSeries],
    observations: Iterable[MacroObservation],
    profiles: Iterable[MacroProfile],
    requested_start_date: date,
    requested_end_date: date,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    """Convert verified SGS evidence into the three strict raw dlt contracts."""
    if requested_start_date > requested_end_date:
        raise ValueError("requested_start_date must not be after requested_end_date")
    registry_list = list(registry)
    observation_list = list(observations)
    profile_list = list(profiles)
    codes = {row.series_code for row in registry_list}
    if codes != EXPECTED_SERIES_CODES or len(registry_list) != len(EXPECTED_SERIES_CODES):
        raise ValueError("Official macro landing requires the exact five-series registry")
    if len({row.series_code for row in profile_list}) != len(profile_list):
        raise ValueError("Macro profiles contain duplicate series codes")
    profile_by_code = {row.series_code: row for row in profile_list}
    if set(profile_by_code) != codes:
        raise ValueError("Each macro series must have exactly one profile")

    observations_by_code: dict[str, list[MacroObservation]] = {
        code: [] for code in codes
    }
    seen: set[tuple[str, str]] = set()
    landing_observations: list[dict[str, object]] = []
    for row in observation_list:
        if row.series_code not in codes:
            raise ValueError(f"Unexpected macro series {row.series_code}")
        identity = (row.series_code, row.source_observation_date)
        if identity in seen:
            raise ValueError(f"Duplicate macro observation {identity}")
        seen.add(identity)
        observed = date.fromisoformat(row.source_observation_date)
        expected_month = f"{observed.year:04d}{observed.month:02d}"
        if row.report_month != expected_month:
            raise ValueError(f"Macro observation {identity} has an invalid report month")
        try:
            value = Decimal(row.value)
        except InvalidOperation as exc:
            raise ValueError(f"Macro observation {identity} has an invalid value") from exc
        if not value.is_finite():
            raise ValueError(f"Macro observation {identity} has a non-finite value")
        retrieved_at = datetime.fromisoformat(row.retrieved_at_utc)
        observations_by_code[row.series_code].append(row)
        landing_observations.append(
            {
                "series_code": row.series_code,
                "source_observation_date": observed,
                "report_month": row.report_month,
                "value_raw": row.value,
                "value": value,
                "retrieved_at_utc": retrieved_at,
                "source_url": row.source_url,
                "fixture": False,
            }
        )

    expected_start_month = f"{requested_start_date.year:04d}{requested_start_date.month:02d}"
    expected_end_month = f"{requested_end_date.year:04d}{requested_end_date.month:02d}"
    fetches: list[dict[str, object]] = []
    for code in sorted(codes, key=int):
        profile = profile_by_code[code]
        series_observations = observations_by_code[code]
        if profile.status != "complete" or profile.error:
            raise ValueError(f"Macro series {code} has not passed its profile")
        if profile.requested_start_month != expected_start_month:
            raise ValueError(f"Macro series {code} has a different requested start month")
        if profile.requested_end_month != expected_end_month:
            raise ValueError(f"Macro series {code} has a different requested end month")
        if profile.row_count != len(series_observations) or not series_observations:
            raise ValueError(f"Macro series {code} profile row count does not reconcile")
        observed_dates = sorted(row.source_observation_date for row in series_observations)
        observed_months = sorted(row.report_month for row in series_observations)
        if (
            profile.first_observation_date != observed_dates[0]
            or profile.last_observation_date != observed_dates[-1]
            or profile.first_report_month != observed_months[0]
            or profile.last_report_month != observed_months[-1]
        ):
            raise ValueError(f"Macro series {code} profile bounds do not reconcile")
        registry_series = next(row for row in registry_list if row.series_code == code)
        if profile.max_expected_lag_months != registry_series.max_expected_lag_months:
            raise ValueError(f"Macro series {code} freshness contract changed after profiling")
        retrieved_values = {row.retrieved_at_utc for row in series_observations}
        if len(retrieved_values) != 1:
            raise ValueError(f"Macro series {code} has multiple retrieval timestamps")
        fetches.append(
            {
                "series_code": code,
                "requested_start_date": requested_start_date,
                "requested_end_date": requested_end_date,
                "retrieved_at_utc": datetime.fromisoformat(next(iter(retrieved_values))),
                "status": "complete",
                "response_count": profile.row_count,
                "fixture": False,
            }
        )
    return macro_metadata_records(registry_list), landing_observations, fetches
