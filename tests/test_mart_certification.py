import csv
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import yaml

from banking_analytics.mart_certification import (
    EXPECTED_MAPPING_ACCOUNTS,
    EXPECTED_MART_COUNTS,
    MAPPING_VERSION,
    ReportingMartSnapshot,
    assess_reporting_mart_snapshot,
)


def _passing_snapshot() -> ReportingMartSnapshot:
    return ReportingMartSnapshot(
        database_name="banking_official_202501_202603",
        relation_counts=dict(EXPECTED_MART_COUNTS),
        mapping_rows=7,
        mapping_versions=(MAPPING_VERSION,),
        mapping_statuses=("certified",),
        mapping_accounts=frozenset(EXPECTED_MAPPING_ACCOUNTS),
        fixture_rows=0,
        population_banks=15,
        population_months=15,
        total_asset_rows=225,
        reporting_rows=900,
        reporting_lines=4,
        reconciliation_mismatches=0,
        reconciliation_max_difference_brl=Decimal("0.00"),
        top15_comparisons=225,
        top15_max_difference_brl=Decimal("0.00"),
        macro_rows=75,
        macro_series=5,
        macro_months=15,
        dbt_models_succeeded=24,
        dbt_seeds_succeeded=2,
        dbt_tests_passed=188,
        dbt_failures=0,
        dbt_total_results=214,
        contract_name="banking_reporting_marts",
        contract_version=MAPPING_VERSION,
        contract_mapping_version=MAPPING_VERSION,
        contract_object_count=12,
        contract_schema_issues=(),
        dagster_run_id="69dd1ce1-74e9-4ebb-85b5-af7c3fa155c0",
        dagster_status="success",
    )


def test_reporting_mart_certification_accepts_complete_snapshot() -> None:
    controls = assess_reporting_mart_snapshot(
        _passing_snapshot(), expected_database="banking_official_202501_202603"
    )

    assert len(controls) == 13
    assert all(control.passed for control in controls)
    assert controls[-1].actual_value == "certified"


def test_reporting_mart_certification_fails_closed_on_mapping_drift() -> None:
    snapshot = replace(
        _passing_snapshot(), mapping_accounts=frozenset({"1000000009"})
    )

    controls = assess_reporting_mart_snapshot(
        snapshot, expected_database="banking_official_202501_202603"
    )

    by_name = {control.control_name: control for control in controls}
    assert not by_name["reporting_line_mapping_frozen"].passed
    assert not controls[-1].passed


def test_reporting_mart_certification_fails_closed_on_contract_drift() -> None:
    snapshot = replace(_passing_snapshot(), contract_schema_issues=("dim_bank",))

    controls = assess_reporting_mart_snapshot(
        snapshot, expected_database="banking_official_202501_202603"
    )

    by_name = {control.control_name: control for control in controls}
    assert not by_name["mart_contract_matches_warehouse"].passed
    assert not controls[-1].passed


def test_frozen_contract_covers_every_mart_model() -> None:
    contract = yaml.safe_load(Path("contracts/mart-schema.yml").read_text(encoding="utf-8"))
    object_names = {item["name"] for item in contract["objects"]}
    mart_models = {path.stem for path in Path("dbt/models/marts").glob("*.sql")}

    assert contract["contract_version"] == MAPPING_VERSION
    assert contract["mapping_version"] == MAPPING_VERSION
    assert object_names == mart_models
    assert all(item["columns"] for item in contract["objects"])


def test_retained_reporting_mart_certification_is_green() -> None:
    with Path("artifacts/reporting_mart_certification.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 13
    assert all(row["passed"] == "True" for row in rows)
    assert rows[-1]["control_name"] == "reporting_marts_certified"
    assert rows[-1]["actual_value"] == "certified"
