# Plan — Brazilian Banking and Macroeconomic Intelligence

Working repository name: `showcase-e2e-banking-analytics`.

## What this is

A public end-to-end BI showcase based on official Brazilian banking data:

```text
BCB COSIF balance files + BCB macroeconomic series
        -> revision-aware landing
        -> governed accounting model
        -> dimensional consumption marts
        -> Power BI semantic model and report
```

It makes visible what a CV can only claim: financial-domain modelling, accounting
hierarchy control, engineering discipline, metric governance and communication.

## Read in this order

| File | Contents | Owner |
|---|---|---|
| [01-concept.md](01-concept.md) | Problem, product and portfolio thesis | shared |
| [02-architecture.md](02-architecture.md) | Stack, layers and design decisions | shared |
| [03-sources.md](03-sources.md) | COSIF and macro sources, licensing and profiling | data layer |
| [04-data-model.md](04-data-model.md) | Canonical accounting model and dimensional marts | data layer |
| [05-transformation.md](05-transformation.md) | dlt, dbt and Dagster implementation brief | data layer |
| [06-semantic-and-report.md](06-semantic-and-report.md) | Measures, report pages and interpretation limits | BI layer |
| [07-testing-governance.md](07-testing-governance.md) | Reconciliation, regression tests and documentation | shared |
| [08-delivery.md](08-delivery.md) | Phases, work packages and handoff boundary | shared |

## Standing decisions

1. Start with **banks** and **prudential conglomerates**; add other segments only
   after duplicate and consolidation risks are understood.
2. Cover **January 2021 through the latest published period**. This deliberately
   crosses the January 2025 COSIF redesign.
3. Include macroeconomic context from the first release.
4. Model directly into a canonical core and dimensional marts. Do not use Data Vault
   when one official source family and stable reporting keys do not justify it.
5. Preserve every downloaded file version by checksum. Restatements are data, not an
   overwrite.
6. Keep native-frequency macro observations and publish an explicitly aligned monthly
   context mart.
7. Use a small number of decision-grade report pages. Do not build a COSIF account
   browser disguised as a product.
8. Do not claim causation from macroeconomic correlations.

## Initial stack decision

Use **dlt + PostgreSQL + dbt + Dagster + Power BI**.

- dlt replaces bespoke landing code and demonstrates schema, state and load-package
  management for custom BCB files and APIs.
- dbt remains because its Dagster integration, testing conventions and generated
  documentation support the public evidence package.
- Dagster replaces Airflow and exposes the project as a set of observable data assets.
- PostgreSQL remains because it is portable, handles the expected volume comfortably
  and has a direct Power BI connector.

Airbyte is unnecessarily service-heavy for two unauthenticated official source
families with custom file semantics. SQLMesh is a credible alternative, but using its
state and environment model alongside dlt and Dagster would introduce three control
planes in the first release. Both choices can be revisited through an ADR, not added
speculatively.

## Handoff boundary

The data and BI layers meet at `contracts/mart-schema.yml`. It will define every
consumption object, grain, column, type, nullability, business meaning, quality rule
and reference row count. The BI layer must not depend on raw, staging or intermediate
schemas.

## Open decisions that require profiling, not preference

1. Whether consolidated prudential data or individual bank data is the primary
   comparison grain.
2. The exact effective-dated mapping between pre-2025 and post-2025 COSIF accounts.
3. Which balance-sheet lines are sufficiently comparable for public KPIs.
4. Whether quarterly IF.data selected indicators add value beyond the COSIF files.
5. Whether institution-level complaints have a stable enough current download path
   for phase two.

