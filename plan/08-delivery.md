# 08 — Delivery

## Handoff boundary

```text
DATA LAYER                                    BI LAYER
dlt + dbt + Dagster                          Power BI + semantic tests + docs
        │                                                   ▲
        └──────── contracts/mart-schema.yml ────────────────┘
```

The mart contract contains table grain, every column and type, keys, nullability,
business meaning, scope rules, comparability flags, reference row counts and source
freshness. Changes after freezing are announced as contract changes.

## Phases

### Phase 0 — Source profiling and decision closure

Profile 24 consecutive months, both initial segments, duplicate scope, document codes,
the 2025 boundary and all macro metadata. Decide the primary comparison grain.

**Evidence:** source-profile table, schema observations, volume estimate and first
taxonomy-mapping coverage.

### Phase 1 — Data layer

Implement dlt sources, PostgreSQL landing, dbt core/marts/tests, Dagster assets,
reconciliation and the frozen mart contract.

**Evidence:** dlt load packages, dbt lineage, Dagster asset run, reconciliation and
restatement examples.

### Phase 2 — Semantic model and report

Author measure contracts, build TMDL, implement the three report pages and validate
filter-context behavior.

**Evidence:** report pages, source drill-through, measure contract and model diagram.

### Phase 3 — Regression and governance

Complete semantic regression tests, capture deliberate failures, generate curated
documentation and publish the license/coverage boundary.

**Evidence:** failing-then-fixed controls, project guide, KPI catalog and decision
records.

### Phase 4 — Portfolio publication

Add the case study to `rmjf-portfolio` only after the data and BI evidence are complete.

## Work packages

| ID | Package | Blocks on | Layer |
|---|---|---|---|
| WP0 | 24-month source profile | — | data |
| WP1 | Source and macro registries | WP0 | data |
| WP2 | dlt COSIF ingestion | WP1 | data |
| WP3 | dlt macro ingestion | WP1 | data |
| WP4 | dbt staging and file-version core | WP2–WP3 | data |
| WP5 | Institution and COSIF taxonomy core | WP4 | data |
| WP6 | Reporting-line mapping and marts | WP5 | data |
| WP7 | Reconciliation and quality evidence | WP4–WP6 | data |
| WP8 | Dagster asset graph | WP2–WP7 | data |
| WP9 | Mart contract and BI handoff | WP6–WP7 | shared |
| WP10 | Measure contracts and TMDL | WP9 | BI |
| WP11 | Three report pages | WP10 | BI |
| WP12 | Semantic regression tests | WP10 | BI |
| WP13 | Curated documentation | WP11–WP12 | shared |
| WP14 | Portfolio case study | WP13 | shared |

## Definition of project done

1. A clean local environment reproduces the official bounded data sample.
2. Source, canonical and mart balances reconcile for the certified population.
3. The 2025 taxonomy boundary is mapped or visibly non-comparable.
4. Dagster materialises the fixture pipeline and bounded live sample.
5. Power BI consumes only the frozen marts and passes regression tests.
6. The report includes context, institution comparison and trust pages.
7. Documentation explains the project to a newcomer without requiring code reading.
8. MIT and ODbL boundaries are correctly published.

## Later extensions

- Additional institution segments
- IF.data selected regulatory indicators
- BCB complaint rankings
- Leasing and vehicle-finance market series
- SQLMesh comparison branch or migration experiment
- Hosted Dagster deployment

