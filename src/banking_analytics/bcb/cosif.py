"""Discovery helpers for BCB COSIF bank balance files."""

from __future__ import annotations

import csv
import re
from collections.abc import Iterable, Iterator
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import httpx

BANKS_BASE_URL = "https://www.bcb.gov.br/content/estabilidadefinanceira/cosif/Bancos"
DEFAULT_USER_AGENT = (
    "showcase-e2e-banking-analytics/0.1 "
    "(+https://github.com/rafaelmjf/showcase-e2e-banking-analytics)"
)


@dataclass(frozen=True)
class AvailabilityRecord:
    """Observed availability and HTTP metadata for one reporting period."""

    period: str
    url: str
    probe_method: str
    available: bool | None
    status_code: int | None
    content_length_bytes: int | None
    content_type: str | None
    last_modified: str | None
    etag: str | None
    checked_at_utc: str
    error: str | None

    def as_dict(self) -> dict[str, object]:
        """Return a stable CSV-ready representation."""
        return asdict(self)


def validate_period(period: str) -> tuple[int, int]:
    """Validate a YYYYMM period and return its year and month."""
    if len(period) != 6 or not period.isdigit():
        raise ValueError(f"Invalid reporting period {period!r}; expected YYYYMM")
    year = int(period[:4])
    month = int(period[4:])
    if year < 1988 or month not in range(1, 13):
        raise ValueError(f"Invalid reporting period {period!r}; expected YYYYMM")
    return year, month


def iter_periods(start_period: str, end_period: str) -> Iterator[str]:
    """Yield inclusive YYYYMM periods in chronological order."""
    start_year, start_month = validate_period(start_period)
    end_year, end_month = validate_period(end_period)
    if (start_year, start_month) > (end_year, end_month):
        raise ValueError("start_period must not be after end_period")

    year, month = start_year, start_month
    while (year, month) <= (end_year, end_month):
        yield f"{year:04d}{month:02d}"
        if month == 12:
            year, month = year + 1, 1
        else:
            month += 1


def build_bank_url(period: str) -> str:
    """Build the official BCB bulk URL for one bank reporting period."""
    validate_period(period)
    return f"{BANKS_BASE_URL}/{period}BANCOS.csv.zip"


def probe_bank_period(
    client: httpx.Client,
    period: str,
    *,
    checked_at_utc: str,
) -> AvailabilityRecord:
    """Probe one official bank file without downloading its body."""
    url = build_bank_url(period)
    try:
        response = client.head(url)
        if response.status_code in {httpx.codes.OK, httpx.codes.NOT_FOUND}:
            return _availability_record(
                period=period,
                url=url,
                probe_method="HEAD",
                response=response,
                checked_at_utc=checked_at_utc,
            )

        # Some servers and intermediaries reject HEAD even though GET works. A
        # streamed range request validates the resource without consuming the body.
        with client.stream("GET", url, headers={"Range": "bytes=0-0"}) as response:
            return _availability_record(
                period=period,
                url=url,
                probe_method="GET_RANGE",
                response=response,
                checked_at_utc=checked_at_utc,
            )
    except (httpx.HTTPError, ValueError) as exc:
        return AvailabilityRecord(
            period=period,
            url=url,
            probe_method="HEAD_OR_GET_RANGE",
            available=None,
            status_code=None,
            content_length_bytes=None,
            content_type=None,
            last_modified=None,
            etag=None,
            checked_at_utc=checked_at_utc,
            error=f"{type(exc).__name__}: {exc}",
        )


def _availability_record(
    *,
    period: str,
    url: str,
    probe_method: str,
    response: httpx.Response,
    checked_at_utc: str,
) -> AvailabilityRecord:
    """Translate one HTTP response without treating server errors as absence."""
    status_code = response.status_code
    if status_code in {httpx.codes.OK, httpx.codes.PARTIAL_CONTENT}:
        available: bool | None = True
        error = None
    elif status_code == httpx.codes.NOT_FOUND:
        available = False
        error = None
    else:
        available = None
        error = f"HTTP {status_code}"

    content_length = response.headers.get("content-length")
    content_range = response.headers.get("content-range")
    range_match = re.search(r"/(\d+)$", content_range or "")
    if range_match:
        content_length_bytes = int(range_match.group(1))
    else:
        content_length_bytes = int(content_length) if content_length else None

    return AvailabilityRecord(
        period=period,
        url=url,
        probe_method=probe_method,
        available=available,
        status_code=status_code,
        content_length_bytes=content_length_bytes,
        content_type=response.headers.get("content-type"),
        last_modified=response.headers.get("last-modified"),
        etag=response.headers.get("etag"),
        checked_at_utc=checked_at_utc,
        error=error,
    )


def build_source_inventory(
    start_period: str,
    end_period: str,
    *,
    timeout_seconds: float = 20.0,
    transport: httpx.BaseTransport | None = None,
) -> list[AvailabilityRecord]:
    """Probe an inclusive range of official bank files."""
    checked_at_utc = datetime.now(UTC).replace(microsecond=0).isoformat()
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    with httpx.Client(
        headers=headers,
        follow_redirects=True,
        timeout=timeout_seconds,
        transport=transport,
    ) as client:
        return [
            probe_bank_period(client, period, checked_at_utc=checked_at_utc)
            for period in iter_periods(start_period, end_period)
        ]


def write_source_inventory(
    records: Iterable[AvailabilityRecord],
    output_path: Path,
) -> int:
    """Write inventory records to CSV and return the number written."""
    materialized = list(records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(AvailabilityRecord.__dataclass_fields__)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(record.as_dict() for record in materialized)
    return len(materialized)
