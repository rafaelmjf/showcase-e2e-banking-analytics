# Foundation checkpoint — verified official landing adapters

Updated: 2026-08-11

## Objective

Connect the implemented COSIF archive and SGS API profilers to the exact strict dlt
contracts already proven by fixtures. The adapter must fail closed when acquisition
or profile evidence is incomplete; it must not turn an HTTP failure into a partial
warehouse load.

## Delivered

The `load-official` command now consumes only persisted acquisition evidence:

- the complete COSIF download manifest;
- the matching COSIF schema/volume profile;
- the governed five-series macro registry;
- native SGS observations;
- the matching SGS completeness profiles;
- the exact requested macro date window.

The COSIF adapter verifies download/profile cardinality, checksum, period, URL,
compressed bytes, header, source generation date, declared period, row count and
every streamed row shape. It preserves the raw balance string beside an exact
decimal and creates stable checksum/physical-row identities.

The macro adapter requires one successful profile for each of SGS 4189, 433, 24363,
20539 and 21082. It reconciles observation counts, dates, reporting months,
freshness contracts and retrieval timestamps before creating metadata, observation
and fetch-manifest records. Both adapters produce exactly the frozen dlt column sets.

## Verification

Local verification passed 43 normal tests and one explicitly enabled PostgreSQL
integration test. The integration test generated bounded mocked BCB-shaped bodies,
created a randomly named database, ran both production dlt pipelines, observed raw
counts `(1, 2, 5, 5, 5)`, and removed the isolated database. Mocked rows were not
retained as project data.

[GitHub Actions run 31447549208](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31447549208)
reproduced all 44 tests on PostgreSQL 18, then completed the existing landing, dbt
and Dagster regression path. The final results were:

```text
Python: 44 passed
mocked official dlt load: 1 manifest, 2 balances, 5 metadata, 5 observations, 5 fetches
dbt: PASS=117 WARN=0 ERROR=0 SKIP=0
Dagster definitions: valid
Dagster fixture job: RUN_SUCCESS
```

An earlier Linux run exposed a test-only portability issue: Rich truncated long CLI
option names according to terminal width, while the Windows terminal did not. The
assertion now inspects Click parameter identities instead of rendered help text.

The compact committed record is
`artifacts/official_adapter_checkpoint_summary.csv`.

## Command

After both official profilers succeed:

```powershell
uv run --locked banking-data load-official `
  --cosif-manifest artifacts/generated/cosif_download_manifest.csv `
  --cosif-profile artifacts/generated/cosif_source_profile.csv `
  --macro-observations artifacts/generated/macro_observations.csv `
  --macro-profile artifacts/generated/macro_profile.csv `
  --macro-start 2025-01-01 `
  --macro-end 2026-03-31
```

## Live boundary

The bounded live retry on 11 August 2026 still returned HTTP 502 for the March 2026
COSIF file and for all five SGS series. Therefore the production route is implemented
and integration-tested, but no official observation has been loaded or certified.
WP2/WP3 and the bounded-live requirement remain open until those services recover.
