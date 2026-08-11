"""Load small synthetic contract fixtures into typed Python records."""

from __future__ import annotations

import csv
from collections.abc import Iterable
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from banking_analytics.parsing import parse_brl_decimal
from banking_analytics.sources.sgs import macro_metadata_records, read_macro_registry


def read_cosif_fixture(path: Path) -> list[dict[str, object]]:
    """Read typed synthetic COSIF rows with deterministic landing identities."""
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    typed: list[dict[str, object]] = []
    seen: set[tuple[str, int]] = set()
    for row in rows:
        identity = (row["source_checksum"], int(row["file_row_number"]))
        if identity in seen:
            raise ValueError(f"Duplicate COSIF fixture identity: {identity}")
        seen.add(identity)
        typed.append(
            {
                **row,
                "saldo": parse_brl_decimal(row["saldo_raw"]),
                "source_generated_at": date.fromisoformat(row["source_generated_at"]),
                "retrieved_at_utc": datetime.fromisoformat(row["retrieved_at_utc"]),
                "file_row_number": int(row["file_row_number"]),
            }
        )
    return typed


def build_cosif_fixture_manifests(rows: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    """Derive one complete source manifest per fixture checksum."""
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(str(row["source_checksum"]), []).append(row)
    manifests: list[dict[str, object]] = []
    for checksum, checksum_rows in sorted(grouped.items()):
        periods = {str(row["source_period"]) for row in checksum_rows}
        urls = {str(row["source_url"]) for row in checksum_rows}
        if len(periods) != 1 or len(urls) != 1:
            raise ValueError(f"Fixture checksum {checksum} spans periods or URLs")
        first = checksum_rows[0]
        manifests.append(
            {
                "source_period": next(iter(periods)),
                "source_url": next(iter(urls)),
                "source_checksum": checksum,
                "source_generated_at": first["source_generated_at"],
                "retrieved_at_utc": first["retrieved_at_utc"],
                "status": "complete",
                "is_active": True,
                "row_count": len(checksum_rows),
                "fixture": True,
            }
        )
    return manifests


def read_macro_fixture(path: Path) -> list[dict[str, object]]:
    """Read typed synthetic SGS observations with an explicit month key."""
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    typed: list[dict[str, object]] = []
    seen: set[tuple[str, date]] = set()
    for row in rows:
        observed = date.fromisoformat(row["source_observation_date"])
        identity = (row["series_code"], observed)
        if identity in seen:
            raise ValueError(f"Duplicate macro fixture identity: {identity}")
        seen.add(identity)
        typed.append(
            {
                **row,
                "source_observation_date": observed,
                "report_month": f"{observed.year:04d}{observed.month:02d}",
                "value": Decimal(row["value_raw"]),
                "retrieved_at_utc": datetime.fromisoformat(row["retrieved_at_utc"]),
                "fixture": True,
            }
        )
    return typed


def build_macro_metadata_fixture(registry_path: Path) -> list[dict[str, object]]:
    """Convert the accepted registry to dlt-ready metadata rows."""
    return macro_metadata_records(read_macro_registry(registry_path))
