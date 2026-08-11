import csv
from pathlib import Path

PROFILE_PATH = Path("artifacts/cosif_source_profile.csv")
MACRO_PROFILE_PATH = Path("artifacts/macro_source_profile.csv")
READINESS_PATH = Path("artifacts/live_readiness_full_202501_202603.csv")
POPULATION_PATH = Path("artifacts/top15_population.csv")
POPULATION_MONTHLY_PATH = Path("artifacts/top15_total_assets_by_month.csv")
POPULATION_CONTROLS_PATH = Path("artifacts/checkpoint_0c_controls.csv")
SOURCE_DECISION_CONTROLS_PATH = Path("artifacts/checkpoint_0e_controls.csv")
SOURCE_CONTRACT_PATH = Path("artifacts/source_profile_contract.csv")
OFFICIAL_CERTIFICATION_PATH = Path("artifacts/official_warehouse_certification.csv")
EXPECTED_PERIODS = [
    f"{year}{month:02d}"
    for year, months in ((2025, range(1, 13)), (2026, range(1, 4)))
    for month in months
]
EXPECTED_COLUMNS = (
    "DATA_BASE|DOCUMENTO|CNPJ|AGENCIA|NOME_INSTITUICAO|COD_CONGL|"
    "NOME_CONGL|TAXONOMIA|CONTA|NOME_CONTA|SALDO"
)
EXPECTED_TOP15_CNPJS = [
    "00000000",
    "00360305",
    "60701190",
    "60746948",
    "90400888",
    "33657248",
    "30306294",
    "60872504",
    "58160789",
    "01181521",
    "33264668",
    "02038232",
    "33479023",
    "92702067",
    "59588111",
]


def test_committed_cosif_profile_satisfies_checkpoint_0b_exit_gate() -> None:
    with PROFILE_PATH.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert [row["period"] for row in rows] == EXPECTED_PERIODS
    assert all(row["sha256"] and len(row["sha256"]) == 64 for row in rows)
    assert all(int(row["compressed_bytes"]) > 0 for row in rows)
    assert all(int(row["row_count"]) > 0 for row in rows)
    assert sum(int(row["row_count"]) for row in rows) == 831_038
    assert all(int(row["malformed_row_count"]) == 0 for row in rows)
    assert all(row["columns"] == EXPECTED_COLUMNS for row in rows)
    assert all(row["encoding"] == "cp1252" for row in rows)
    assert all(row["delimiter"] == ";" for row in rows)
    assert all(row["header_line_number"] == "4" for row in rows)
    assert all(row["declared_periods"] == row["period"] for row in rows)
    assert all(row["period_matches"] == "True" for row in rows)


def test_semester_end_files_preserve_both_document_types() -> None:
    with PROFILE_PATH.open(encoding="utf-8", newline="") as handle:
        by_period = {row["period"]: row for row in csv.DictReader(handle)}

    assert by_period["202506"]["document_count"] == "2"
    assert by_period["202512"]["document_count"] == "2"
    assert by_period["202512"]["source_url"].endswith("202512BANCOS.zip.csv.zip")


def test_full_window_source_evidence_is_ready() -> None:
    with MACRO_PROFILE_PATH.open(encoding="utf-8", newline="") as handle:
        macro_rows = list(csv.DictReader(handle))
    with READINESS_PATH.open(encoding="utf-8", newline="") as handle:
        readiness_rows = list(csv.DictReader(handle))

    assert {row["series_code"] for row in macro_rows} == {
        "4189",
        "433",
        "24363",
        "20539",
        "21082",
    }
    assert all(row["status"] == "complete" for row in macro_rows)
    assert all(row["row_count"] == "15" for row in macro_rows)
    assert all(row["internal_missing_month_count"] == "0" for row in macro_rows)
    assert len(readiness_rows) == 9
    assert all(row["status"] == "pass" for row in readiness_rows)
    assert readiness_rows[-1]["actual_value"] == "ready"


def test_committed_checkpoint_0c_evidence_freezes_the_certified_population() -> None:
    with POPULATION_PATH.open(encoding="utf-8", newline="") as handle:
        population = list(csv.DictReader(handle))
    with POPULATION_MONTHLY_PATH.open(encoding="utf-8", newline="") as handle:
        monthly = list(csv.DictReader(handle))
    with POPULATION_CONTROLS_PATH.open(encoding="utf-8", newline="") as handle:
        controls = list(csv.DictReader(handle))

    assert [row["institution_cnpj"] for row in population] == EXPECTED_TOP15_CNPJS
    assert [int(row["freeze_rank"]) for row in population] == list(range(1, 16))
    assert all(row["freeze_period"] == "202603" for row in population)
    assert all(row["document_code"] == "4010" for row in population)
    assert all(row["periods_present"] == "15" for row in population)
    assert all(row["component_complete_periods"] == "15" for row in population)
    assert len(monthly) == 225
    assert {row["report_period"] for row in monthly} == set(EXPECTED_PERIODS)
    assert all(row["document_code"] == "4010" for row in monthly)
    assert len(controls) == 11
    assert all(row["passed"] == "True" for row in controls)
    assert controls[-1]["actual_value"] == "ready"


def test_committed_checkpoint_0e_evidence_freezes_the_source_boundary() -> None:
    with SOURCE_DECISION_CONTROLS_PATH.open(encoding="utf-8", newline="") as handle:
        controls = list(csv.DictReader(handle))
    with SOURCE_CONTRACT_PATH.open(encoding="utf-8", newline="") as handle:
        contract_rows = list(csv.DictReader(handle))

    assert len(controls) == 11
    assert all(row["passed"] == "True" for row in controls)
    assert controls[-1]["control_name"] == "checkpoint_0e_ready"
    assert controls[-1]["actual_value"] == ("ready_for_official_warehouse_certification")
    contract = {row["contract_key"]: row for row in contract_rows}
    assert contract["analytical_document"]["contract_value"] == "4010"
    assert contract["total_assets_formula"]["status"] == "certified"
    assert contract["reporting_lines"]["status"] == "bounded"
    assert contract["warehouse_status"]["contract_value"] == "not_certified"
    assert contract["mart_status"]["contract_value"] == "not_built"


def test_committed_official_warehouse_certification_is_complete() -> None:
    with OFFICIAL_CERTIFICATION_PATH.open(encoding="utf-8", newline="") as handle:
        controls = list(csv.DictReader(handle))

    assert len(controls) == 11
    assert all(row["passed"] == "True" for row in controls)
    assert controls[-1]["control_name"] == "official_warehouse_certified"
    assert controls[-1]["actual_value"] == "certified"
    by_name = {row["control_name"]: row for row in controls}
    assert by_name["official_top15_total_assets_reconciliation"]["actual_value"] == (
        "225/225|max_difference_brl=0.00"
    )
    assert "69dd1ce1-74e9-4ebb-85b5-af7c3fa155c0" in by_name["official_dagster_run"]["actual_value"]
