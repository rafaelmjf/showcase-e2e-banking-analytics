# Foundation checkpoint — fail-closed Dagster source modes

Updated: 2026-08-11

## Objective

Let the same Dagster code location select synthetic fixtures or verified official
evidence without changing physical asset keys, duplicating dbt sources or silently
falling back when official inputs are incomplete.

## Delivered

`BANKING_SOURCE_MODE` accepts exactly two values:

- `fixture`, the safe default used by local development and continuous regression;
- `official`, which requires explicit COSIF manifest/profile paths, SGS
  observation/profile paths and a bounded macro date window.

Both modes expose the same five raw keys and therefore the same 16-asset lineage
through dbt. The selected mode changes only the dlt resources, pipeline state names
and job name (`fixture_end_to_end` or `official_end_to_end`). Unknown modes, absent
variables, nonexistent files, invalid ISO dates and inverted date windows fail while
the code location is being constructed, before any asset runs.

## Verification

The isolated PostgreSQL integration test now performs three separate checks:

1. runs the official adapter through its direct dlt pipeline;
2. materializes both official raw asset groups through `dagster-dlt` and confirms
   idempotent raw counts;
3. constructs the 16-asset official Definitions object and resolves the
   `official_end_to_end` job.

[GitHub Actions run 31448066885](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31448066885)
passed 47 tests on Linux, including that isolated official-mode path. It then loaded
the normal fixture contracts, passed all 117 dbt nodes, validated the default fixture
code location and completed Dagster run
`80cd0ae8-f2bc-48de-8dbf-3cc665b3e231` successfully.

The first clean attempt exposed an important packaging condition: importing the dbt
asset decorator requires a generated `dbt/target/manifest.json`. Tests that only
exercise source-mode configuration no longer import the complete code location at
collection time. The isolated full-definition test explicitly runs `dbt parse`
before its lazy import, while deployment validation still happens after a dbt build.
A clean-tree local test also passed with `dbt/target` temporarily absent.

The compact committed record is `artifacts/dagster_source_mode_summary.csv`.

## Boundary

This certifies source selection, official raw Dagster materialization and stable
lineage. The full `official_end_to_end` job has not been executed because mocked
two-row bank data is not a valid analytical sample and live BCB acquisition still
returns HTTP 502. No official dbt certification, reporting mart or BI contract is
claimed.
