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
| [09-future-enhancements.md](09-future-enhancements.md) | Prioritised BCB dataset extensions after the MVP | shared |

## Standing decisions

1. Start with **banks only** and select a stable top-15 comparison set using total
   assets in the latest complete source period.
2. Cover **January 2025 through the latest published period**. Pre-2025 history and
   taxonomy bridging are later enhancements.
3. Include a small, monthly macroeconomic context set from the first release.
4. Keep checksum and load-manifest evidence, but do not build restatement analytics
   or a bi-temporal consumption model in the MVP.
5. Model directly into a canonical core and dimensional marts. Do not use Data Vault
   when one official source family and stable reporting keys do not justify it.
6. Keep native source observations for lineage but expose only authored monthly
   macro context to the MVP.
7. Use two decision-grade report pages plus a compact trust panel. Do not build a COSIF account
   browser disguised as a product.
8. Lead with understandable banking questions; COSIF is the evidence layer, not the
   public headline.
9. Do not claim causation from macroeconomic correlations.

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

## Decisions closed for the MVP

1. Primary scope: individual bank files only.
2. Time range: January 2025 onward.
3. Comparison population: latest-period top 15 by total assets, held stable over the
   report period.
4. Report: two pages plus a trust panel.
5. Stack: dlt, PostgreSQL, dbt, Dagster and Power BI.

## Decisions still requiring profiling

1. Which current-standard COSIF accounts safely define the small set of public
   reporting lines.
2. Whether all months from January 2025 are comparable within the current standard.
3. The exact monthly macro series and aggregation rules.
4. Whether institution name/CNPJ history needs a Type-2 dimension within the short
   MVP period.
