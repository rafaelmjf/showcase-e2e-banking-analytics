# Foundation checkpoint — operational runbook

Updated: 2026-08-11

## Objective

Make fixture regression, live recovery and a future official execution safely
repeatable by a newcomer without relying on conversation history.

## Delivered

`docs/runbook.md` contains:

- prerequisites and local PostgreSQL defaults;
- the exact idempotent fixture/dlt/dbt/Dagster/docs regression;
- minimal COSIF and SGS availability retries;
- a timestamped bounded acquisition that does not overwrite prior evidence;
- readiness assessment before any warehouse mutation;
- official dlt, dbt and Dagster commands;
- safe removal of source-mode environment variables;
- manual GitHub workflow dispatch and artifact retrieval;
- diagnosis and safe next action for eight hard gates;
- the evidence checklist for a future green run;
- the explicit mart-contract/BI handoff gate.

Two tests compare the runbook to the actual Typer command registry and require all
eight operational stages. They also pin readiness before `load-official` and the
no-fallback fixture boundary.

## Verification

[GitHub Actions run 31449393897](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31449393897)
passed 53 tests, both 117-node dbt builds, catalog generation and Dagster run
`8915ba97-dca6-4c23-8584-1b705156c3b4` on a clean Linux/PostgreSQL 18 environment.

The compact committed record is `artifacts/runbook_checkpoint_summary.csv`.

## Boundary

The runbook does not bypass current source gates. It makes the next official retry
and its evidence review reproducible; it does not complete checkpoints 0B, 0C or 0E
while BCB observation hosts return HTTP 502.
