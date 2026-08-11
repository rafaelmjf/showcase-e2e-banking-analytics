"""Explicit source-mode configuration for the Dagster code location."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path

SOURCE_MODES = {"fixture", "official"}
OFFICIAL_PATH_KEYS = {
    "cosif_manifest": "BANKING_OFFICIAL_COSIF_MANIFEST",
    "cosif_profile": "BANKING_OFFICIAL_COSIF_PROFILE",
    "macro_observations": "BANKING_OFFICIAL_MACRO_OBSERVATIONS",
    "macro_profile": "BANKING_OFFICIAL_MACRO_PROFILE",
}


@dataclass(frozen=True)
class OfficialEvidenceConfig:
    """Resolved, bounded evidence paths required by official Dagster mode."""

    cosif_manifest: Path
    cosif_profile: Path
    macro_observations: Path
    macro_profile: Path
    macro_registry: Path
    macro_start_date: date
    macro_end_date: date

    @classmethod
    def from_environment(
        cls,
        project_root: Path,
        environment: Mapping[str, str] | None = None,
    ) -> OfficialEvidenceConfig:
        """Resolve all official inputs or fail before the code location loads."""
        values = environment if environment is not None else os.environ
        required = [
            *OFFICIAL_PATH_KEYS.values(),
            "BANKING_OFFICIAL_MACRO_START",
            "BANKING_OFFICIAL_MACRO_END",
        ]
        missing = [key for key in required if not values.get(key, "").strip()]
        if missing:
            raise ValueError(
                "Official source mode requires environment variables: "
                + ", ".join(missing)
            )

        resolved_paths = {
            field: _resolve_required_file(project_root, values[key], key)
            for field, key in OFFICIAL_PATH_KEYS.items()
        }
        registry_value = values.get(
            "BANKING_OFFICIAL_MACRO_REGISTRY", "config/macro_series_registry.csv"
        )
        registry = _resolve_required_file(
            project_root, registry_value, "BANKING_OFFICIAL_MACRO_REGISTRY"
        )
        try:
            start_date = date.fromisoformat(values["BANKING_OFFICIAL_MACRO_START"])
            end_date = date.fromisoformat(values["BANKING_OFFICIAL_MACRO_END"])
        except ValueError as exc:
            raise ValueError("Official macro dates must use YYYY-MM-DD") from exc
        if start_date > end_date:
            raise ValueError("Official macro start date must not be after its end date")
        return cls(
            **resolved_paths,
            macro_registry=registry,
            macro_start_date=start_date,
            macro_end_date=end_date,
        )


def resolve_source_mode(
    source_mode: str | None = None,
    environment: Mapping[str, str] | None = None,
) -> str:
    """Return the explicit mode, defaulting safely to synthetic fixtures."""
    values = environment if environment is not None else os.environ
    selected = (source_mode or values.get("BANKING_SOURCE_MODE", "fixture")).strip().lower()
    if selected not in SOURCE_MODES:
        raise ValueError(
            f"BANKING_SOURCE_MODE must be one of {sorted(SOURCE_MODES)}; got {selected!r}"
        )
    return selected


def _resolve_required_file(project_root: Path, value: str, variable_name: str) -> Path:
    path = Path(value)
    resolved = path.resolve() if path.is_absolute() else (project_root / path).resolve()
    if not resolved.is_file():
        raise ValueError(f"{variable_name} does not identify a file: {resolved}")
    return resolved
