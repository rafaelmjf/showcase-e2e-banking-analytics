"""Certify the bounded official warehouse after dlt, dbt and Dagster execution."""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import psycopg
from psycopg import sql

from banking_analytics.settings import WarehouseSettings

EXPECTED_RELATION_COUNTS = {
    "analytics_core.account_balance": 831_038,
    "analytics_core.bank_period": 2_589,
    "analytics_core.cosif_account": 1_056,
    "analytics_core.cosif_file_manifest": 15,
    "analytics_core.macro_observation": 75,
    "analytics_core.macro_series": 5,
    "raw_cosif.cosif_balance_row": 831_038,
    "raw_cosif.cosif_file_manifest": 15,
    "raw_macro.sgs_fetch_manifest": 5,
    "raw_macro.sgs_observation": 75,
    "raw_macro.sgs_series_metadata": 5,
}


@dataclass(frozen=True)
class OfficialWarehouseSnapshot:
    """Observed official warehouse, dbt and Dagster certification facts."""

    database_name: str
    relation_counts: dict[str, int]
    cosif_start_period: str
    cosif_end_period: str
    cosif_periods: int
    cosif_checksums: int
    cosif_raw_rows: int
    cosif_declared_rows: int
    macro_start_period: str
    macro_end_period: str
    macro_rows: int
    macro_series: int
    macro_fetches: int
    macro_responses: int
    raw_fixture_rows: int
    core_fixture_rows: int
    cosif_successful_loads: int
    macro_successful_loads: int
    failed_loads: int
    top15_comparisons: int
    top15_max_difference_brl: Decimal | None
    dbt_models_succeeded: int
    dbt_tests_passed: int
    dbt_failures: int
    dbt_total_results: int
    dagster_run_id: str
    dagster_status: str


@dataclass(frozen=True)
class OfficialCertificationControl:
    """One machine-readable official warehouse certification control."""

    control_name: str
    passed: bool
    expected_value: str
    actual_value: str
    detail: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _counts_text(counts: dict[str, int]) -> str:
    return "|".join(f"{name}={counts[name]}" for name in sorted(counts))


def assess_official_snapshot(
    snapshot: OfficialWarehouseSnapshot,
    *,
    expected_database: str,
) -> tuple[OfficialCertificationControl, ...]:
    """Evaluate a collected snapshot against the frozen official contract."""
    controls: list[OfficialCertificationControl] = []
    controls.append(
        OfficialCertificationControl(
            "isolated_official_database",
            snapshot.database_name == expected_database,
            expected_database,
            snapshot.database_name,
            "Certification must never reuse the fixture-backed development database.",
        )
    )
    controls.append(
        OfficialCertificationControl(
            "official_relation_counts",
            snapshot.relation_counts == EXPECTED_RELATION_COUNTS,
            _counts_text(EXPECTED_RELATION_COUNTS),
            _counts_text(snapshot.relation_counts),
            "All five raw and six canonical-core relations must match the frozen source window.",
        )
    )
    cosif_actual = (
        f"{snapshot.cosif_start_period}|{snapshot.cosif_end_period}|"
        f"periods={snapshot.cosif_periods}|checksums={snapshot.cosif_checksums}|"
        f"raw={snapshot.cosif_raw_rows}|declared={snapshot.cosif_declared_rows}"
    )
    controls.append(
        OfficialCertificationControl(
            "official_cosif_coverage",
            snapshot.cosif_start_period == "202501"
            and snapshot.cosif_end_period == "202603"
            and snapshot.cosif_periods == 15
            and snapshot.cosif_checksums == 15
            and snapshot.cosif_raw_rows == 831_038
            and snapshot.cosif_declared_rows == 831_038,
            "202501|202603|periods=15|checksums=15|raw=831038|declared=831038",
            cosif_actual,
            "Manifest identities and declared volumes must reconcile to landed balances.",
        )
    )
    macro_actual = (
        f"{snapshot.macro_start_period}|{snapshot.macro_end_period}|"
        f"series={snapshot.macro_series}|rows={snapshot.macro_rows}|"
        f"fetches={snapshot.macro_fetches}|responses={snapshot.macro_responses}"
    )
    controls.append(
        OfficialCertificationControl(
            "official_macro_coverage",
            snapshot.macro_start_period == "202501"
            and snapshot.macro_end_period == "202603"
            and snapshot.macro_series == 5
            and snapshot.macro_rows == 75
            and snapshot.macro_fetches == 5
            and snapshot.macro_responses == 75,
            "202501|202603|series=5|rows=75|fetches=5|responses=75",
            macro_actual,
            "All frozen SGS series require one observation per month and a clean fetch record.",
        )
    )
    controls.append(
        OfficialCertificationControl(
            "official_rows_are_fixture_free",
            snapshot.raw_fixture_rows == 0 and snapshot.core_fixture_rows == 0,
            "raw=0|core=0",
            f"raw={snapshot.raw_fixture_rows}|core={snapshot.core_fixture_rows}",
            "No fact-like official certification relation may contain fixture-labelled rows.",
        )
    )
    controls.append(
        OfficialCertificationControl(
            "official_dlt_replay_idempotent",
            snapshot.cosif_successful_loads >= 2
            and snapshot.macro_successful_loads >= 2
            and snapshot.failed_loads == 0,
            "cosif_success>=2|macro_success>=2|failed=0",
            f"cosif_success={snapshot.cosif_successful_loads}|"
            f"macro_success={snapshot.macro_successful_loads}|failed={snapshot.failed_loads}",
            "Direct and Dagster dlt executions must leave stable identities and only "
            "successful loads.",
        )
    )
    controls.append(
        OfficialCertificationControl(
            "official_raw_core_reconciliation",
            snapshot.relation_counts.get("raw_cosif.cosif_balance_row")
            == snapshot.relation_counts.get("analytics_core.account_balance")
            and snapshot.relation_counts.get("raw_cosif.cosif_file_manifest")
            == snapshot.relation_counts.get("analytics_core.cosif_file_manifest")
            and snapshot.relation_counts.get("raw_macro.sgs_observation")
            == snapshot.relation_counts.get("analytics_core.macro_observation")
            and snapshot.relation_counts.get("raw_macro.sgs_series_metadata")
            == snapshot.relation_counts.get("analytics_core.macro_series"),
            "balances=831038|manifests=15|observations=75|series=5",
            f"balances={snapshot.relation_counts.get('analytics_core.account_balance', 0)}|"
            f"manifests={snapshot.relation_counts.get('analytics_core.cosif_file_manifest', 0)}|"
            f"observations={snapshot.relation_counts.get('analytics_core.macro_observation', 0)}|"
            f"series={snapshot.relation_counts.get('analytics_core.macro_series', 0)}",
            "Canonical core must preserve the selected raw official identities.",
        )
    )
    max_difference = snapshot.top15_max_difference_brl
    controls.append(
        OfficialCertificationControl(
            "official_top15_total_assets_reconciliation",
            snapshot.top15_comparisons == 225
            and max_difference is not None
            and max_difference <= Decimal("0.01"),
            "225/225|max_difference_brl<=0.01",
            f"{snapshot.top15_comparisons}/225|max_difference_brl="
            f"{max_difference if max_difference is not None else 'missing'}",
            "The core 4010 class-1 plus class-2 balances must reproduce checkpoint 0C.",
        )
    )
    controls.append(
        OfficialCertificationControl(
            "official_dbt_build",
            snapshot.dbt_models_succeeded == 11
            and snapshot.dbt_tests_passed == 106
            and snapshot.dbt_failures == 0
            and snapshot.dbt_total_results == 117,
            "models=11|tests=106|failures=0|total=117",
            f"models={snapshot.dbt_models_succeeded}|tests={snapshot.dbt_tests_passed}|"
            f"failures={snapshot.dbt_failures}|total={snapshot.dbt_total_results}",
            "The official dbt result artifact must contain every implemented model and test.",
        )
    )
    try:
        UUID(snapshot.dagster_run_id)
        valid_run_id = True
    except ValueError:
        valid_run_id = False
    controls.append(
        OfficialCertificationControl(
            "official_dagster_run",
            valid_run_id and snapshot.dagster_status == "success",
            "valid_uuid|success",
            f"{snapshot.dagster_run_id}|{snapshot.dagster_status}",
            "The terminal official_end_to_end result is recorded from the attached CLI execution.",
        )
    )
    ready = all(control.passed for control in controls)
    controls.append(
        OfficialCertificationControl(
            "official_warehouse_certified",
            ready,
            "certified",
            "certified" if ready else "blocked",
            "This certifies landing and canonical core only; reporting marts remain separate.",
        )
    )
    return tuple(controls)


def _read_population(path: Path) -> dict[tuple[str, str], Decimal]:
    if not path.is_file():
        raise ValueError(f"Population evidence is missing: {path}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {
        (row["report_period"], row["institution_cnpj"]): Decimal(row["total_assets_brl"])
        for row in rows
    }


def _read_dbt_results(path: Path) -> tuple[int, int, int, int]:
    if not path.is_file():
        raise ValueError(f"dbt run results are missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    results = payload.get("results", [])
    statuses = Counter(str(result.get("status", "")) for result in results)
    return (
        statuses["success"],
        statuses["pass"],
        len(results) - statuses["success"] - statuses["pass"],
        len(results),
    )


def collect_official_snapshot(
    settings: WarehouseSettings,
    *,
    population_monthly: Path,
    dbt_run_results: Path,
    dagster_run_id: str,
    dagster_status: str,
) -> OfficialWarehouseSnapshot:
    """Collect bounded official certification facts from PostgreSQL and artifacts."""
    population = _read_population(population_monthly)
    with psycopg.connect(settings.dsn) as connection, connection.cursor() as cursor:
        cursor.execute("select current_database()")
        database_name = str((cursor.fetchone() or ("",))[0])
        relation_counts: dict[str, int] = {}
        for relation in EXPECTED_RELATION_COUNTS:
            schema, table = relation.split(".")
            cursor.execute(
                sql.SQL("select count(*) from {}.{}").format(
                    sql.Identifier(schema), sql.Identifier(table)
                )
            )
            relation_counts[relation] = int((cursor.fetchone() or (0,))[0])

        cursor.execute(
            """
            select min(source_period), max(source_period), count(distinct source_period),
                   count(distinct source_checksum), count(*),
                   (select sum(declared_row_count)
                    from analytics_core.cosif_file_manifest)
            from analytics_core.account_balance
            """
        )
        cosif = cursor.fetchone() or ("", "", 0, 0, 0, 0)
        cursor.execute(
            """
            select min(to_char(report_month, 'YYYYMM')),
                   max(to_char(report_month, 'YYYYMM')),
                   count(*), count(distinct series_code)
            from analytics_core.macro_observation
            """
        )
        macro = cursor.fetchone() or ("", "", 0, 0)
        cursor.execute(
            "select count(*), coalesce(sum(response_count), 0) from raw_macro.sgs_fetch_manifest"
        )
        macro_fetch = cursor.fetchone() or (0, 0)
        cursor.execute(
            """
            select
              (select count(*) from raw_cosif.cosif_file_manifest where fixture)
              + (select count(*) from raw_macro.sgs_observation where fixture)
              + (select count(*) from raw_macro.sgs_fetch_manifest where fixture),
              (select count(*) from analytics_core.account_balance where is_fixture)
              + (select count(*) from analytics_core.macro_observation where is_fixture)
            """
        )
        fixture_counts = cursor.fetchone() or (0, 0)
        cursor.execute(
            """
            select
              (select count(*) from raw_cosif._dlt_loads where status = 0),
              (select count(*) from raw_macro._dlt_loads where status = 0),
              (select count(*) from raw_cosif._dlt_loads where status <> 0)
              + (select count(*) from raw_macro._dlt_loads where status <> 0)
            """
        )
        loads = cursor.fetchone() or (0, 0, 0)
        cursor.execute(
            """
            select source_period, institution_cnpj, sum(balance_amount)
            from analytics_core.account_balance
            where document_code = '4010'
              and account_code in ('1000000009', '2000000008')
            group by source_period, institution_cnpj
            """
        )
        actual_assets = {
            (str(period), str(cnpj)): Decimal(total) for period, cnpj, total in cursor.fetchall()
        }

    differences = [
        abs(actual_assets[key] - expected)
        for key, expected in population.items()
        if key in actual_assets
    ]
    dbt_models, dbt_tests, dbt_failures, dbt_total = _read_dbt_results(dbt_run_results)
    return OfficialWarehouseSnapshot(
        database_name=database_name,
        relation_counts=relation_counts,
        cosif_start_period=str(cosif[0]),
        cosif_end_period=str(cosif[1]),
        cosif_periods=int(cosif[2]),
        cosif_checksums=int(cosif[3]),
        cosif_raw_rows=int(cosif[4]),
        cosif_declared_rows=int(cosif[5]),
        macro_start_period=str(macro[0]),
        macro_end_period=str(macro[1]),
        macro_rows=int(macro[2]),
        macro_series=int(macro[3]),
        macro_fetches=int(macro_fetch[0]),
        macro_responses=int(macro_fetch[1]),
        raw_fixture_rows=int(fixture_counts[0]),
        core_fixture_rows=int(fixture_counts[1]),
        cosif_successful_loads=int(loads[0]),
        macro_successful_loads=int(loads[1]),
        failed_loads=int(loads[2]),
        top15_comparisons=len(differences),
        top15_max_difference_brl=max(differences) if differences else None,
        dbt_models_succeeded=dbt_models,
        dbt_tests_passed=dbt_tests,
        dbt_failures=dbt_failures,
        dbt_total_results=dbt_total,
        dagster_run_id=dagster_run_id,
        dagster_status=dagster_status,
    )


def write_official_certification(
    controls: tuple[OfficialCertificationControl, ...], output: Path
) -> int:
    """Write official certification controls to CSV."""
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = [control.as_dict() for control in controls]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)
