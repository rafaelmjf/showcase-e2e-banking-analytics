"""Certify the COSIF total-assets mapping and stable comparison population."""

from __future__ import annotations

import csv
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from decimal import Decimal
from pathlib import Path

from banking_analytics.sources.cosif import (
    DownloadRecord,
    ProfileRecord,
    build_cosif_landing_records,
)

RANKING_DOCUMENT = "4010"
SEMESTER_END_DOCUMENT = "4016"
REALIZABLE_ASSETS_ACCOUNT = "1000000009"
PERMANENT_ASSETS_ACCOUNT = "2000000008"
ACTIVE_COMPENSATION_ACCOUNT = "3000000007"
TOTAL_GENERAL_ASSETS_ACCOUNT = "3999999009"
EXPECTED_ACCOUNT_NAMES = {
    REALIZABLE_ASSETS_ACCOUNT: "Ativo Realizável",
    PERMANENT_ASSETS_ACCOUNT: "Ativo Permanente",
    ACTIVE_COMPENSATION_ACCOUNT: "Compensação Ativa",
    TOTAL_GENERAL_ASSETS_ACCOUNT: "TOTAL GERAL DO ATIVO",
}
ASSET_ACCOUNTS = frozenset(EXPECTED_ACCOUNT_NAMES)


@dataclass(frozen=True)
class TotalAssetsPeriodProfile:
    """Coverage and reference-reconciliation evidence for one source period."""

    period: str
    source_checksum: str
    document_4010_institutions: int
    document_4016_institutions: int
    realizable_assets_present: int
    permanent_assets_present: int
    reference_total_present: int
    reference_reconciled: int
    reference_outliers: int
    max_abs_reference_difference_brl: Decimal | None
    summed_total_assets_brl: Decimal

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TopPopulationMember:
    """One frozen comparison-population member selected in the freeze period."""

    freeze_period: str
    freeze_rank: int
    document_code: str
    institution_cnpj: str
    institution_name: str
    taxonomy: str | None
    realizable_assets_brl: Decimal
    permanent_assets_brl: Decimal
    total_assets_brl: Decimal
    periods_present: int
    component_complete_periods: int
    reference_complete_periods: int
    reference_reconciled_periods: int
    observed_names: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TopPopulationMonthlyBalance:
    """Monthly certified total assets for one frozen population member."""

    report_period: str
    freeze_rank: int
    institution_cnpj: str
    institution_name: str
    document_code: str
    realizable_assets_brl: Decimal
    permanent_assets_brl: Decimal
    total_assets_brl: Decimal
    source_checksum: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PopulationControl:
    """One machine-readable checkpoint 0C gate control."""

    control_name: str
    passed: bool
    expected_value: str
    actual_value: str
    detail: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PopulationAnalysis:
    """Complete output of the total-assets and population certification."""

    period_profiles: tuple[TotalAssetsPeriodProfile, ...]
    population: tuple[TopPopulationMember, ...]
    monthly_balances: tuple[TopPopulationMonthlyBalance, ...]
    controls: tuple[PopulationControl, ...]

    @property
    def passed(self) -> bool:
        return bool(self.controls) and self.controls[-1].passed


@dataclass
class _InstitutionPeriod:
    period: str
    cnpj: str
    source_checksum: str
    names: set[str] = field(default_factory=set)
    taxonomies: set[str] = field(default_factory=set)
    balances: dict[str, Decimal] = field(
        default_factory=lambda: defaultdict(Decimal)
    )
    account_row_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def balance_or_zero(self, account_code: str) -> Decimal:
        return self.balances.get(account_code, Decimal())

    @property
    def total_assets(self) -> Decimal:
        return self.balance_or_zero(REALIZABLE_ASSETS_ACCOUNT) + self.balance_or_zero(
            PERMANENT_ASSETS_ACCOUNT
        )

    @property
    def has_reference_total(self) -> bool:
        return TOTAL_GENERAL_ASSETS_ACCOUNT in self.balances

    @property
    def reference_difference(self) -> Decimal | None:
        if not self.has_reference_total:
            return None
        reference_assets = self.balances[TOTAL_GENERAL_ASSETS_ACCOUNT] - self.balance_or_zero(
            ACTIVE_COMPENSATION_ACCOUNT
        )
        return self.total_assets - reference_assets

    @property
    def name(self) -> str:
        return sorted(self.names)[-1] if self.names else ""

    @property
    def taxonomy(self) -> str | None:
        return sorted(self.taxonomies)[-1] if self.taxonomies else None


def profile_cosif_population(
    downloads: Iterable[DownloadRecord],
    profiles: Iterable[ProfileRecord],
    *,
    freeze_period: str | None = None,
    population_size: int = 15,
    reconciliation_tolerance_brl: Decimal = Decimal("1.00"),
) -> PopulationAnalysis:
    """Profile official 4010 rows and freeze a reproducible comparison population."""
    if population_size < 1:
        raise ValueError("population_size must be at least 1")
    if reconciliation_tolerance_brl < 0:
        raise ValueError("reconciliation_tolerance_brl cannot be negative")

    download_list = list(downloads)
    profile_list = list(profiles)
    if not download_list:
        raise ValueError("COSIF population profiling requires complete downloads")
    checksum_by_period = {
        record.period: record.sha256 or "" for record in download_list
    }
    periods = sorted(checksum_by_period)
    selected_freeze_period = freeze_period or periods[-1]
    if selected_freeze_period not in checksum_by_period:
        raise ValueError(f"Freeze period {selected_freeze_period} is absent from the manifest")

    _, landing_rows = build_cosif_landing_records(download_list, profile_list)
    documents_by_period: dict[str, set[str]] = defaultdict(set)
    institutions_by_period_document: dict[tuple[str, str], set[str]] = defaultdict(set)
    observations: dict[tuple[str, str], _InstitutionPeriod] = {}
    names_by_cnpj: dict[str, set[str]] = defaultdict(set)
    account_names: dict[str, set[str]] = defaultdict(set)
    blank_cnpj_rows = 0

    for row in landing_rows:
        period = str(row["source_period"])
        document_code = str(row["documento"])
        cnpj = str(row["cnpj"])
        documents_by_period[period].add(document_code)
        if not cnpj:
            blank_cnpj_rows += 1
            continue
        institutions_by_period_document[(period, document_code)].add(cnpj)
        if document_code != RANKING_DOCUMENT:
            continue

        key = (period, cnpj)
        observation = observations.setdefault(
            key,
            _InstitutionPeriod(
                period=period,
                cnpj=cnpj,
                source_checksum=str(row["source_checksum"]),
            ),
        )
        institution_name = str(row["nome_instituicao"])
        observation.names.add(institution_name)
        names_by_cnpj[cnpj].add(institution_name)
        if row["taxonomia"]:
            observation.taxonomies.add(str(row["taxonomia"]))
        account_code = str(row["conta"])
        if account_code in ASSET_ACCOUNTS:
            observation.balances[account_code] += Decimal(row["saldo"])
            observation.account_row_counts[account_code] += 1
            account_names[account_code].add(str(row["nome_conta"]))

    period_profiles = _build_period_profiles(
        periods,
        checksum_by_period,
        institutions_by_period_document,
        observations,
        reconciliation_tolerance_brl,
    )
    candidates = _rank_candidates(observations, selected_freeze_period)
    selected = candidates[:population_size]
    selected_cnpjs = [candidate.cnpj for candidate in selected]
    monthly_balances = _build_monthly_balances(periods, selected, observations)
    population = _build_population(
        periods,
        selected,
        observations,
        names_by_cnpj,
        reconciliation_tolerance_brl,
    )
    controls = _build_controls(
        periods=periods,
        freeze_period=selected_freeze_period,
        population_size=population_size,
        candidates=candidates,
        selected_cnpjs=selected_cnpjs,
        observations=observations,
        documents_by_period=documents_by_period,
        account_names=account_names,
        blank_cnpj_rows=blank_cnpj_rows,
        reconciliation_tolerance_brl=reconciliation_tolerance_brl,
    )
    return PopulationAnalysis(
        period_profiles=tuple(period_profiles),
        population=tuple(population),
        monthly_balances=tuple(monthly_balances),
        controls=tuple(controls),
    )


def _build_period_profiles(
    periods: list[str],
    checksum_by_period: dict[str, str],
    institutions_by_period_document: dict[tuple[str, str], set[str]],
    observations: dict[tuple[str, str], _InstitutionPeriod],
    tolerance: Decimal,
) -> list[TotalAssetsPeriodProfile]:
    results: list[TotalAssetsPeriodProfile] = []
    for period in periods:
        period_observations = [
            observation
            for (observed_period, _), observation in observations.items()
            if observed_period == period
        ]
        differences = [
            abs(difference)
            for observation in period_observations
            if (difference := observation.reference_difference) is not None
        ]
        results.append(
            TotalAssetsPeriodProfile(
                period=period,
                source_checksum=checksum_by_period[period],
                document_4010_institutions=len(
                    institutions_by_period_document[(period, RANKING_DOCUMENT)]
                ),
                document_4016_institutions=len(
                    institutions_by_period_document[(period, SEMESTER_END_DOCUMENT)]
                ),
                realizable_assets_present=sum(
                    REALIZABLE_ASSETS_ACCOUNT in observation.balances
                    for observation in period_observations
                ),
                permanent_assets_present=sum(
                    PERMANENT_ASSETS_ACCOUNT in observation.balances
                    for observation in period_observations
                ),
                reference_total_present=len(differences),
                reference_reconciled=sum(difference <= tolerance for difference in differences),
                reference_outliers=sum(difference > tolerance for difference in differences),
                max_abs_reference_difference_brl=max(differences, default=None),
                summed_total_assets_brl=sum(
                    (observation.total_assets for observation in period_observations),
                    start=Decimal(),
                ),
            )
        )
    return results


def _rank_candidates(
    observations: dict[tuple[str, str], _InstitutionPeriod], freeze_period: str
) -> list[_InstitutionPeriod]:
    candidates = [
        observation
        for (period, _), observation in observations.items()
        if period == freeze_period and REALIZABLE_ASSETS_ACCOUNT in observation.balances
    ]
    return sorted(candidates, key=lambda item: (-item.total_assets, item.cnpj))


def _build_monthly_balances(
    periods: list[str],
    selected: list[_InstitutionPeriod],
    observations: dict[tuple[str, str], _InstitutionPeriod],
) -> list[TopPopulationMonthlyBalance]:
    results: list[TopPopulationMonthlyBalance] = []
    for rank, frozen in enumerate(selected, start=1):
        for period in periods:
            observation = observations.get((period, frozen.cnpj))
            if observation is None or REALIZABLE_ASSETS_ACCOUNT not in observation.balances:
                continue
            results.append(
                TopPopulationMonthlyBalance(
                    report_period=period,
                    freeze_rank=rank,
                    institution_cnpj=frozen.cnpj,
                    institution_name=observation.name,
                    document_code=RANKING_DOCUMENT,
                    realizable_assets_brl=observation.balance_or_zero(
                        REALIZABLE_ASSETS_ACCOUNT
                    ),
                    permanent_assets_brl=observation.balance_or_zero(
                        PERMANENT_ASSETS_ACCOUNT
                    ),
                    total_assets_brl=observation.total_assets,
                    source_checksum=observation.source_checksum,
                )
            )
    return sorted(results, key=lambda item: (item.report_period, item.freeze_rank))


def _build_population(
    periods: list[str],
    selected: list[_InstitutionPeriod],
    observations: dict[tuple[str, str], _InstitutionPeriod],
    names_by_cnpj: dict[str, set[str]],
    tolerance: Decimal,
) -> list[TopPopulationMember]:
    results: list[TopPopulationMember] = []
    for rank, frozen in enumerate(selected, start=1):
        history = [observations.get((period, frozen.cnpj)) for period in periods]
        available = [observation for observation in history if observation is not None]
        component_complete = [
            observation
            for observation in available
            if REALIZABLE_ASSETS_ACCOUNT in observation.balances
            and PERMANENT_ASSETS_ACCOUNT in observation.balances
        ]
        reference_differences = [
            abs(difference)
            for observation in available
            if (difference := observation.reference_difference) is not None
        ]
        results.append(
            TopPopulationMember(
                freeze_period=frozen.period,
                freeze_rank=rank,
                document_code=RANKING_DOCUMENT,
                institution_cnpj=frozen.cnpj,
                institution_name=frozen.name,
                taxonomy=frozen.taxonomy,
                realizable_assets_brl=frozen.balance_or_zero(REALIZABLE_ASSETS_ACCOUNT),
                permanent_assets_brl=frozen.balance_or_zero(PERMANENT_ASSETS_ACCOUNT),
                total_assets_brl=frozen.total_assets,
                periods_present=len(available),
                component_complete_periods=len(component_complete),
                reference_complete_periods=len(reference_differences),
                reference_reconciled_periods=sum(
                    difference <= tolerance for difference in reference_differences
                ),
                observed_names="|".join(sorted(names_by_cnpj[frozen.cnpj])),
            )
        )
    return results


def _build_controls(
    *,
    periods: list[str],
    freeze_period: str,
    population_size: int,
    candidates: list[_InstitutionPeriod],
    selected_cnpjs: list[str],
    observations: dict[tuple[str, str], _InstitutionPeriod],
    documents_by_period: dict[str, set[str]],
    account_names: dict[str, set[str]],
    blank_cnpj_rows: int,
    reconciliation_tolerance_brl: Decimal,
) -> list[PopulationControl]:
    controls: list[PopulationControl] = []

    def add(name: str, passed: bool, expected: object, actual: object, detail: str) -> None:
        controls.append(
            PopulationControl(
                control_name=name,
                passed=passed,
                expected_value=str(expected),
                actual_value=str(actual),
                detail=detail,
            )
        )

    add(
        "freeze_period_is_latest",
        freeze_period == periods[-1],
        periods[-1],
        freeze_period,
        "Membership is frozen from the latest complete official period.",
    )
    observed_documents = sorted(
        {document for values in documents_by_period.values() for document in values}
    )
    semester_end_periods = sorted(
        period
        for period, documents in documents_by_period.items()
        if SEMESTER_END_DOCUMENT in documents
    )
    documents_valid = set(observed_documents) <= {RANKING_DOCUMENT, SEMESTER_END_DOCUMENT}
    semester_end_valid = all(period.endswith(("06", "12")) for period in semester_end_periods)
    add(
        "document_scope_is_individual_4010",
        documents_valid and semester_end_valid,
        "rank 4010; observe 4016 only at semester-end",
        f"documents={'|'.join(observed_documents)};4016_periods={'|'.join(semester_end_periods)}",
        "4016 is a semiannual duplicate position and is excluded from ranking and trends.",
    )
    actual_account_names = "|".join(
        f"{code}:{'~'.join(sorted(account_names[code]))}" for code in sorted(ASSET_ACCOUNTS)
    )
    names_valid = all(
        account_names[code] == {name} for code, name in EXPECTED_ACCOUNT_NAMES.items()
    )
    add(
        "asset_account_contract",
        names_valid,
        "|".join(f"{code}:{EXPECTED_ACCOUNT_NAMES[code]}" for code in sorted(ASSET_ACCOUNTS)),
        actual_account_names,
        "Total assets are reported class 1 plus class 2; class 3 is excluded.",
    )
    duplicate_rows = sum(
        count > 1
        for observation in observations.values()
        for count in observation.account_row_counts.values()
    )
    add(
        "relevant_account_rows_are_unique",
        duplicate_rows == 0 and blank_cnpj_rows == 0,
        "duplicate_keys=0;blank_cnpj_rows=0",
        f"duplicate_keys={duplicate_rows};blank_cnpj_rows={blank_cnpj_rows}",
        "The relevant top-level balances must have one row per period, document and CNPJ.",
    )
    add(
        "population_size",
        len(selected_cnpjs) == population_size,
        population_size,
        len(selected_cnpjs),
        "The authored comparison set is selected once from the freeze-period ranking.",
    )
    cutoff_gap = (
        candidates[population_size - 1].total_assets - candidates[population_size].total_assets
        if len(candidates) > population_size
        else None
    )
    add(
        "cutoff_is_unambiguous",
        cutoff_gap is not None and cutoff_gap > 0,
        "positive rank-15 minus rank-16 gap",
        cutoff_gap if cutoff_gap is not None else "unavailable",
        "A tie at the cutoff would require an authored tie-break decision.",
    )
    expected_population_periods = population_size * len(periods)
    present_population_periods = sum(
        (period, cnpj) in observations for period in periods for cnpj in selected_cnpjs
    )
    add(
        "stable_population_period_coverage",
        present_population_periods == expected_population_periods,
        expected_population_periods,
        present_population_periods,
        "Every frozen member must be present in every MVP month.",
    )
    explicit_component_periods = sum(
        PERMANENT_ASSETS_ACCOUNT in observations[(period, cnpj)].balances
        and REALIZABLE_ASSETS_ACCOUNT in observations[(period, cnpj)].balances
        for period in periods
        for cnpj in selected_cnpjs
        if (period, cnpj) in observations
    )
    add(
        "top_population_components_are_explicit",
        explicit_component_periods == expected_population_periods,
        expected_population_periods,
        explicit_component_periods,
        "Although zero-balance accounts may be omitted, both components are explicit "
        "for the top 15.",
    )
    stable_names = sum(
        len(
            {
                observations[(period, cnpj)].name
                for period in periods
                if (period, cnpj) in observations
            }
        )
        == 1
        for cnpj in selected_cnpjs
    )
    add(
        "top_population_names_are_stable",
        stable_names == population_size,
        population_size,
        stable_names,
        "CNPJ is the membership key; stable names avoid a Type-2 requirement in the MVP window.",
    )
    reference_differences = [
        abs(difference)
        for period in periods
        for cnpj in selected_cnpjs
        if (period, cnpj) in observations
        if (difference := observations[(period, cnpj)].reference_difference) is not None
    ]
    reconciled = sum(
        difference <= reconciliation_tolerance_brl for difference in reference_differences
    )
    max_difference = max(reference_differences, default=None)
    add(
        "top_population_reference_reconciliation",
        bool(reference_differences) and reconciled == len(reference_differences),
        f"all available checks within BRL {reconciliation_tolerance_brl}",
        f"{reconciled}/{len(reference_differences)};max={max_difference}",
        "Reference check: class 1 + class 2 equals total-general less class 3 where "
        "total-general is published.",
    )
    prior_passed = all(control.passed for control in controls)
    add(
        "checkpoint_0c_ready",
        prior_passed,
        "ready",
        "ready" if prior_passed else "blocked",
        "All preceding mapping, scope, coverage, cutoff and reconciliation controls must pass.",
    )
    return controls


def write_population_analysis(analysis: PopulationAnalysis, output_dir: Path) -> dict[str, int]:
    """Write the four checkpoint 0C evidence files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "period_profile": (
            analysis.period_profiles,
            output_dir / "total_assets_period_profile.csv",
        ),
        "population": (analysis.population, output_dir / "top15_population.csv"),
        "monthly_balances": (
            analysis.monthly_balances,
            output_dir / "top15_total_assets_by_month.csv",
        ),
        "controls": (analysis.controls, output_dir / "checkpoint_0c_controls.csv"),
    }
    return {
        name: _write_dataclasses(records, path)
        for name, (records, path) in outputs.items()
    }


def _write_dataclasses(records: Iterable[object], output_path: Path) -> int:
    materialized = list(records)
    if not materialized:
        raise ValueError(f"Cannot write empty evidence file {output_path}")
    fieldnames = list(materialized[0].__dataclass_fields__)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(record.as_dict() for record in materialized)
    return len(materialized)
