"""Discovery helpers for BCB COSIF bank balance files."""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import httpx

BANKS_BASE_URL = "https://www.bcb.gov.br/content/estabilidadefinanceira/cosif/Bancos"
BANKS_CATALOG_URL = (
    "https://www.bcb.gov.br/api/servico/sitebcb/Documentos/byListGuid"
    "?tronco=estabilidadefinanceira"
    "&guidLista=a11917e4-c729-4259-bd4e-0266827b6acd"
    "&ordem=DataDocumento%20desc"
    "&pasta=/Bancos"
)
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


@dataclass(frozen=True)
class CatalogRecord:
    """One bank file advertised by the official BCB document catalog."""

    period: str | None
    period_version: int | None
    is_active: bool | None
    title: str | None
    source_url: str | None
    document_date: str | None
    discovered_at_utc: str
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


def parse_bank_catalog(
    payload: dict[str, Any],
    *,
    discovered_at_utc: str,
) -> list[CatalogRecord]:
    """Parse the official document-list response without discarding anomalies."""
    content = payload.get("conteudo")
    if not isinstance(content, list):
        raise ValueError("BCB bank catalog response has no 'conteudo' list")

    records: list[CatalogRecord] = []
    for item in content:
        if not isinstance(item, dict):
            records.append(
                CatalogRecord(
                    period=None,
                    period_version=None,
                    is_active=None,
                    title=None,
                    source_url=None,
                    document_date=None,
                    discovered_at_utc=discovered_at_utc,
                    error="Catalog item is not an object",
                )
            )
            continue

        raw_url = _optional_text(item.get("Url"))
        source_url = urljoin("https://www.bcb.gov.br", raw_url) if raw_url else None
        period_match = re.search(
            r"/(\d{6})BANCOS(?:\.[^/?#]+)+$",
            source_url or "",
            re.I,
        )
        period = period_match.group(1) if period_match else None
        error = None if period else "Unrecognized or missing bank file URL"
        records.append(
            CatalogRecord(
                period=period,
                period_version=None,
                is_active=None,
                title=_first_text(item, "Titulo", "Nome", "Title", "Name"),
                source_url=source_url,
                document_date=_first_text(item, "DataDocumento", "DataPublicacao"),
                discovered_at_utc=discovered_at_utc,
                error=error,
            )
        )
    by_period: dict[str, list[int]] = defaultdict(list)
    for index, record in enumerate(records):
        if record.period:
            by_period[record.period].append(index)

    for indexes in by_period.values():
        indexes.sort(
            key=lambda index: (
                records[index].document_date or "",
                records[index].source_url or "",
            )
        )
        for version, index in enumerate(indexes, start=1):
            records[index] = replace(
                records[index],
                period_version=version,
                is_active=version == len(indexes),
            )
    return records


def _optional_text(value: object) -> str | None:
    """Normalize optional catalog text."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _first_text(item: dict[str, Any], *keys: str) -> str | None:
    """Return the first non-empty catalog field from known API variants."""
    for key in keys:
        value = _optional_text(item.get(key))
        if value:
            return value
    return None


def probe_bank_period(
    client: httpx.Client,
    period: str,
    *,
    checked_at_utc: str,
    url: str | None = None,
) -> AvailabilityRecord:
    """Probe one official bank file without downloading its body."""
    url = url or build_bank_url(period)
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
    url_by_period: Mapping[str, str] | None = None,
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
            probe_bank_period(
                client,
                period,
                checked_at_utc=checked_at_utc,
                url=(url_by_period or {}).get(period),
            )
            for period in iter_periods(start_period, end_period)
        ]


def build_source_catalog(
    *,
    timeout_seconds: float = 20.0,
    transport: httpx.BaseTransport | None = None,
) -> list[CatalogRecord]:
    """Read the official BCB bank-file catalog."""
    discovered_at_utc = datetime.now(UTC).replace(microsecond=0).isoformat()
    headers = {"User-Agent": DEFAULT_USER_AGENT, "Accept": "application/json"}
    with httpx.Client(
        headers=headers,
        follow_redirects=True,
        timeout=timeout_seconds,
        transport=transport,
    ) as client:
        response = client.get(BANKS_CATALOG_URL)
        response.raise_for_status()
        payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("BCB bank catalog response is not an object")
    return parse_bank_catalog(payload, discovered_at_utc=discovered_at_utc)


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


def write_source_catalog(records: Iterable[CatalogRecord], output_path: Path) -> int:
    """Write catalog records to CSV and return the number written."""
    materialized = list(records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(CatalogRecord.__dataclass_fields__)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(record.as_dict() for record in materialized)
    return len(materialized)


def read_active_catalog_urls(catalog_path: Path) -> dict[str, str]:
    """Read active period URLs from a catalog CSV produced by this project."""
    with catalog_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    active_urls: dict[str, str] = {}
    for row in rows:
        if row.get("is_active", "").lower() != "true":
            continue
        period = row.get("period", "").strip()
        source_url = row.get("source_url", "").strip()
        if not period or not source_url:
            raise ValueError("Active catalog row is missing period or source_url")
        if period in active_urls:
            raise ValueError(f"Catalog contains multiple active URLs for period {period}")
        active_urls[period] = source_url
    if not active_urls:
        raise ValueError("Catalog contains no active bank file URLs")
    return active_urls
