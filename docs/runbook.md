# Data-platform runbook

Updated: 2026-08-11

This runbook operates the implemented landing, staging, canonical core and certified
reporting marts. Power BI is authorized only against the frozen twelve-object mart
contract, never against raw, staging or core relations.

## Current operational state

- Fixture regression: green on PostgreSQL 18, dbt and Dagster.
- Official catalog: accessible and parsed successfully.
- Official COSIF bodies: all 15 MVP archives downloaded and profiled successfully.
- Official SGS observations: all five series passed a bounded 202501–202603 retry.
- Machine-readable readiness: latest bounded local assessment is `ready`.
- Total-assets/population gate: checkpoint 0C is `ready` from document 4010 and the
  frozen 202603 top 15.
- Final source-profile gate: checkpoint 0E is
  `ready_for_official_warehouse_certification`; the warehouse has since been
  certified and its bounded mapping drafts have been resolved.
- Official PostgreSQL/dbt/Dagster run: certified for the frozen 202501–202603 window
  in isolated database `banking_official_202501_202603`.
- Reporting marts: all 13 controls are certified under mapping and contract version
  `2026-08-11-v1`; the retained official Dagster run is
  `8dff5096-2d50-418c-a8a7-8758c7ed63f4`.

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
definitions, 15 observations and 5 fetch manifests. dbt expects 24 models, two seeds
and 188 tests (`214/214`). Repeated dlt loads must not increase business-table counts.

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

## 4a. Certify total assets and the comparison population

Run the full 0C gate against the complete 202501–202603 COSIF evidence before building
population-dependent marts:

```powershell
uv run --locked banking-data profile-cosif-population `
  --manifest artifacts/generated/cosif_download_manifest.csv `
  --profile artifacts/cosif_source_profile.csv `
  --freeze-period 202603 `
  --output-dir artifacts/generated/checkpoint-0c `
  --population-size 15 `
  --reconciliation-tolerance 1.00
```

Continue only when `checkpoint_0c_ready` is `True` / `ready`. The command ranks only
document 4010, requires 225/225 selected member/month component observations and
discloses whole-source reference outliers separately.

## 4b. Freeze the final source-profile decision

Run the non-mutating 0E gate against the complete retained source window:

```powershell
uv run --locked banking-data assess-source-profile `
  --catalog artifacts/source_catalog.csv `
  --cosif-manifest artifacts/generated/cosif_download_manifest.csv `
  --cosif-profile artifacts/cosif_source_profile.csv `
  --macro-observations artifacts/generated/macro_observations.csv `
  --macro-profile artifacts/macro_source_profile.csv `
  --readiness artifacts/live_readiness_full_202501_202603.csv `
  --population-controls artifacts/checkpoint_0c_controls.csv `
  --population artifacts/top15_population.csv `
  --population-monthly artifacts/top15_total_assets_by_month.csv `
  --period-profile artifacts/total_assets_period_profile.csv `
  --reporting-line-draft config/reporting_line_draft.csv `
  --start 202501 --end 202603 --freeze-period 202603 `
  --population-size 15 `
  --output-dir artifacts/generated/checkpoint-0e
```

Continue only when `checkpoint_0e_ready` reports
`ready_for_official_warehouse_certification`. Inspect the contract's pending rows:
`warehouse_status=not_certified` and `mart_status=not_built` are expected until later
gates. The command performs no PostgreSQL mutation.

## 5. Load and build a ready official sample

Only after readiness, 0C and 0E pass:

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
$env:BANKING_OFFICIAL_MACRO_END = "2026-03-31"
$dagsterEvidence = Join-Path (Resolve-Path "data/work") "dagster-official-certification"
New-Item -ItemType Directory -Force $dagsterEvidence | Out-Null
$env:DAGSTER_HOME = $dagsterEvidence

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

## 6a. Certify the completed official warehouse

After the attached official Dagster command exits successfully, retain its run ID
and certify the isolated database against the dbt result artifact and checkpoint 0C:

```powershell
$env:BANKING_POSTGRES_DB = "banking_official_202501_202603"

uv run --locked banking-data certify-official-warehouse `
  --expected-database banking_official_202501_202603 `
  --dagster-run-id 69dd1ce1-74e9-4ebb-85b5-af7c3fa155c0 `
  --dagster-status success `
  --population-monthly artifacts/top15_total_assets_by_month.csv `
  --dbt-run-results dbt/target/run_results.json `
  --output artifacts/generated/official_warehouse_certification.csv
```

Continue only when all 11 controls pass and `official_warehouse_certified` is
`certified`. A changed run must supply its own Dagster run ID; never copy the example
ID into new evidence. This gate certifies landing and canonical core, not marts.

## 6b. Certify the reporting marts

Use the run-specific Dagster dbt result directory, not the general
`dbt/target/run_results.json`, so the evidence is attached to the same expanded run:

```powershell
$env:BANKING_POSTGRES_DB = "banking_official_202501_202603"

uv run --locked banking-data certify-reporting-marts `
  --expected-database banking_official_202501_202603 `
  --dagster-run-id 8dff5096-2d50-418c-a8a7-8758c7ed63f4 `
  --dagster-status success `
  --population-monthly artifacts/top15_total_assets_by_month.csv `
  --dbt-run-results dbt/target/banking_dbt_assets-8dff509-e29d307/run_results.json `
  --contract contracts/mart-schema.yml `
  --output artifacts/generated/reporting_mart_certification.csv
```

Continue only when all 13 controls pass and `reporting_marts_certified` is
`certified`. A changed run must supply its own run ID and run-specific dbt result
path. The contract check compares every ordered mart column and normalized PostgreSQL
type, so schema drift blocks the BI handoff.

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
| Source profile | Eleven-control 0E CSV and 16-row contract | Restore the exact frozen evidence boundary; do not promote draft reporting lines |
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
- all 11 final source-profile controls and the 16-row frozen contract;
- raw/staging/core counts and fixture flags;
- dbt result totals and reconciliation outcomes;
- Dagster run ID and asset/check status;
- the frozen mapping/contract version and all thirteen mart controls.

## BI handoff gate

Power BI may bind to the certified mart contract, but must not bind to raw, staging
or core tables. The handoff gates are now complete:

1. the official warehouse/dbt/Dagster certification run passes (complete for the
   frozen 202501–202603 window);
2. reporting-line mappings and mart reconciliation are certified;
3. stable top-15 membership and all twelve marts exist;
4. `contracts/mart-schema.yml` is frozen and schema-tested.

The Power BI layer is now implemented (checkpoint 13) and satisfies these gates.

## 8. Open and refresh the Power BI report

The PBIP project is version-controlled under `powerbi/`. It reads only the certified
`analytics_marts` objects through two parameters that default to the local warehouse.

```powershell
docker compose up -d warehouse
# then open powerbi/BankingAnalytics.pbip in Power BI Desktop
```

On first open, confirm the parameters (`localhost:55433` /
`banking_official_202501_202603`) and enter the Database credential (`banking`). The
model refreshes into three pages: Banking Pulse, Compare Banks, Trust.

Operating notes for anyone editing the model:

- Balance measures are semi-additive (latest month via `LASTNONBLANK`); never sum a
  balance across months.
- Period-over-period growth uses `EDATE`, not `DATEADD`, because `dim_date` is
  monthly-grain.
- Do not use `Current` or `Prior` as DAX `VAR` names — this parser treats them as
  reserved and silently compiles the measure to a `SYNTAXERROR` stub. Use `CurVal` /
  `PriorVal`. See `.claude/rules/connect-pbid.md`.
- Measure definitions are governed in `contracts/measure-contract.md`; change the
  contract before changing a measure's meaning.
- To verify without reopening, connect to Desktop's local Analysis Services engine via
  TOM/ADOMD (the `connect-pbid` skill) and query measures directly.

Power BI must never bind to raw, staging or core relations, and must not widen the
twelve-object mart contract implicitly.
