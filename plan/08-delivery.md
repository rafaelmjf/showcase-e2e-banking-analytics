# 08 — Delivery

## Handoff boundary

```text
DATA LAYER                                    BI LAYER
dlt + dbt + Dagster                          Power BI + semantic tests + docs
        │                                                   ▲
        └──────── contracts/mart-schema.yml ────────────────┘
```

The mart contract contains table grain, columns/types, keys, nullability, business
meaning, mapping coverage, reference row counts and source freshness. Changes after
freezing are announced as contract changes.

## Phases

### Phase 0 — Focused source profile

Profile every available `BANCOS` month from January 2025 onward and validate the five
monthly macro themes. Identify the top-15 population and only the reporting lines
needed by the two report pages.

**Evidence:** source profile, volume table, schema observations, institution/account
coverage and draft reporting-line mapping.

Phase 0 is delivered through independently reviewable checkpoints. Do not roll a
failed or unverified checkpoint into the next one:

| Checkpoint | Deliverable | Exit gate |
|---|---|---|
| 0A | COSIF bank-file availability inventory | Tested catalog and probe commands, live catalog with zero parse errors, active versions resolved, handover updated |
| 0B | Downloaded-file schema and volume profile | Checksums, row counts, schemas and document/institution/account coverage published |
| 0C | Total-assets and top-15 decision | Account mapping reconciled and reproducible latest-complete-period ranking published |
| 0D | Five-series macro profile | Official metadata, frequency, units and monthly alignment rules validated |
| 0E | Source-profile decision | Findings, bounded reporting-line draft and implementation-readiness decision published |

At every exit gate: run the relevant tests, update `HANDOVER.md`, commit the evidence,
check goal usage, and stop for review before consuming the next package.

### Phase 1 — Data layer

Implement dlt sources, PostgreSQL landing, dbt core/marts/tests, Dagster assets,
reconciliation and the frozen mart contract.

**State:** complete and certified in checkpoint 12.

**Evidence:** dlt load packages, dbt lineage, Dagster asset run, reconciliation,
mapping coverage and active-file manifest.

### Phase 2 — Semantic model and report

Author measure contracts, build TMDL, implement Banking Pulse and Compare Banks, and
add the shared trust panel.

**Evidence:** two report pages, trust panel, source drill-through, measure contracts
and semantic-model diagram.

### Phase 3 — Regression and governance

Complete semantic regression tests, capture deliberate failures, generate curated
documentation and publish the license/coverage boundary.

### Phase 4 — Portfolio publication

Add the case study to `rmjf-portfolio` after the evidence and report are complete.

Future dataset additions begin only after the MVP definition of done and use the
prioritised gates in [09-future-enhancements.md](09-future-enhancements.md).

## Work packages

| ID | Package | Blocks on | Layer |
|---|---|---|---|
| WP0 | January 2025+ bank source profile | — | data |
| WP1 | Source and monthly macro registries | WP0 | data |
| WP2 | dlt COSIF bank ingestion | WP1 | data |
| WP3 | dlt macro ingestion | WP1 | data |
| WP4 | dbt staging and active-file selection | WP2–WP3 | data |
| WP5 | Current-standard bank/account core | WP4 | data |
| WP6 | Reporting-line mapping, top-15 population and marts | WP5 | data |
| WP7 | Reconciliation and quality evidence | WP4–WP6 | data |
| WP8 | Dagster asset graph | WP2–WP7 | data |
| WP9 | Mart contract and BI handoff | WP6–WP7 | shared |
| WP10 | Measure contracts and TMDL | WP9 | BI |
| WP11 | Two pages and trust panel | WP10 | BI |
| WP12 | Semantic regression tests | WP10 | BI |
| WP13 | Curated documentation | WP11–WP12 | shared |
| WP14 | Portfolio case study | WP13 | shared |

## Definition of MVP done

1. A clean local environment reproduces all available official bank months from
   January 2025 onward.
2. Source, canonical and mart balances reconcile for the certified reporting lines.
3. Top-15 membership is reproducible and stable across the report period.
4. Dagster materialises the fixture and frozen full-window official graphs.
5. Power BI consumes only frozen marts and passes regression tests.
6. Banking Pulse, Compare Banks and the trust panel are complete.
7. Documentation explains the project without requiring COSIF knowledge.
8. MIT and ODbL boundaries are correctly published.
