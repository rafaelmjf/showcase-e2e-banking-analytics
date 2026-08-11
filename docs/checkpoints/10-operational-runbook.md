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
- full-window total-assets and population certification;
- final non-mutating source-profile decision;
- official dlt, dbt and Dagster commands;
- post-run official warehouse certification;
- safe removal of source-mode environment variables;
- manual GitHub workflow dispatch and artifact retrieval;
- diagnosis and safe next action for eight hard gates;
- the evidence checklist for a future green run;
- the explicit mart-contract/BI handoff gate.

Two tests compare the runbook to the actual Typer command registry and require all
eleven current operational stages. They also pin readiness before `load-official`
and the no-fallback fixture boundary.

## Verification

[GitHub Actions run 31449393897](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31449393897)
passed 53 tests, both 117-node dbt builds, catalog generation and Dagster run
`8915ba97-dca6-4c23-8584-1b705156c3b4` on a clean Linux/PostgreSQL 18 environment.

The compact committed record is `artifacts/runbook_checkpoint_summary.csv`.

## Boundary

The runbook does not bypass source gates. The original retained run demonstrates the
HTTP-502 recovery path; later local evidence completed 0B, 0C and 0E. The official
warehouse/dbt/Dagster certification remains an explicit gate.
