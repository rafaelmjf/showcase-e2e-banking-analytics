"""dlt resources for verified SGS metadata and native observations."""

from __future__ import annotations

from collections.abc import Iterable

import dlt

STRICT_COLUMNS = {"tables": "evolve", "columns": "freeze", "data_type": "freeze"}


def _text() -> dict[str, object]:
    """Return a fresh dlt hint because dlt annotates column dictionaries in place."""
    return {"data_type": "text", "nullable": False}

METADATA_COLUMNS = {
    "series_code": _text(),
    "theme": _text(),
    "display_name": _text(),
    "official_title": _text(),
    "unit": _text(),
    "frequency": _text(),
    "source_start_date": {"data_type": "date", "nullable": False},
    "observation_semantics": _text(),
    "monthly_alignment": _text(),
    "derived_metric": _text(),
    "max_expected_lag_months": {"data_type": "bigint", "nullable": False},
    "revision_policy": _text(),
    "source_url": _text(),
    "metadata_url": _text(),
}

OBSERVATION_COLUMNS = {
    "series_code": _text(),
    "source_observation_date": {"data_type": "date", "nullable": False},
    "report_month": _text(),
    "value_raw": _text(),
    "value": {"data_type": "decimal", "nullable": False, "precision": 38, "scale": 10},
    "retrieved_at_utc": {"data_type": "timestamp", "nullable": False, "timezone": True},
    "source_url": _text(),
    "fixture": {"data_type": "bool", "nullable": False},
}

FETCH_COLUMNS = {
    "series_code": _text(),
    "requested_start_date": {"data_type": "date", "nullable": False},
    "requested_end_date": {"data_type": "date", "nullable": False},
    "retrieved_at_utc": {"data_type": "timestamp", "nullable": False, "timezone": True},
    "status": _text(),
    "response_count": {"data_type": "bigint", "nullable": False},
    "fixture": {"data_type": "bool", "nullable": False},
}


@dlt.resource(
    name="sgs_series_metadata",
    write_disposition="merge",
    primary_key="series_code",
    columns=METADATA_COLUMNS,
    schema_contract=STRICT_COLUMNS,
)
def sgs_series_metadata(rows: Iterable[dict[str, object]]):
    """One accepted semantic contract per SGS series code."""
    yield from rows


@dlt.resource(
    name="sgs_observation",
    write_disposition="merge",
    primary_key=["series_code", "source_observation_date"],
    columns=OBSERVATION_COLUMNS,
    schema_contract=STRICT_COLUMNS,
)
def sgs_observation(rows: Iterable[dict[str, object]]):
    """One native source observation plus its explicit calendar-month key."""
    yield from rows


@dlt.resource(
    name="sgs_fetch_manifest",
    write_disposition="merge",
    primary_key=["series_code", "requested_start_date", "requested_end_date", "fixture"],
    columns=FETCH_COLUMNS,
    schema_contract=STRICT_COLUMNS,
)
def sgs_fetch_manifest(rows: Iterable[dict[str, object]]):
    """One bounded acquisition result per series and request window."""
    yield from rows


@dlt.source(name="macro_landing")
def macro_landing_source(
    metadata: Iterable[dict[str, object]],
    observations: Iterable[dict[str, object]],
    fetches: Iterable[dict[str, object]],
):
    """Return the bounded macro raw landing source."""
    return (
        sgs_series_metadata(metadata),
        sgs_observation(observations),
        sgs_fetch_manifest(fetches),
    )
