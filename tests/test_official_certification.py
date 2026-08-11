from dataclasses import replace
from decimal import Decimal

from banking_analytics.official_certification import (
    EXPECTED_RELATION_COUNTS,
    OfficialWarehouseSnapshot,
    assess_official_snapshot,
)


def _passing_snapshot() -> OfficialWarehouseSnapshot:
    return OfficialWarehouseSnapshot(
        database_name="banking_official_202501_202603",
        relation_counts=dict(EXPECTED_RELATION_COUNTS),
        cosif_start_period="202501",
        cosif_end_period="202603",
        cosif_periods=15,
        cosif_checksums=15,
        cosif_raw_rows=831_038,
        cosif_declared_rows=831_038,
        macro_start_period="202501",
        macro_end_period="202603",
        macro_rows=75,
        macro_series=5,
        macro_fetches=5,
        macro_responses=75,
        raw_fixture_rows=0,
        core_fixture_rows=0,
        cosif_successful_loads=2,
        macro_successful_loads=2,
        failed_loads=0,
        top15_comparisons=225,
        top15_max_difference_brl=Decimal("0.00"),
        dbt_models_succeeded=11,
        dbt_tests_passed=106,
        dbt_failures=0,
        dbt_total_results=117,
        dagster_run_id="69dd1ce1-74e9-4ebb-85b5-af7c3fa155c0",
        dagster_status="success",
    )


def test_official_certification_accepts_complete_official_snapshot() -> None:
    controls = assess_official_snapshot(
        _passing_snapshot(), expected_database="banking_official_202501_202603"
    )

    assert len(controls) == 11
    assert all(control.passed for control in controls)
    assert controls[-1].actual_value == "certified"


def test_official_certification_fails_closed_on_fixture_contamination() -> None:
    snapshot = replace(_passing_snapshot(), core_fixture_rows=1)

    controls = assess_official_snapshot(
        snapshot, expected_database="banking_official_202501_202603"
    )

    by_name = {control.control_name: control for control in controls}
    assert not by_name["official_rows_are_fixture_free"].passed
    assert not controls[-1].passed
