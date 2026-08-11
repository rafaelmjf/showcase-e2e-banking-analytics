# Checkpoint 12 — certified reporting marts

Date: 2026-08-11

## Decision

The source-dependent reporting-line mapping, stable-population dimensional marts and
data-to-BI contract are complete. The official `202501–202603` warehouse passed all
thirteen reporting-mart controls in isolated PostgreSQL 18 database
`banking_official_202501_202603`. Power BI may bind only to the twelve objects in
`contracts/mart-schema.yml`; raw, staging and core schemas are not consumption APIs.

## Frozen reporting-line mapping

Mapping version `2026-08-11-v1` assigns seven mutually exclusive top-level COSIF
accounts:

| Reporting line | Certified account components |
|---|---|
| Total assets | `1000000009`, `2000000008` |
| Credit portfolio | `1600000007`, `1700000000`, `1810000000` |
| Deposits | `4100000009` |
| Equity | `6000000004` |

The BCB COSIF account pages identify 1.6 as credit operations, 1.7 as leasing, 4.1
as deposits and class 6 as equity. The BCB credit-risk accounting rules also treat
leasing and other credit-characteristic operations alongside credit exposures. The
committed mapping retains these source URLs and preserves the earlier 0E draft as
historical decision evidence.

## Implemented boundary

The dbt project now contains 24 models, two governance seeds and 188 tests. Its
twelve consumption objects are seven dimensions, one account-to-line bridge and four
facts. The official build produced:

| Object | Rows |
|---|---:|
| `dim_bank` | 15 |
| `dim_cosif_account` | 1,056 |
| `dim_reporting_line` | 4 |
| `dim_document` | 2 |
| `dim_macro_series` | 5 |
| `dim_date` | 15 |
| `dim_source_file` | 15 |
| `bridge_account_reporting_line` | 7 |
| `fact_account_balance` | 121,092 |
| `fact_reporting_line_balance` | 900 |
| `fact_macro_observation` | 75 |
| `fact_monthly_economic_context` | 75 |

The same graph also passed `214/214` in the fixture database. Fixture-only fallback
membership keeps mechanical CI useful while official-only coverage tests remain
conditional and explicit.

## Orchestration certification

The expanded graph resolves 31 assets: five raw dlt outputs, 24 dbt models and two
governance seeds. It emits 171 Dagster asset checks. A retained multiprocess attempt,
run `ea6564ef-5aab-492f-b0d8-bb2a8e98bc80`, exposed a Windows race while two workers
initialized shared dlt schema-storage paths. The job now uses deterministic
in-process execution; asset keys and dependencies are unchanged.

After that hardening, `official_end_to_end` succeeded in 3 minutes 7 seconds with run
ID `8dff5096-2d50-418c-a8a7-8758c7ed63f4`. Its run-specific dbt artifact contains 24
successful models, two successful seeds and 188 passing tests (`214/214`). Replayed
official loads retained the same business identities and mart row counts.

## Machine-readable certification

`artifacts/reporting_mart_certification.csv` contains thirteen passing controls:

1. isolated official database;
2. exact counts for all twelve consumption objects;
3. exact seven-account mapping and mapping version;
4. zero fixture-labelled official mart rows;
5. 15-bank × 15-month stable population coverage;
6. all four reporting lines for every bank-month (`900` rows);
7. exact account-to-reporting-line reconciliation;
8. `225/225` total-assets reconciliation to checkpoint 0C at BRL `0.00` maximum
   difference;
9. five-series × 15-month macro context coverage;
10. complete `214/214` dbt result;
11. ordered warehouse schema equality with the twelve-object contract;
12. successful expanded Dagster run identity;
13. overall `reporting_marts_certified` decision.

Artifact SHA-256:
`DDA79FF2303743070F94910730CA3A967AFB4B8377DA601608EA03311A43F5EE`.

## Next boundary

The data layer is complete for the MVP. The next work package is the version-controlled
Power BI PBIP/TMDL semantic model, measures, two report pages and compact trust panel,
using only the frozen mart contract.
