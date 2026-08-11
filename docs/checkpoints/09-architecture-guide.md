# Foundation checkpoint — newcomer architecture guide

Updated: 2026-08-11

## Objective

Give a newcomer one presentation-ready document that explains the project problem,
solution, official inputs, defended stack choices, implemented layers, entity
relationships, quality strategy, challenges and current/planned boundary without
requiring them to reconstruct decisions from the work-package plan.

## Delivered

`docs/architecture.md` now provides:

- the tangible banking question and bounded proposed product;
- COSIF fields and the exact five macro series/treatments;
- reasons for dlt, PostgreSQL, dbt, Dagster and Power BI;
- explicit arguments against Data Vault, Airbyte and SQLMesh for this MVP;
- a source-to-consumption flow with planned nodes clearly marked;
- raw and canonical-core ERDs;
- responsibilities for all five source tables, five staging models and six core
  models;
- orchestration, readiness and quality controls;
- the important parsing, scope, versioning and macro-interpretation challenges;
- an implemented-versus-planned matrix and continuation links.

Two regression tests derive the 11 dbt model names from the repository, add the five
raw asset names and fail if the guide omits any of the 16. They also pin the statements
that the full official job is not certified and Power BI remains planned.

## Verification

[GitHub Actions run 31449192239](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31449192239)
passed 51 tests, both 117-node dbt builds, generated the catalog and completed Dagster
run `364228dc-1c1e-48ff-b91d-45cf9e69827c`. The documentation coverage tests passed
on the clean Linux checkout.

The compact committed record is
`artifacts/architecture_guide_checkpoint_summary.csv`.

## Boundary

The guide describes planned marts and BI only as future components. It does not
invent reporting-line mappings, top-15 membership, measures or report pages while
the live profile is blocked.
