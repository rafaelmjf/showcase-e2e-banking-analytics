# Foundation checkpoint — official warehouse certification

Updated: 2026-08-11

## Objective

Execute the frozen checkpoint 0E evidence through official dlt, PostgreSQL, dbt and
Dagster; prove that repeated landing is identity-stable; and certify the canonical
core without allowing fixture contamination or implying that reporting marts exist.

## Isolated execution

The certification used PostgreSQL 18 database
`banking_official_202501_202603` on the existing healthy local container. The normal
fixture-backed `banking` database was not changed.

The exact source contract was:

- COSIF `BANCOS`, 202501–202603, 15 source checksums and 831,038 rows;
- documents 4010 and 4016 retained at landing, 4010 used analytically;
- five SGS series with 75 monthly observations;
- 202603 top-15 population held stable across all 15 months.

## Results

The direct official dlt run and the Dagster dlt run both completed successfully. The
second pass left every merge identity stable:

| Relation | Rows |
|---|---:|
| `raw_cosif.cosif_file_manifest` | 15 |
| `raw_cosif.cosif_balance_row` | 831,038 |
| `raw_macro.sgs_series_metadata` | 5 |
| `raw_macro.sgs_observation` | 75 |
| `raw_macro.sgs_fetch_manifest` | 5 |
| `analytics_core.cosif_file_manifest` | 15 |
| `analytics_core.account_balance` | 831,038 |
| `analytics_core.bank_period` | 2,589 |
| `analytics_core.cosif_account` | 1,056 |
| `analytics_core.macro_series` | 5 |
| `analytics_core.macro_observation` | 75 |

No raw or core fact-like row carried a fixture flag. Raw and core identities
reconciled exactly. All 225 checkpoint 0C top-15 member/month total-assets values
matched official core at a maximum absolute difference of BRL 0.00.

The official dbt build completed with `PASS=117 WARN=0 ERROR=0 SKIP=0`: 11 models and
106 tests. Official Dagster definitions validated, then `official_end_to_end`
succeeded in 3 minutes 19 seconds with run ID
`69dd1ce1-74e9-4ebb-85b5-af7c3fa155c0`.

## Machine-readable certification

`banking-data certify-official-warehouse` collects database counts, period/checksum
coverage, fixture flags, dlt load histories, raw/core reconciliation, checkpoint 0C
total assets, dbt results and the attached Dagster terminal result. It fails closed
if the database name is not the isolated target or any expected value changes.

All 11 controls passed. The retained result is
[official_warehouse_certification.csv](../../artifacts/official_warehouse_certification.csv).

## Boundary and next action

The official landing, staging and canonical core are certified. No reporting-line
mart or Power BI model is certified or built. Next, resolve the bounded credit,
deposit and equity mappings, implement dimensional marts, reconcile them to official
core and freeze `contracts/mart-schema.yml` before BI work begins.
