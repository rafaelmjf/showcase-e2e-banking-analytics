from __future__ import annotations

import csv
from pathlib import Path

from banking_analytics.source_decision import (
    assess_source_profile_rows,
    write_source_profile_decision,
)


def _periods() -> list[str]:
    return [f"2025{month:02d}" for month in range(1, 13)] + [
        f"2026{month:02d}" for month in range(1, 4)
    ]


def _passing_rows() -> dict[str, list[dict[str, object]]]:
    periods = _periods()
    cnpjs = [f"{rank:08d}" for rank in range(1, 16)]
    macro_codes = ["4189", "433", "24363", "20539", "21082"]
    reporting_lines = [
        {
            "reporting_line": "total_assets",
            "status": "certified",
            "document_code": "4010",
            "account_codes": "1000000009|2000000008",
            "presentation_sign": "positive",
            "top15_period_coverage": "225/225",
            "decision": "approved",
            "rationale": "certified",
        },
        {
            "reporting_line": "credit_portfolio",
            "status": "draft",
            "document_code": "4010",
            "account_codes": "1600000007|1700000000|1810000000",
            "presentation_sign": "positive",
            "top15_period_coverage": "160=225/225|170=67/225|181=210/225",
            "decision": "requires_mapping_review",
            "rationale": "bounded",
        },
        {
            "reporting_line": "deposits",
            "status": "draft",
            "document_code": "4010",
            "account_codes": "4100000009",
            "presentation_sign": "positive",
            "top15_period_coverage": "225/225",
            "decision": "requires_mapping_reconciliation",
            "rationale": "bounded",
        },
        {
            "reporting_line": "equity",
            "status": "draft",
            "document_code": "4010",
            "account_codes": "6000000004",
            "presentation_sign": "positive",
            "top15_period_coverage": "225/225",
            "decision": "requires_mapping_reconciliation",
            "rationale": "bounded",
        },
    ]
    readiness = [
        {"control_name": f"control_{index}", "status": "pass", "actual_value": "ok"}
        for index in range(8)
    ]
    readiness.append(
        {
            "control_name": "bounded_official_load_ready",
            "status": "pass",
            "actual_value": "ready",
        }
    )
    population_controls = [
        {"control_name": f"control_{index}", "passed": "True", "actual_value": "ok"}
        for index in range(10)
    ]
    population_controls.append(
        {
            "control_name": "checkpoint_0c_ready",
            "passed": "True",
            "actual_value": "ready",
        }
    )
    return {
        "catalog_rows": [{"period": period, "is_active": "True"} for period in periods],
        "manifest_rows": [
            {
                "period": period,
                "status": "complete",
                "sha256": f"sha-{period}",
                "archive_path": f"archive-{period}.zip",
                "error": "",
            }
            for period in periods
        ],
        "cosif_profile_rows": [
            {
                "period": period,
                "row_count": "1",
                "malformed_row_count": "0",
                "period_matches": "True",
                "sha256": f"sha-{period}",
            }
            for period in periods
        ],
        "macro_observation_rows": [
            {"series_code": code, "report_month": period}
            for code in macro_codes
            for period in periods
        ],
        "macro_profile_rows": [
            {
                "series_code": code,
                "status": "complete",
                "requested_start_month": "202501",
                "requested_end_month": "202603",
                "row_count": "15",
                "internal_missing_month_count": "0",
                "duplicate_report_month_count": "0",
                "error": "",
            }
            for code in macro_codes
        ],
        "readiness_rows": readiness,
        "population_control_rows": population_controls,
        "population_rows": [
            {
                "freeze_period": "202603",
                "freeze_rank": str(rank),
                "document_code": "4010",
                "institution_cnpj": cnpj,
            }
            for rank, cnpj in enumerate(cnpjs, start=1)
        ],
        "population_monthly_rows": [
            {
                "report_period": period,
                "institution_cnpj": cnpj,
                "document_code": "4010",
            }
            for period in periods
            for cnpj in cnpjs
        ],
        "period_profile_rows": [
            {
                "period": period,
                "document_4010_institutions": "1",
                "document_4016_institutions": "1" if period in {"202506", "202512"} else "0",
                "reference_outliers": "0",
            }
            for period in periods
        ],
        "reporting_line_rows": reporting_lines,
    }


def test_source_profile_decision_passes_complete_bounded_evidence() -> None:
    decision = assess_source_profile_rows(**_passing_rows())

    assert decision.passed
    assert len(decision.controls) == 11
    assert decision.controls[-1].actual_value == ("ready_for_official_warehouse_certification")
    contract = {row.contract_key: row.contract_value for row in decision.contract}
    assert contract["warehouse_status"] == "not_certified"
    assert contract["mart_status"] == "not_built"


def test_source_profile_decision_fails_closed_when_draft_is_misrepresented() -> None:
    rows = _passing_rows()
    rows["reporting_line_rows"][1]["status"] = "certified"

    decision = assess_source_profile_rows(**rows)

    assert not decision.passed
    controls = {row.control_name: row for row in decision.controls}
    assert not controls["reporting_line_draft_bounded"].passed
    assert controls["checkpoint_0e_ready"].actual_value == "blocked"


def test_source_profile_decision_writer_publishes_both_files(tmp_path: Path) -> None:
    decision = assess_source_profile_rows(**_passing_rows())

    counts = write_source_profile_decision(decision, tmp_path)

    assert counts == {"controls": 11, "contract": 16}
    with (tmp_path / "checkpoint_0e_controls.csv").open(encoding="utf-8") as handle:
        controls = list(csv.DictReader(handle))
    with (tmp_path / "source_profile_contract.csv").open(encoding="utf-8") as handle:
        contract = list(csv.DictReader(handle))
    assert controls[-1]["passed"] == "True"
    assert contract[-2]["contract_value"] == "not_certified"
