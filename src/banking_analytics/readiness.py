"""Machine-readable implementation-readiness controls for bounded live evidence."""

from __future__ import annotations

import csv
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

from banking_analytics.bcb.cosif import iter_periods
from banking_analytics.sources.cosif import DownloadRecord, ProfileRecord
from banking_analytics.sources.sgs import (
    EXPECTED_SERIES_CODES,
    MacroProfile,
)


@dataclass(frozen=True)
class ReadinessControl:
    """One deterministic condition required before a bounded official load."""

    scope: str
    control_name: str
    status: str
    expected_value: str
    actual_value: str
    detail: str

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def assess_live_readiness(
    downloads: Iterable[DownloadRecord],
    cosif_profiles: Iterable[ProfileRecord],
    macro_profiles: Iterable[MacroProfile],
    cosif_start_period: str,
    cosif_end_period: str,
    macro_start_date: date,
    macro_end_date: date,
) -> list[ReadinessControl]:
    """Assess exact evidence coverage without loading or mutating the warehouse."""
    download_list = list(downloads)
    cosif_profile_list = list(cosif_profiles)
    macro_profile_list = list(macro_profiles)
    expected_periods = list(iter_periods(cosif_start_period, cosif_end_period))
    expected_period_set = set(expected_periods)
    actual_periods = [row.period for row in download_list]
    actual_period_set = set(actual_periods)
    complete_downloads = [row for row in download_list if row.status == "complete"]
    download_checksums = {row.sha256 for row in complete_downloads if row.sha256}
    profile_checksums = {row.sha256 for row in cosif_profile_list}
    controls: list[ReadinessControl] = []

    _add_control(
        controls,
        "cosif",
        "manifest_period_coverage",
        actual_period_set == expected_period_set and len(actual_periods) == len(expected_periods),
        "|".join(expected_periods),
        "|".join(sorted(actual_period_set)),
        _duplicate_detail(actual_periods),
    )
    _add_control(
        controls,
        "cosif",
        "all_downloads_complete",
        len(complete_downloads) == len(expected_periods),
        str(len(expected_periods)),
        str(len(complete_downloads)),
        _download_error_detail(download_list),
    )
    _add_control(
        controls,
        "cosif",
        "profile_matches_complete_downloads",
        bool(complete_downloads)
        and len(cosif_profile_list) == len(complete_downloads)
        and profile_checksums == download_checksums,
        "one profile per complete checksum",
        f"profiles={len(cosif_profile_list)};checksums={len(profile_checksums)}",
        "",
    )
    valid_profiles = [
        row
        for row in cosif_profile_list
        if row.row_count > 0
        and row.malformed_row_count == 0
        and row.period_matches
        and row.source_generated_at
    ]
    _add_control(
        controls,
        "cosif",
        "all_profiles_valid",
        len(valid_profiles) == len(expected_periods),
        str(len(expected_periods)),
        str(len(valid_profiles)),
        "Requires rows, zero malformed rows, matching DATA_BASE and generation date.",
    )

    macro_codes = [row.series_code for row in macro_profile_list]
    _add_control(
        controls,
        "macro",
        "exact_series_coverage",
        set(macro_codes) == EXPECTED_SERIES_CODES
        and len(macro_codes) == len(EXPECTED_SERIES_CODES),
        "|".join(sorted(EXPECTED_SERIES_CODES, key=int)),
        "|".join(sorted(set(macro_codes), key=int)),
        _duplicate_detail(macro_codes),
    )
    complete_macro = [row for row in macro_profile_list if row.status == "complete"]
    _add_control(
        controls,
        "macro",
        "all_series_complete",
        len(complete_macro) == len(EXPECTED_SERIES_CODES),
        str(len(EXPECTED_SERIES_CODES)),
        str(len(complete_macro)),
        _macro_error_detail(macro_profile_list),
    )
    expected_start_month = f"{macro_start_date.year:04d}{macro_start_date.month:02d}"
    expected_end_month = f"{macro_end_date.year:04d}{macro_end_date.month:02d}"
    matching_windows = [
        row
        for row in macro_profile_list
        if row.requested_start_month == expected_start_month
        and row.requested_end_month == expected_end_month
    ]
    _add_control(
        controls,
        "macro",
        "requested_window_matches",
        len(matching_windows) == len(EXPECTED_SERIES_CODES),
        f"{expected_start_month}|{expected_end_month}",
        str(len(matching_windows)),
        "Actual value is the number of profiles matching both requested bounds.",
    )
    positive_macro = [row for row in macro_profile_list if row.row_count > 0]
    _add_control(
        controls,
        "macro",
        "all_series_have_observations",
        len(positive_macro) == len(EXPECTED_SERIES_CODES),
        str(len(EXPECTED_SERIES_CODES)),
        str(len(positive_macro)),
        "",
    )

    ready = all(control.passed for control in controls)
    _add_control(
        controls,
        "overall",
        "bounded_official_load_ready",
        ready,
        "ready",
        "ready" if ready else "blocked",
        "All preceding controls must pass.",
    )
    return controls


def write_readiness_controls(
    records: Iterable[ReadinessControl], output_path: Path
) -> int:
    """Persist the assessment as a stable CSV contract."""
    materialized = list(records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ReadinessControl.__dataclass_fields__))
        writer.writeheader()
        writer.writerows(record.as_dict() for record in materialized)
    return len(materialized)


def _add_control(
    controls: list[ReadinessControl],
    scope: str,
    control_name: str,
    passed: bool,
    expected_value: str,
    actual_value: str,
    detail: str,
) -> None:
    controls.append(
        ReadinessControl(
            scope=scope,
            control_name=control_name,
            status="pass" if passed else "fail",
            expected_value=expected_value,
            actual_value=actual_value,
            detail=detail,
        )
    )


def _duplicate_detail(values: list[str]) -> str:
    duplicates = sorted(value for value, count in Counter(values).items() if count > 1)
    return f"duplicates={'|'.join(duplicates)}" if duplicates else ""


def _download_error_detail(records: list[DownloadRecord]) -> str:
    return " | ".join(
        f"{row.period}:{row.http_status or 'no-http'}:{row.status}"
        for row in records
        if row.status != "complete"
    )


def _macro_error_detail(records: list[MacroProfile]) -> str:
    return " | ".join(
        f"{row.series_code}:{row.status}" for row in records if row.status != "complete"
    )
