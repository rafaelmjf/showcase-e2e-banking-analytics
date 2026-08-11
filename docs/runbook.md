# Data-platform runbook

Updated: 2026-08-11

This runbook operates the implemented landing, staging and canonical-core platform.
It does not authorize reporting marts or Power BI work that depends on unresolved
COSIF mappings.

## Current operational state

- Fixture regression: green on PostgreSQL 18, dbt and Dagster.
- Official catalog: accessible and parsed successfully.
- Official COSIF bodies: HTTP 502 at the latest check.
- Official SGS observations: HTTP 502 for all five series at the latest check.
- Machine-readable readiness: `blocked`.
- Official PostgreSQL/dbt/Dagster run: correctly skipped by the hard gate.

Use [the handover](../HANDOVER.md) for the latest run IDs and evidence counts before
starting a new attempt.

## Prerequisites

From the repository root:

```powershell
uv sync --locked --extra dev
docker compose up -d warehouse
docker compose ps warehouse
```

The compose defaults are development-only and match `WarehouseSettings`:

```text
host=localhost port=55433 database=banking user=banking
```

Do not put production credentials in `.env`, dlt state or committed dbt profiles.
Environment variables with the `BANKING_POSTGRES_` prefix override local defaults.

## 1. Prove the fixture foundation

Run this before diagnosing a live source. It separates implementation regressions
from BCB availability problems.

```powershell
uv run --locked ruff check src tests
uv run --locked pytest

uv run --locked banking-data load-fixtures --project-root .
uv run --locked banking-data load-fixtures --project-root .
uv run --locked banking-data verify-fixtures `
  --output artifacts/generated/fixture_landing_evidence.csv

uv run --locked dbt build --project-dir dbt --profiles-dir dbt
uv run --locked dagster definitions validate `
  -f orchestration/definitions.py -a defs
uv run --locked dagster job execute `
  -f orchestration/definitions.py -a defs -j fixture_end_to_end
uv run --locked dbt docs generate --project-dir dbt --profiles-dir dbt
```

Expected fixture identities are 2 COSIF manifests, 24 account rows, 5 macro
definitions, 15 observations and 5 fetch manifests. dbt currently expects 11 models
plus 106 tests. Repeated dlt loads must not increase business-table counts.

If this path fails, do not retry live sources yet. Fix the local/CI regression and
record it as a separate checkpoint.

## 2. Perform a minimal live availability retry

The fastest current COSIF check is one active period:

```powershell
uv run --locked banking-data download-cosif `
  --start 202603 --end 202603 `
  --catalog artifacts/source_catalog.csv `
  --download-dir data/downloads/cosif `
  --manifest artifacts/generated/cosif_download_manifest_retry.csv `
  --timeout 30 --attempts 1
```

The minimal five-series check is one month:

```powershell
uv run --locked banking-data profile-sgs `
  --registry config/macro_series_registry.csv `
  --start 2025-01-01 --end 2025-01-31 `
  --observations artifacts/generated/macro_observations_retry.csv `
  --profile artifacts/generated/macro_profile_retry.csv `
  --timeout 15 --attempts 1
```

HTTP 5xx is an accessibility failure. Do not edit the catalog to remove the period,
replace failed observations with zero, or treat an empty output as official absence.

## 3. Run a bounded official acquisition locally

Use a unique evidence directory so a retry does not overwrite the previous diagnosis:

```powershell
$runStamp = Get-Date -Format "yyyyMMdd-HHmmss"
$evidenceDir = Join-Path "artifacts/generated" "official-$runStamp"
$downloadDir = Join-Path "data/downloads/cosif" $runStamp
New-Item -ItemType Directory -Path $evidenceDir -Force | Out-Null
```

Choose explicit bounds. The example uses one COSIF month and a short macro window:

```powershell
uv run --locked banking-data source-catalog `
  --output (Join-Path $evidenceDir "source_catalog.csv")

uv run --locked banking-data download-cosif `
  --start 202603 --end 202603 `
  --catalog (Join-Path $evidenceDir "source_catalog.csv") `
  --download-dir $downloadDir `
  --manifest (Join-Path $evidenceDir "cosif_download_manifest.csv")

uv run --locked banking-data profile-cosif `
  --manifest (Join-Path $evidenceDir "cosif_download_manifest.csv") `
  --output (Join-Path $evidenceDir "cosif_source_profile.csv")

uv run --locked banking-data profile-sgs `
  --registry config/macro_series_registry.csv `
  --start 2025-01-01 --end 2025-01-31 `
  --observations (Join-Path $evidenceDir "macro_observations.csv") `
  --profile (Join-Path $evidenceDir "macro_profile.csv")
```

Do not continue after a nonzero command. Preserve the generated CSVs and use the gate
in the next section to make the blocked reason explicit.

## 4. Assess readiness before mutation

```powershell
uv run --locked banking-data assess-readiness `
  --cosif-manifest (Join-Path $evidenceDir "cosif_download_manifest.csv") `
  --cosif-profile (Join-Path $evidenceDir "cosif_source_profile.csv") `
  --macro-profile (Join-Path $evidenceDir "macro_profile.csv") `
  --cosif-start 202603 --cosif-end 202603 `
  --macro-start 2025-01-01 --macro-end 2025-01-31 `
  --output (Join-Path $evidenceDir "live_readiness.csv")
```

The command writes all nine controls before exiting. Continue only when the overall
row is `pass` / `ready` and the eight preceding controls are individually understood.
A ready result means the bounded inputs are complete; it does not approve accounting
mapping or analytical suitability.

## 5. Load and build a ready official sample

Only after readiness passes:

```powershell
uv run --locked banking-data load-official `
  --cosif-manifest (Join-Path $evidenceDir "cosif_download_manifest.csv") `
  --cosif-profile (Join-Path $evidenceDir "cosif_source_profile.csv") `
  --macro-observations (Join-Path $evidenceDir "macro_observations.csv") `
  --macro-profile (Join-Path $evidenceDir "macro_profile.csv") `
  --macro-start 2025-01-01 --macro-end 2025-01-31

uv run --locked dbt build --project-dir dbt --profiles-dir dbt
```

Record raw and core row counts, selected checksums, fixture flags and all dbt results.
Do not call the sample official if any fact-like core row remains fixture-derived for
the requested period.

## 6. Execute official Dagster mode

Official mode requires every path; it never falls back to fixtures:

```powershell
$env:BANKING_SOURCE_MODE = "official"
$env:BANKING_OFFICIAL_COSIF_MANIFEST = Join-Path $evidenceDir "cosif_download_manifest.csv"
$env:BANKING_OFFICIAL_COSIF_PROFILE = Join-Path $evidenceDir "cosif_source_profile.csv"
$env:BANKING_OFFICIAL_MACRO_OBSERVATIONS = Join-Path $evidenceDir "macro_observations.csv"
$env:BANKING_OFFICIAL_MACRO_PROFILE = Join-Path $evidenceDir "macro_profile.csv"
$env:BANKING_OFFICIAL_MACRO_START = "2025-01-01"
$env:BANKING_OFFICIAL_MACRO_END = "2025-01-31"

uv run --locked dagster definitions validate `
  -f orchestration/definitions.py -a defs
uv run --locked dagster job execute `
  -f orchestration/definitions.py -a defs -j official_end_to_end
```

After the run, remove the source-mode variables from the current shell if returning
to fixture development:

```powershell
Remove-Item Env:BANKING_SOURCE_MODE -ErrorAction SilentlyContinue
Remove-Item Env:BANKING_OFFICIAL_COSIF_MANIFEST -ErrorAction SilentlyContinue
Remove-Item Env:BANKING_OFFICIAL_COSIF_PROFILE -ErrorAction SilentlyContinue
Remove-Item Env:BANKING_OFFICIAL_MACRO_OBSERVATIONS -ErrorAction SilentlyContinue
Remove-Item Env:BANKING_OFFICIAL_MACRO_PROFILE -ErrorAction SilentlyContinue
Remove-Item Env:BANKING_OFFICIAL_MACRO_START -ErrorAction SilentlyContinue
Remove-Item Env:BANKING_OFFICIAL_MACRO_END -ErrorAction SilentlyContinue
```

## 7. Use the GitHub workflow

The repository workflow performs the same bounded sequence on a clean runner:

```powershell
gh workflow run official-sample.yml `
  -f cosif_start_period=202603 `
  -f cosif_end_period=202603 `
  -f macro_start_date=2025-01-01 `
  -f macro_end_date=2025-01-31
```

Follow the returned run and inspect its artifact even when the gate is red:

```powershell
gh run list --workflow official-sample.yml --limit 3
gh run view RUN_ID
gh run download RUN_ID --name official-sample-202603-202603 `
  --dir (Join-Path "data/work" "official-sample-RUN_ID")
```

Expected current behavior is a red acquisition gate with evidence upload and skipped
warehouse/dbt/Dagster official steps. A future green run is a new checkpoint and must
update `HANDOVER.md` before work proceeds.

## Gate diagnosis

| Failed gate | Inspect | Safe next action |
|---|---|---|
| Catalog | Catalog CSV/error and BCB catalog response | Retry bounded; never synthesize URLs or mark periods absent from HTTP failure |
| COSIF download | HTTP status, partial-file absence, ZIP/CRC error, checksum | Retry one period; keep `.part` cleanup and content-addressed final files intact |
| COSIF profile | Header line, encoding, columns, malformed rows, `DATA_BASE` | Treat schema change as a new profiling decision; do not loosen required fields silently |
| Macro profile | Per-series error, gaps, duplicates, freshness lag | Review each official series independently; do not backfill zeros or change units |
| Readiness | Nine-control CSV | Resolve every failed source control; never bypass by calling `load-official` manually |
| dlt load | Load packages, schema-contract error, warehouse connectivity | Preserve package/state; fix contract or infrastructure, then rerun the same evidence |
| dbt build | Failing model/test and selected checksum | Fix source/core logic; do not disable reconciliation to obtain green status |
| Dagster | Asset event/check failure and dbt invocation | Reproduce the failing asset; keep raw/dbt asset keys stable across modes |

## Evidence checklist for a future green run

Record in a new checkpoint document and `HANDOVER.md`:

- Git commit and GitHub/local run identity;
- exact COSIF and macro bounds;
- catalog records and active version chosen per period;
- compressed bytes, SHA-256, source generation dates and row counts;
- document, institution and account coverage;
- all nine readiness controls;
- raw/staging/core counts and fixture flags;
- dbt result totals and reconciliation outcomes;
- Dagster run ID and asset/check status;
- what remains provisional for total assets, top-15 and reporting lines.

## BI handoff gate

Power BI may inspect the architecture and planned contract, but production BI work
must not bind to raw, staging or core tables. Handoff starts only after:

1. live checkpoints 0B, 0C and 0E are complete;
2. reporting-line coverage and total-assets reconciliation are approved;
3. stable top-15 membership and marts exist;
4. `contracts/mart-schema.yml` is frozen and tested.

Until then, the data layer is a verified foundation with an explicit external-source
blocker, not a finished analytical product.
