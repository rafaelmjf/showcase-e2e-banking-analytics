# Foundation checkpoint — curated dbt catalog

Updated: 2026-08-11

## Objective

Make the implemented raw, staging and canonical core understandable in generated dbt
docs without implying that reporting marts or live-source certification exist.

## Delivered

All five dlt source tables and all 11 dbt models now have curated descriptions. The
catalog names ownership, BCB authority and ODbL at the source boundary, and documents
important identities and raw/typed value pairs. Four reusable governance notes make
the following constraints visible throughout lineage:

- fixture validation is not banking evidence;
- URLs, checksums, source timestamps and dlt load identifiers preserve lineage;
- one complete COSIF checksum is selected deterministically per period;
- native SGS dates are aligned to months without aggregation or causal claims.

Staging descriptions emphasize typing and renaming without hidden business mapping.
Core descriptions distinguish canonical facts/entities from the withheld public
reporting-line marts.

CI now runs `dbt docs generate` after the complete Dagster regression and uploads
`index.html`, `catalog.json`, `manifest.json` and `run_results.json` together.

## Verification

The local catalog generated successfully after the 117-node build. The first attempt
correctly failed because the reusable documentation block file was outside dbt's
configured `model-paths`; moving it under `dbt/models` fixed discovery rather than
duplicating text inline.

[GitHub Actions run 31448952033](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31448952033)
then passed 49 tests, both 117-node dbt builds, Dagster run
`9b25831c-4302-4f55-a0ff-d8cb4f13b453` and catalog generation. Downloaded artifact
`9085610234` was inspected and contains:

```text
11 models; 11 described
5 source tables; 5 described
4 authored reusable documentation blocks
11 catalog model relations + 5 catalog source relations
catalog.json: present
index.html: present
```

The compact committed record is `artifacts/dbt_catalog_checkpoint_summary.csv`.

## Boundary

This documents only the implemented landing, staging and canonical core. There are
no exposures, marts, reporting-line mappings or Power BI consumption objects to
document yet. Those remain blocked by the live 0B/0C evidence gates.
