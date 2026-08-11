"""Publish the fail-closed checkpoint 0E source-profile decision."""

from __future__ import annotations

import csv
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path

EXPECTED_MACRO_CODES = frozenset({"4189", "433", "24363", "20539", "21082"})
EXPECTED_REPORTING_LINES = {
    "total_assets": ("certified", "1000000009|2000000008", "225/225", "approved"),
    "credit_portfolio": (
        "draft",
        "1600000007|1700000000|1810000000",
        "160=225/225|170=67/225|181=210/225",
        "requires_mapping_review",
    ),
    "deposits": (
        "draft",
        "4100000009",
        "225/225",
        "requires_mapping_reconciliation",
    ),
    "equity": (
        "draft",
        "6000000004",
        "225/225",
        "requires_mapping_reconciliation",
    ),
}


@dataclass(frozen=True)
class SourceDecisionControl:
    """One machine-readable checkpoint 0E gate control."""

    control_name: str
    passed: bool
    expected_value: str
    actual_value: str
    detail: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SourceContractRecord:
    """One frozen or explicitly provisional source-profile decision."""

    contract_key: str
    contract_value: str
    status: str
    detail: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SourceProfileDecision:
    """Checkpoint 0E controls and the exact official-load boundary."""

    controls: tuple[SourceDecisionControl, ...]
    contract: tuple[SourceContractRecord, ...]

    @property
    def passed(self) -> bool:
        return bool(self.controls) and self.controls[-1].passed


def _expected_periods(start_period: str, end_period: str) -> list[str]:
    if len(start_period) != 6 or len(end_period) != 6:
        raise ValueError("Source periods must use YYYYMM")
    year, month = int(start_period[:4]), int(start_period[4:])
    end_year, end_month = int(end_period[:4]), int(end_period[4:])
    if not 1 <= month <= 12 or not 1 <= end_month <= 12:
        raise ValueError("Source periods must contain valid months")
    periods: list[str] = []
    while (year, month) <= (end_year, end_month):
        periods.append(f"{year:04d}{month:02d}")
        month += 1
        if month == 13:
            year += 1
            month = 1
    if not periods:
        raise ValueError("Source start period must not follow end period")
    return periods


def _is_true(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "pass", "ready"}


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise ValueError(f"Required checkpoint evidence is missing: {path}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def assess_source_profile_rows(
    *,
    catalog_rows: Iterable[Mapping[str, object]],
    manifest_rows: Iterable[Mapping[str, object]],
    cosif_profile_rows: Iterable[Mapping[str, object]],
    macro_observation_rows: Iterable[Mapping[str, object]],
    macro_profile_rows: Iterable[Mapping[str, object]],
    readiness_rows: Iterable[Mapping[str, object]],
    population_control_rows: Iterable[Mapping[str, object]],
    population_rows: Iterable[Mapping[str, object]],
    population_monthly_rows: Iterable[Mapping[str, object]],
    period_profile_rows: Iterable[Mapping[str, object]],
    reporting_line_rows: Iterable[Mapping[str, object]],
    start_period: str = "202501",
    end_period: str = "202603",
    freeze_period: str = "202603",
    population_size: int = 15,
    require_archive_files: bool = False,
) -> SourceProfileDecision:
    """Combine retained 0A-0D evidence into the final fail-closed decision."""
    periods = _expected_periods(start_period, end_period)
    period_set = set(periods)
    expected_period_text = "|".join(periods)
    controls: list[SourceDecisionControl] = []

    catalog = list(catalog_rows)
    active_catalog_periods = sorted(
        str(row.get("period", ""))
        for row in catalog
        if str(row.get("period", "")) in period_set and _is_true(row.get("is_active"))
    )
    controls.append(
        SourceDecisionControl(
            "catalog_active_period_coverage",
            active_catalog_periods == periods,
            expected_period_text,
            "|".join(active_catalog_periods),
            "Exactly one active official BANCOS catalog record is required per month.",
        )
    )

    manifest = list(manifest_rows)
    manifest_periods = sorted(str(row.get("period", "")) for row in manifest)
    complete_archives = sum(
        str(row.get("status", "")) == "complete"
        and bool(str(row.get("sha256", "")).strip())
        and bool(str(row.get("archive_path", "")).strip())
        and (not require_archive_files or Path(str(row.get("archive_path", ""))).is_file())
        and not str(row.get("error", "")).strip()
        for row in manifest
    )
    cosif_profile = list(cosif_profile_rows)
    profile_periods = sorted(str(row.get("period", "")) for row in cosif_profile)
    valid_profiles = sum(
        int(str(row.get("row_count", "0"))) > 0
        and int(str(row.get("malformed_row_count", "0"))) == 0
        and _is_true(row.get("period_matches"))
        and bool(str(row.get("sha256", "")).strip())
        for row in cosif_profile
    )
    cosif_ready = (
        manifest_periods == periods
        and complete_archives == len(periods)
        and profile_periods == periods
        and valid_profiles == len(periods)
    )
    controls.append(
        SourceDecisionControl(
            "cosif_runtime_and_profile_ready",
            cosif_ready,
            f"{len(periods)} complete archives and valid profiles",
            f"archives={complete_archives};profiles={valid_profiles}",
            "Every selected archive needs a checksum, retained path and clean matching profile.",
        )
    )

    macro_profiles = list(macro_profile_rows)
    macro_codes = {str(row.get("series_code", "")) for row in macro_profiles}
    valid_macro_profiles = sum(
        str(row.get("status", "")) == "complete"
        and str(row.get("requested_start_month", "")) == start_period
        and str(row.get("requested_end_month", "")) == end_period
        and int(str(row.get("row_count", "0"))) == len(periods)
        and int(str(row.get("internal_missing_month_count", "0"))) == 0
        and int(str(row.get("duplicate_report_month_count", "0"))) == 0
        and not str(row.get("error", "")).strip()
        for row in macro_profiles
    )
    macro_observations = list(macro_observation_rows)
    observation_keys = {
        (str(row.get("series_code", "")), str(row.get("report_month", "")))
        for row in macro_observations
    }
    expected_observation_keys = {
        (series_code, period) for series_code in EXPECTED_MACRO_CODES for period in periods
    }
    macro_ready = (
        macro_codes == EXPECTED_MACRO_CODES
        and valid_macro_profiles == len(EXPECTED_MACRO_CODES)
        and observation_keys == expected_observation_keys
        and len(macro_observations) == len(expected_observation_keys)
    )
    controls.append(
        SourceDecisionControl(
            "macro_runtime_and_profile_ready",
            macro_ready,
            f"{len(EXPECTED_MACRO_CODES)} series and {len(expected_observation_keys)} observations",
            f"profiles={valid_macro_profiles};observations={len(observation_keys)}",
            "All five official SGS series must cover the exact bounded monthly window.",
        )
    )

    readiness = list(readiness_rows)
    readiness_last = str(readiness[-1].get("actual_value", "")) if readiness else "missing"
    readiness_ready = (
        len(readiness) == 9
        and all(str(row.get("status", "")).lower() == "pass" for row in readiness)
        and str(readiness[-1].get("control_name", "")) == "bounded_official_load_ready"
        and str(readiness[-1].get("actual_value", "")) == "ready"
    )
    controls.append(
        SourceDecisionControl(
            "acquisition_readiness_retained",
            readiness_ready,
            "9/9 controls pass; bounded_official_load_ready=ready",
            f"rows={len(readiness)};last={readiness_last}",
            "The independent acquisition gate must remain fully ready.",
        )
    )

    population_controls = list(population_control_rows)
    population_controls_last = (
        str(population_controls[-1].get("actual_value", "")) if population_controls else "missing"
    )
    population_controls_ready = (
        len(population_controls) == 11
        and all(_is_true(row.get("passed")) for row in population_controls)
        and str(population_controls[-1].get("control_name", "")) == "checkpoint_0c_ready"
        and str(population_controls[-1].get("actual_value", "")) == "ready"
    )
    controls.append(
        SourceDecisionControl(
            "population_controls_retained",
            population_controls_ready,
            "11/11 controls pass; checkpoint_0c_ready=ready",
            f"rows={len(population_controls)};last={population_controls_last}",
            "The certified total-assets and population controls must remain fully ready.",
        )
    )

    population = list(population_rows)
    population_cnpjs = {str(row.get("institution_cnpj", "")) for row in population}
    ranks = {int(str(row.get("freeze_rank", "0"))) for row in population}
    population_ready = (
        len(population) == population_size
        and len(population_cnpjs) == population_size
        and ranks == set(range(1, population_size + 1))
        and all(str(row.get("freeze_period", "")) == freeze_period for row in population)
        and all(str(row.get("document_code", "")) == "4010" for row in population)
    )
    controls.append(
        SourceDecisionControl(
            "population_contract_frozen",
            population_ready,
            f"{population_size} unique 4010 members ranked at {freeze_period}",
            f"rows={len(population)};cnpjs={len(population_cnpjs)};ranks={len(ranks)}",
            "Membership is a fixed CNPJ set, not a rolling monthly top-N.",
        )
    )

    monthly = list(population_monthly_rows)
    monthly_keys = {
        (str(row.get("report_period", "")), str(row.get("institution_cnpj", ""))) for row in monthly
    }
    expected_monthly_keys = {(period, cnpj) for period in periods for cnpj in population_cnpjs}
    monthly_ready = (
        population_ready
        and len(monthly) == len(periods) * population_size
        and monthly_keys == expected_monthly_keys
        and all(str(row.get("document_code", "")) == "4010" for row in monthly)
    )
    controls.append(
        SourceDecisionControl(
            "population_monthly_coverage",
            monthly_ready,
            str(len(periods) * population_size),
            str(len(monthly_keys)),
            "Every frozen member requires one certified monthly total-assets row.",
        )
    )

    period_profiles = list(period_profile_rows)
    period_profile_periods = {str(row.get("period", "")) for row in period_profiles}
    semester_periods = {
        str(row.get("period", ""))
        for row in period_profiles
        if int(str(row.get("document_4016_institutions", "0"))) > 0
    }
    expected_semester_periods = {period for period in periods if period[4:] in {"06", "12"}}
    period_scope_ready = (
        len(period_profiles) == len(periods)
        and period_profile_periods == period_set
        and semester_periods == expected_semester_periods
        and all(int(str(row.get("document_4010_institutions", "0"))) > 0 for row in period_profiles)
        and all("reference_outliers" in row for row in period_profiles)
    )
    controls.append(
        SourceDecisionControl(
            "document_scope_disclosed",
            period_scope_ready,
            f"4010 monthly;4016={'|'.join(sorted(expected_semester_periods))}",
            f"profiles={len(period_profiles)};4016={'|'.join(sorted(semester_periods))}",
            "4016 is observed only as semiannual scope evidence and is excluded analytically.",
        )
    )

    reporting_lines = list(reporting_line_rows)
    reporting_by_name = {str(row.get("reporting_line", "")): row for row in reporting_lines}
    reporting_ready = len(reporting_lines) == len(EXPECTED_REPORTING_LINES)
    for name, (status, account_codes, coverage, decision) in EXPECTED_REPORTING_LINES.items():
        row = reporting_by_name.get(name, {})
        reporting_ready = reporting_ready and (
            str(row.get("status", "")) == status
            and str(row.get("document_code", "")) == "4010"
            and str(row.get("account_codes", "")) == account_codes
            and str(row.get("presentation_sign", "")) == "positive"
            and str(row.get("top15_period_coverage", "")) == coverage
            and str(row.get("decision", "")) == decision
            and bool(str(row.get("rationale", "")).strip())
        )
    controls.append(
        SourceDecisionControl(
            "reporting_line_draft_bounded",
            reporting_ready,
            "total_assets=certified;credit_portfolio|deposits|equity=draft",
            "|".join(
                f"{name}={reporting_by_name.get(name, {}).get('status', 'missing')}"
                for name in EXPECTED_REPORTING_LINES
            ),
            "Unresolved reporting lines stay explicit and cannot masquerade as certified mappings.",
        )
    )

    source_boundary_ready = (
        freeze_period == end_period
        and population_size == 15
        and start_period == "202501"
        and end_period == "202603"
    )
    controls.append(
        SourceDecisionControl(
            "source_boundary_complete",
            source_boundary_ready,
            "BANCOS|base_individual|202501-202603|freeze=202603|top=15|ODbL",
            f"BANCOS|base_individual|{start_period}-{end_period}|freeze={freeze_period}|top={population_size}|ODbL",
            "The bounded MVP source decision is intentionally exact and versionable.",
        )
    )

    overall_ready = all(control.passed for control in controls)
    controls.append(
        SourceDecisionControl(
            "checkpoint_0e_ready",
            overall_ready,
            "ready_for_official_warehouse_certification",
            "ready_for_official_warehouse_certification" if overall_ready else "blocked",
            "This authorizes the next certification run; it does not claim that the "
            "warehouse or marts are certified.",
        )
    )

    contract = (
        SourceContractRecord(
            "source_period_start", start_period, "frozen", "First MVP source month."
        ),
        SourceContractRecord("source_period_end", end_period, "frozen", "Last MVP source month."),
        SourceContractRecord(
            "cosif_segment", "BANCOS", "frozen", "Official BCB bank archive segment."
        ),
        SourceContractRecord(
            "source_scope", "base_individual", "frozen", "Individual institution CNPJ grain."
        ),
        SourceContractRecord(
            "landing_documents", "4010|4016", "frozen", "Preserve both source documents at landing."
        ),
        SourceContractRecord(
            "analytical_document", "4010", "frozen", "Monthly ranking and trend document."
        ),
        SourceContractRecord(
            "total_assets_formula",
            "1000000009 + 2000000008",
            "certified",
            "Class 3 compensation balances are excluded.",
        ),
        SourceContractRecord(
            "population_freeze_period", freeze_period, "frozen", "Latest complete source month."
        ),
        SourceContractRecord(
            "population_size", str(population_size), "frozen", "Stable comparison set."
        ),
        SourceContractRecord(
            "macro_codes",
            "4189|433|24363|20539|21082",
            "frozen",
            "Five official monthly SGS series.",
        ),
        SourceContractRecord(
            "macro_window", f"{start_period}|{end_period}", "frozen", "Exact monthly macro window."
        ),
        SourceContractRecord(
            "reporting_lines",
            "total_assets=certified|credit_portfolio=draft|deposits=draft|equity=draft",
            "bounded",
            "Draft lines require Phase 1 reconciliation before mart certification.",
        ),
        SourceContractRecord("license", "ODbL", "frozen", "Official BCB data reuse boundary."),
        SourceContractRecord(
            "implementation_decision",
            "ready_for_official_warehouse_certification" if overall_ready else "blocked",
            "decision",
            "Checkpoint 0E outcome.",
        ),
        SourceContractRecord(
            "warehouse_status",
            "not_certified",
            "pending",
            "No official PostgreSQL mutation is performed by checkpoint 0E.",
        ),
        SourceContractRecord(
            "mart_status", "not_built", "pending", "Reporting-line marts remain Phase 1 work."
        ),
    )
    return SourceProfileDecision(tuple(controls), contract)


def assess_source_profile_files(
    *,
    catalog: Path,
    cosif_manifest: Path,
    cosif_profile: Path,
    macro_observations: Path,
    macro_profile: Path,
    readiness: Path,
    population_controls: Path,
    population: Path,
    population_monthly: Path,
    period_profile: Path,
    reporting_line_draft: Path,
    start_period: str = "202501",
    end_period: str = "202603",
    freeze_period: str = "202603",
    population_size: int = 15,
) -> SourceProfileDecision:
    """Read retained CSV evidence and assess the final source-profile decision."""
    return assess_source_profile_rows(
        catalog_rows=_read_rows(catalog),
        manifest_rows=_read_rows(cosif_manifest),
        cosif_profile_rows=_read_rows(cosif_profile),
        macro_observation_rows=_read_rows(macro_observations),
        macro_profile_rows=_read_rows(macro_profile),
        readiness_rows=_read_rows(readiness),
        population_control_rows=_read_rows(population_controls),
        population_rows=_read_rows(population),
        population_monthly_rows=_read_rows(population_monthly),
        period_profile_rows=_read_rows(period_profile),
        reporting_line_rows=_read_rows(reporting_line_draft),
        start_period=start_period,
        end_period=end_period,
        freeze_period=freeze_period,
        population_size=population_size,
        require_archive_files=True,
    )


def write_source_profile_decision(
    decision: SourceProfileDecision, output_dir: Path
) -> dict[str, int]:
    """Write checkpoint controls and the frozen source contract."""
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "controls": ("checkpoint_0e_controls.csv", decision.controls),
        "contract": ("source_profile_contract.csv", decision.contract),
    }
    counts: dict[str, int] = {}
    for key, (filename, records) in outputs.items():
        path = output_dir / filename
        rows = [record.as_dict() for record in records]
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        counts[key] = len(rows)
    return counts
