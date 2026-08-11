# Foundation checkpoint — fixture-backed dbt staging and core

Updated: 2026-08-11

## Objective

Prove that the frozen dlt landing shapes can be converted into source-faithful
staging and a small canonical core with deterministic source-version selection and
auditable quality controls. This checkpoint deliberately stops before reporting
lines, top-15 membership and marts.

## Delivered

Five staging models preserve raw values, typed values, dlt load identifiers, source
URLs, source dates and explicit fixture lineage:

- `stg_cosif_file_manifest`
- `stg_cosif_balance_row`
- `stg_sgs_series_metadata`
- `stg_sgs_observation`
- `stg_sgs_fetch_manifest`

Six core models provide:

- every file version plus deterministic `is_selected` ranking;
- account rows only from selected complete files;
- one bank-period entity and one current account description;
- exactly five governed macro definitions;
- native macro observations with explicit reporting month.

The staging models enforce declared column names and PostgreSQL data types. The core
does not relabel synthetic rows as official data and carries fixture status into all
fact-like objects.

## Controls

The dbt graph includes source tests, staging contracts, core key/null tests and seven
singular business controls:

1. one selected complete file per period;
2. unique checksum plus file-row landing identity;
3. declared manifest rows reconcile to selected account rows;
4. fixture accounting identity reconciles within R$0.01;
5. native macro observation grain is unique;
6. macro months are contiguous inside each observed series window;
7. the registry contains exactly SGS 4189, 433, 24363, 20539 and 21082.

The first local build exposed that YAML flow mappings split an unquoted
`numeric(38,2)` at the comma. Quoting precision types corrected the contract DDL; the
model SQL itself was unchanged. This is retained as a useful implementation
observation rather than hidden from the checkpoint history.

## Verification

The final local command completed with:

```text
11 table models
106 data tests
PASS=117 WARN=0 ERROR=0 SKIP=0
```

[GitHub Actions run 31446214745](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31446214745)
then created a clean PostgreSQL 18 service, passed 37 Python tests, loaded both dlt
sources twice, passed the 11 landing controls and completed the same dbt graph. Its
`run_results.json` records 11 successful models, 106 passing tests, zero warnings,
errors or skips, and 2.531 seconds of dbt execution.

The compact committed result is `artifacts/dbt_fixture_build_summary.csv`; the full
manifest and run results remain attached to the GitHub run.

## Command

```powershell
uv run --locked dbt build --project-dir dbt --profiles-dir dbt
```

## Boundary

This certifies the fixture staging/core mechanics only. No live source has passed
through these models, no reporting-line mapping has been approved, and no top-15 or
consumption mart exists. WP4–WP7 remain incomplete until the official WP0 evidence
is available and the same tests pass on it.
