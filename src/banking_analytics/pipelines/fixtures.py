"""Run synthetic contract fixtures through the real PostgreSQL dlt destinations."""

from __future__ import annotations

import csv
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

import dlt
import psycopg
from dlt.destinations import postgres

from banking_analytics.fixtures import (
    build_cosif_fixture_manifests,
    build_macro_metadata_fixture,
    read_cosif_fixture,
    read_macro_fixture,
)
from banking_analytics.pipelines.cosif import cosif_landing_source
from banking_analytics.pipelines.macro import macro_landing_source
from banking_analytics.settings import WarehouseSettings


@dataclass(frozen=True)
class FixtureControl:
    """One database assertion from the fixture landing smoke test."""

    control_name: str
    expected_value: int
    actual_value: int
    passed: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


COUNT_CONTROLS = {
    "raw_cosif.cosif_file_manifest": (
        2,
        "select count(*), count(distinct source_checksum) "
        "from raw_cosif.cosif_file_manifest",
    ),
    "raw_cosif.cosif_balance_row": (
        24,
        "select count(*), count(distinct (source_checksum, file_row_number)) "
        "from raw_cosif.cosif_balance_row",
    ),
    "raw_macro.sgs_series_metadata": (
        5,
        "select count(*), count(distinct series_code) "
        "from raw_macro.sgs_series_metadata",
    ),
    "raw_macro.sgs_observation": (
        15,
        "select count(*), count(distinct (series_code, source_observation_date)) "
        "from raw_macro.sgs_observation",
    ),
    "raw_macro.sgs_fetch_manifest": (
        5,
        "select count(*), count(distinct "
        "(series_code, requested_start_date, requested_end_date, fixture)) "
        "from raw_macro.sgs_fetch_manifest",
    ),
}

RECONCILIATION_SQL = """
with bank_month as (
    select
        source_period,
        cnpj,
        sum(saldo) filter (where conta = '1000000009') as class_1,
        sum(saldo) filter (where conta = '2000000008') as class_2,
        sum(saldo) filter (where conta = '3000000007') as class_3,
        sum(saldo) filter (where conta = '3999999009') as total_general
    from raw_cosif.cosif_balance_row
    group by source_period, cnpj
)
select count(*)
from bank_month
where abs((class_1 + class_2) - (total_general - class_3)) > 0.01
"""


def build_macro_fixture_fetches(observations: list[dict[str, object]]) -> list[dict[str, object]]:
    """Derive deterministic successful request manifests from fixture observations."""
    counts = Counter(str(row["series_code"]) for row in observations)
    dates_by_code: dict[str, list[date]] = {}
    for row in observations:
        dates_by_code.setdefault(str(row["series_code"]), []).append(
            row["source_observation_date"]  # type: ignore[arg-type]
        )
    return [
        {
            "series_code": code,
            "requested_start_date": min(dates),
            "requested_end_date": max(dates),
            "retrieved_at_utc": next(
                row["retrieved_at_utc"]
                for row in observations
                if str(row["series_code"]) == code
            ),
            "status": "complete",
            "response_count": counts[code],
            "fixture": True,
        }
        for code, dates in sorted(dates_by_code.items(), key=lambda item: int(item[0]))
    ]


def run_fixture_pipelines(
    project_root: Path,
    settings: WarehouseSettings | None = None,
) -> tuple[dlt.common.pipeline.LoadInfo, dlt.common.pipeline.LoadInfo]:
    """Load both fixture sources with the same schemas used by live acquisition."""
    settings = settings or WarehouseSettings()
    destination = postgres(credentials=settings.dsn)
    pipelines_dir = project_root / "data" / "work" / "dlt"
    cosif_rows = read_cosif_fixture(project_root / "fixtures" / "cosif_balance_rows.csv")
    cosif_manifests = build_cosif_fixture_manifests(cosif_rows)
    macro_rows = read_macro_fixture(project_root / "fixtures" / "macro_observations.csv")
    macro_metadata = build_macro_metadata_fixture(
        project_root / "config" / "macro_series_registry.csv"
    )
    macro_fetches = build_macro_fixture_fetches(macro_rows)

    cosif_pipeline = dlt.pipeline(
        pipeline_name="banking_cosif",
        pipelines_dir=str(pipelines_dir),
        destination=destination,
        dataset_name="raw_cosif",
    )
    cosif_info = cosif_pipeline.run(
        cosif_landing_source(cosif_manifests, cosif_rows),
        loader_file_format="insert_values",
    )

    macro_pipeline = dlt.pipeline(
        pipeline_name="banking_macro",
        pipelines_dir=str(pipelines_dir),
        destination=destination,
        dataset_name="raw_macro",
    )
    macro_info = macro_pipeline.run(
        macro_landing_source(macro_metadata, macro_rows, macro_fetches),
        loader_file_format="insert_values",
    )
    return cosif_info, macro_info


def verify_fixture_landing(settings: WarehouseSettings | None = None) -> list[FixtureControl]:
    """Verify exact row identities and the fixture accounting reconciliation."""
    settings = settings or WarehouseSettings()
    controls: list[FixtureControl] = []
    with psycopg.connect(settings.dsn) as connection, connection.cursor() as cursor:
        for table_name, (expected, query) in COUNT_CONTROLS.items():
            cursor.execute(query)  # type: ignore[arg-type]
            actual, unique_count = cursor.fetchone() or (0, 0)
            controls.append(
                FixtureControl(
                    control_name=f"{table_name}.row_count",
                    expected_value=expected,
                    actual_value=actual,
                    passed=actual == expected,
                )
            )
            controls.append(
                FixtureControl(
                    control_name=f"{table_name}.unique_identity_count",
                    expected_value=expected,
                    actual_value=unique_count,
                    passed=unique_count == expected,
                )
            )
        cursor.execute(RECONCILIATION_SQL)
        failures = (cursor.fetchone() or (0,))[0]
        controls.append(
            FixtureControl(
                control_name="raw_cosif.accounting_identity_failure_count",
                expected_value=0,
                actual_value=failures,
                passed=failures == 0,
            )
        )
    return controls


def write_fixture_controls(records: Iterable[FixtureControl], output_path: Path) -> int:
    """Write stable database verification evidence."""
    materialized = list(records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(FixtureControl.__dataclass_fields__))
        writer.writeheader()
        writer.writerows(record.as_dict() for record in materialized)
    return len(materialized)
