# Foundation checkpoint — fixture-backed Dagster asset graph

Updated: 2026-08-11

## Objective

Prove that Dagster can orchestrate the real dlt and dbt integrations as one
observable asset graph before official BCB downloads are available. This checkpoint
certifies orchestration mechanics, not live-source completeness.

## Delivered

The code location exposes 16 materializable assets:

- five `dagster-dlt` raw landing assets in the physical `raw_cosif` and `raw_macro`
  datasets;
- five dbt staging assets;
- six dbt core assets;
- a `fixture_end_to_end` job that materializes the complete graph.

A custom dlt translator assigns raw asset keys as `[dataset, table]`. Those keys are
identical to the dbt source keys, so the graph has direct raw-to-staging lineage and
does not show duplicate logical source nodes. dbt tests stream back to Dagster as
asset checks; the COSIF manifest row-count reconciliation is attached directly to
`core/account_balance`.

## Verification

Local verification passed:

```text
38 Python tests
Ruff: all checks passed
Dagster definitions: valid
Dagster fixture job: RUN_SUCCESS
dbt inside Dagster: PASS=117 WARN=0 ERROR=0 SKIP=0
```

[GitHub Actions run 31446855199](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31446855199)
then reproduced the checkpoint on a clean Ubuntu runner and PostgreSQL 18 service.
The job completed in 1 minute 12 seconds. Dagster run
`206dfd08-498f-4eb6-9315-910ad51b12aa` materialized the graph successfully, and its
dbt step passed 11 models plus 106 tests.

The compact committed record is `artifacts/dagster_fixture_run_summary.csv`; the
full logs, dbt manifest and run results remain attached to the GitHub run.

## Command

```powershell
uv run --locked dbt parse --project-dir dbt --profiles-dir dbt
uv run --locked dagster definitions validate -f orchestration/definitions.py -a defs
uv run --locked dagster job execute `
  -f orchestration/definitions.py -a defs -j fixture_end_to_end
```

## Boundary

The assets currently use synthetic contract fixtures. WP8 is therefore proven for
the fixture path but is not fully complete: the definition of MVP done also requires
a bounded official live sample. Reporting-line mapping, top-15 selection, marts and
the Power BI contract remain intentionally absent.
