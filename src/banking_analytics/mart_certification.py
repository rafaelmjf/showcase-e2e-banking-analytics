"""Certify the frozen official reporting-mart consumption boundary."""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import psycopg
import yaml
from psycopg import sql

from banking_analytics.settings import WarehouseSettings

MAPPING_VERSION = "2026-08-11-v1"
EXPECTED_MAPPING_ACCOUNTS = {
    "1000000009",
    "1600000007",
    "1700000000",
    "1810000000",
    "2000000008",
    "4100000009",
    "6000000004",
}
EXPECTED_MART_COUNTS = {
    "bridge_account_reporting_line": 7,
    "dim_bank": 15,
    "dim_cosif_account": 1_056,
    "dim_date": 15,
    "dim_document": 2,
    "dim_macro_series": 5,
    "dim_reporting_line": 4,
    "dim_source_file": 15,
    "fact_account_balance": 121_092,
    "fact_macro_observation": 75,
    "fact_monthly_economic_context": 75,
    "fact_reporting_line_balance": 900,
}


@dataclass(frozen=True)
class ReportingMartSnapshot:
    """Observed official mart, contract, dbt and Dagster facts."""

    database_name: str
    relation_counts: dict[str, int]
    mapping_rows: int
    mapping_versions: tuple[str, ...]
    mapping_statuses: tuple[str, ...]
    mapping_accounts: frozenset[str]
    fixture_rows: int
    population_banks: int
    population_months: int
    total_asset_rows: int
    reporting_rows: int
    reporting_lines: int
    reconciliation_mismatches: int
    reconciliation_max_difference_brl: Decimal
    top15_comparisons: int
    top15_max_difference_brl: Decimal | None
    macro_rows: int
    macro_series: int
    macro_months: int
    dbt_models_succeeded: int
    dbt_seeds_succeeded: int
    dbt_tests_passed: int
    dbt_failures: int
    dbt_total_results: int
    contract_name: str
    contract_version: str
    contract_mapping_version: str
    contract_object_count: int
    contract_schema_issues: tuple[str, ...]
    dagster_run_id: str
    dagster_status: str


@dataclass(frozen=True)
class ReportingMartControl:
    """One machine-readable reporting-mart certification control."""

    control_name: str
    passed: bool
    expected_value: str
    actual_value: str
    detail: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _counts_text(counts: dict[str, int]) -> str:
    return "|".join(f"{name}={counts[name]}" for name in sorted(counts))


def assess_reporting_mart_snapshot(
    snapshot: ReportingMartSnapshot,
    *,
    expected_database: str,
) -> tuple[ReportingMartControl, ...]:
    """Evaluate an observed snapshot against the frozen mart contract."""
    controls: list[ReportingMartControl] = []
    controls.append(
        ReportingMartControl(
            "isolated_official_database",
            snapshot.database_name == expected_database,
            expected_database,
            snapshot.database_name,
            "Mart certification must never reuse the fixture development database.",
        )
    )
    controls.append(
        ReportingMartControl(
            "official_mart_relation_counts",
            snapshot.relation_counts == EXPECTED_MART_COUNTS,
            _counts_text(EXPECTED_MART_COUNTS),
            _counts_text(snapshot.relation_counts),
            "All twelve frozen consumption objects must match the official reference build.",
        )
    )
    mapping_actual = (
        f"rows={snapshot.mapping_rows}|versions={','.join(snapshot.mapping_versions)}|"
        f"statuses={','.join(snapshot.mapping_statuses)}|accounts="
        f"{','.join(sorted(snapshot.mapping_accounts))}"
    )
    controls.append(
        ReportingMartControl(
            "reporting_line_mapping_frozen",
            snapshot.mapping_rows == 7
            and snapshot.mapping_versions == (MAPPING_VERSION,)
            and snapshot.mapping_statuses == ("certified",)
            and snapshot.mapping_accounts == EXPECTED_MAPPING_ACCOUNTS,
            f"rows=7|versions={MAPPING_VERSION}|statuses=certified|accounts="
            f"{','.join(sorted(EXPECTED_MAPPING_ACCOUNTS))}",
            mapping_actual,
            "Seven non-overlapping top-level COSIF accounts define the four reporting lines.",
        )
    )
    controls.append(
        ReportingMartControl(
            "official_marts_are_fixture_free",
            snapshot.fixture_rows == 0,
            "0",
            str(snapshot.fixture_rows),
            "Every official dimension or fact carrying fixture lineage must be fixture-free.",
        )
    )
    controls.append(
        ReportingMartControl(
            "stable_population_coverage",
            snapshot.population_banks == 15
            and snapshot.population_months == 15
            and snapshot.total_asset_rows == 225,
            "banks=15|months=15|total_asset_rows=225",
            f"banks={snapshot.population_banks}|months={snapshot.population_months}|"
            f"total_asset_rows={snapshot.total_asset_rows}",
            "The frozen top-15 population must be comparable across all fifteen months.",
        )
    )
    controls.append(
        ReportingMartControl(
            "reporting_line_coverage",
            snapshot.reporting_rows == 900 and snapshot.reporting_lines == 4,
            "rows=900|lines=4",
            f"rows={snapshot.reporting_rows}|lines={snapshot.reporting_lines}",
            "Each of fifteen banks and fifteen months requires all four reporting lines.",
        )
    )
    controls.append(
        ReportingMartControl(
            "reporting_line_account_reconciliation",
            snapshot.reconciliation_mismatches == 0
            and snapshot.reconciliation_max_difference_brl <= Decimal("0.01"),
            "mismatches=0|max_difference_brl<=0.01",
            f"mismatches={snapshot.reconciliation_mismatches}|max_difference_brl="
            f"{snapshot.reconciliation_max_difference_brl}",
            "Reporting facts must reproduce the mapped source-account sums exactly.",
        )
    )
    controls.append(
        ReportingMartControl(
            "top15_total_assets_reconciliation",
            snapshot.top15_comparisons == 225
            and snapshot.top15_max_difference_brl is not None
            and snapshot.top15_max_difference_brl <= Decimal("0.01"),
            "225/225|max_difference_brl<=0.01",
            f"{snapshot.top15_comparisons}/225|max_difference_brl="
            + (
                str(snapshot.top15_max_difference_brl)
                if snapshot.top15_max_difference_brl is not None
                else "missing"
            ),
            "The total-assets mart line must reproduce the frozen checkpoint 0C evidence.",
        )
    )
    controls.append(
        ReportingMartControl(
            "monthly_macro_context_coverage",
            snapshot.macro_rows == 75
            and snapshot.macro_series == 5
            and snapshot.macro_months == 15,
            "rows=75|series=5|months=15",
            f"rows={snapshot.macro_rows}|series={snapshot.macro_series}|"
            f"months={snapshot.macro_months}",
            "The aligned context fact must preserve five governed series over fifteen months.",
        )
    )
    controls.append(
        ReportingMartControl(
            "official_dbt_mart_build",
            snapshot.dbt_models_succeeded == 24
            and snapshot.dbt_seeds_succeeded == 2
            and snapshot.dbt_tests_passed == 188
            and snapshot.dbt_failures == 0
            and snapshot.dbt_total_results == 214,
            "models=24|seeds=2|tests=188|failures=0|total=214",
            f"models={snapshot.dbt_models_succeeded}|seeds={snapshot.dbt_seeds_succeeded}|"
            f"tests={snapshot.dbt_tests_passed}|failures={snapshot.dbt_failures}|"
            f"total={snapshot.dbt_total_results}",
            "The official dbt result must contain the complete expanded graph and test suite.",
        )
    )
    controls.append(
        ReportingMartControl(
            "mart_contract_matches_warehouse",
            snapshot.contract_name == "banking_reporting_marts"
            and snapshot.contract_version == MAPPING_VERSION
            and snapshot.contract_mapping_version == MAPPING_VERSION
            and snapshot.contract_object_count == 12
            and not snapshot.contract_schema_issues,
            f"banking_reporting_marts|{MAPPING_VERSION}|objects=12|schema_issues=0",
            f"{snapshot.contract_name}|{snapshot.contract_version}|objects="
            f"{snapshot.contract_object_count}|schema_issues="
            f"{len(snapshot.contract_schema_issues)}",
            "The versioned handoff contract must match every ordered warehouse column and type.",
        )
    )
    try:
        UUID(snapshot.dagster_run_id)
        valid_run_id = True
    except ValueError:
        valid_run_id = False
    controls.append(
        ReportingMartControl(
            "expanded_official_dagster_run",
            valid_run_id and snapshot.dagster_status == "success",
            "valid_uuid|success",
            f"{snapshot.dagster_run_id}|{snapshot.dagster_status}",
            "The expanded official Dagster graph must finish successfully with marts included.",
        )
    )
    ready = all(control.passed for control in controls)
    controls.append(
        ReportingMartControl(
            "reporting_marts_certified",
            ready,
            "certified",
            "certified" if ready else "blocked",
            "Certification freezes the data-to-BI boundary; Power BI remains downstream.",
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


def _read_dbt_results(path: Path) -> tuple[int, int, int, int, int]:
    if not path.is_file():
        raise ValueError(f"dbt run results are missing: {path}")
    results = json.loads(path.read_text(encoding="utf-8")).get("results", [])
    counts: Counter[tuple[str, str]] = Counter()
    failures = 0
    for result in results:
        unique_id = str(result.get("unique_id", ""))
        resource_type = unique_id.split(".", 1)[0]
        status = str(result.get("status", ""))
        counts[(resource_type, status)] += 1
        if status not in {"success", "pass"}:
            failures += 1
    return (
        counts[("model", "success")],
        counts[("seed", "success")],
        counts[("test", "pass")],
        failures,
        len(results),
    )


def _actual_type(
    data_type: str,
    character_length: int | None,
    numeric_precision: int | None,
    numeric_scale: int | None,
) -> str:
    if data_type == "character varying":
        return f"varchar_{character_length}"
    if data_type == "timestamp with time zone":
        return "timestamptz"
    if data_type == "numeric" and numeric_precision is not None:
        return f"numeric_{numeric_precision}_{numeric_scale}"
    return data_type


def _read_contract(
    path: Path,
) -> tuple[
    dict[str, object],
    dict[str, list[tuple[str, str]]],
    dict[str, tuple[str, ...]],
]:
    if not path.is_file():
        raise ValueError(f"Mart contract is missing: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("objects"), list):
        raise ValueError(f"Mart contract has an invalid structure: {path}")
    schemas: dict[str, list[tuple[str, str]]] = {}
    required_columns: dict[str, tuple[str, ...]] = {}
    for item in payload["objects"]:
        schemas[str(item["name"])] = [
            (str(column["name"]), str(column["type"])) for column in item["columns"]
        ]
        required_columns[str(item["name"])] = tuple(
            str(column["name"])
            for column in item["columns"]
            if not bool(column["nullable"])
        )
    return payload, schemas, required_columns


def collect_reporting_mart_snapshot(
    settings: WarehouseSettings,
    *,
    population_monthly: Path,
    dbt_run_results: Path,
    contract: Path,
    dagster_run_id: str,
    dagster_status: str,
) -> ReportingMartSnapshot:
    """Collect official reporting-mart certification facts from PostgreSQL and artifacts."""
    population = _read_population(population_monthly)
    contract_payload, contract_schemas, required_columns = _read_contract(contract)
    with psycopg.connect(settings.dsn) as connection, connection.cursor() as cursor:
        cursor.execute("select current_database()")
        database_name = str((cursor.fetchone() or ("",))[0])
        relation_counts: dict[str, int] = {}
        for relation in EXPECTED_MART_COUNTS:
            cursor.execute(
                sql.SQL("select count(*) from analytics_marts.{}").format(
                    sql.Identifier(relation)
                )
            )
            relation_counts[relation] = int((cursor.fetchone() or (0,))[0])

        cursor.execute(
            """
            select count(*), array_agg(distinct mapping_version order by mapping_version),
                   array_agg(distinct status order by status),
                   array_agg(account_code order by account_code)
            from analytics_core.reporting_line_mapping
            """
        )
        mapping = cursor.fetchone() or (0, [], [], [])
        cursor.execute(
            """
            select
              (select count(*) from analytics_marts.dim_bank where is_fixture)
              + (select count(*) from analytics_marts.dim_cosif_account where is_fixture)
              + (select count(*) from analytics_marts.dim_source_file where is_fixture)
              + (select count(*) from analytics_marts.fact_account_balance where is_fixture)
              + (select count(*) from analytics_marts.fact_reporting_line_balance where is_fixture)
              + (select count(*) from analytics_marts.fact_macro_observation where is_fixture)
              + (select count(*)
                 from analytics_marts.fact_monthly_economic_context where is_fixture)
            """
        )
        fixture_rows = int((cursor.fetchone() or (0,))[0])
        cursor.execute(
            """
            select
              (select count(*) from analytics_marts.dim_bank),
              (select count(distinct month_key) from analytics_marts.fact_reporting_line_balance),
              (select count(*) from analytics_marts.fact_reporting_line_balance
               where reporting_line_code = 'total_assets')
            """
        )
        population_counts = cursor.fetchone() or (0, 0, 0)
        cursor.execute(
            """
            select count(*), count(distinct reporting_line_code)
            from analytics_marts.fact_reporting_line_balance
            """
        )
        reporting_counts = cursor.fetchone() or (0, 0)
        cursor.execute(
            """
            with expected as (
                select fact.bank_key, fact.month_key, bridge.reporting_line_key,
                       sum(fact.balance_amount * bridge.presentation_multiplier) as amount
                from analytics_marts.fact_account_balance as fact
                inner join analytics_marts.bridge_account_reporting_line as bridge
                    on fact.account_key = bridge.account_key
                group by fact.bank_key, fact.month_key, bridge.reporting_line_key
            ), compared as (
                select coalesce(expected.bank_key, actual.bank_key) as bank_key,
                       coalesce(expected.month_key, actual.month_key) as month_key,
                       coalesce(expected.reporting_line_key, actual.reporting_line_key) as line_key,
                       abs(coalesce(expected.amount, 0) -
                           coalesce(actual.presentation_balance_amount, 0)) as difference
                from expected
                full join analytics_marts.fact_reporting_line_balance as actual
                    using (bank_key, month_key, reporting_line_key)
            )
            select count(*) filter (where difference > 0.01), coalesce(max(difference), 0)
            from compared
            """
        )
        reconciliation = cursor.fetchone() or (0, Decimal("0"))
        cursor.execute(
            """
            select to_char(report_month, 'YYYYMM'), institution_cnpj,
                   presentation_balance_amount
            from analytics_marts.fact_reporting_line_balance
            where reporting_line_code = 'total_assets'
            """
        )
        actual_assets = {
            (str(period), str(cnpj)): Decimal(amount)
            for period, cnpj, amount in cursor.fetchall()
        }
        cursor.execute(
            """
            select count(*), count(distinct series_code), count(distinct month_key)
            from analytics_marts.fact_monthly_economic_context
            """
        )
        macro = cursor.fetchone() or (0, 0, 0)
        cursor.execute(
            """
            select table_name, column_name, data_type, character_maximum_length,
                   numeric_precision, numeric_scale
            from information_schema.columns
            where table_schema = 'analytics_marts'
            order by table_name, ordinal_position
            """
        )
        actual_schemas: dict[str, list[tuple[str, str]]] = {}
        for table, column, data_type, char_length, precision, scale in cursor.fetchall():
            actual_schemas.setdefault(str(table), []).append(
                (
                    str(column),
                    _actual_type(str(data_type), char_length, precision, scale),
                )
            )
        null_issues: list[str] = []
        for table, columns in required_columns.items():
            for column in columns:
                cursor.execute(
                    sql.SQL("select count(*) from analytics_marts.{} where {} is null").format(
                        sql.Identifier(table), sql.Identifier(column)
                    )
                )
                null_count = int((cursor.fetchone() or (0,))[0])
                if null_count:
                    null_issues.append(f"{table}.{column}:nulls={null_count}")

    differences = [
        abs(actual_assets[key] - expected)
        for key, expected in population.items()
        if key in actual_assets
    ]
    schema_issues = tuple(
        name
        for name in sorted(set(contract_schemas) | set(actual_schemas))
        if contract_schemas.get(name) != actual_schemas.get(name)
    ) + tuple(null_issues)
    dbt_models, dbt_seeds, dbt_tests, dbt_failures, dbt_total = _read_dbt_results(
        dbt_run_results
    )
    return ReportingMartSnapshot(
        database_name=database_name,
        relation_counts=relation_counts,
        mapping_rows=int(mapping[0]),
        mapping_versions=tuple(str(value) for value in mapping[1]),
        mapping_statuses=tuple(str(value) for value in mapping[2]),
        mapping_accounts=frozenset(str(value) for value in mapping[3]),
        fixture_rows=fixture_rows,
        population_banks=int(population_counts[0]),
        population_months=int(population_counts[1]),
        total_asset_rows=int(population_counts[2]),
        reporting_rows=int(reporting_counts[0]),
        reporting_lines=int(reporting_counts[1]),
        reconciliation_mismatches=int(reconciliation[0]),
        reconciliation_max_difference_brl=Decimal(reconciliation[1]),
        top15_comparisons=len(differences),
        top15_max_difference_brl=max(differences) if differences else None,
        macro_rows=int(macro[0]),
        macro_series=int(macro[1]),
        macro_months=int(macro[2]),
        dbt_models_succeeded=dbt_models,
        dbt_seeds_succeeded=dbt_seeds,
        dbt_tests_passed=dbt_tests,
        dbt_failures=dbt_failures,
        dbt_total_results=dbt_total,
        contract_name=str(contract_payload.get("contract_name", "")),
        contract_version=str(contract_payload.get("contract_version", "")),
        contract_mapping_version=str(contract_payload.get("mapping_version", "")),
        contract_object_count=len(contract_schemas),
        contract_schema_issues=schema_issues,
        dagster_run_id=dagster_run_id,
        dagster_status=dagster_status,
    )


def write_reporting_mart_certification(
    controls: tuple[ReportingMartControl, ...], output: Path
) -> int:
    """Write reporting-mart certification controls to CSV."""
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = [control.as_dict() for control in controls]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)
