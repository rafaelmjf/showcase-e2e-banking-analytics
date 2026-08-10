# 05 — Transformation and orchestration

**Owner: data layer. This file plus 03 and 04 is the implementation brief.**

## dlt source layout

```text
src/banking_analytics/
  sources/
    cosif.py          # URL discovery, ZIP validation, metadata and balance rows
    sgs.py            # verified series registry and native observations
  pipelines/
    cosif.py          # dlt pipeline configuration and destination
    macro.py
  quality/
    manifests.py      # checksum, schema and source-period controls
```

### COSIF resources

- `cosif_file_manifest`: one row per attempted source URL and checksum.
- `cosif_balance_row`: parsed source rows with file lineage.
- `cosif_schema_observation`: columns, encoding, delimiter and source metadata seen
  in each file.

Extraction is metadata-driven by period and segment. A file is downloaded to a
temporary path, checksummed, inspected, streamed as rows and retained in the warehouse
through its manifest. A checksum already marked complete is skipped idempotently.

### Macro resources

- `sgs_series_metadata`: one verified source definition per SGS code.
- `sgs_observation`: one native-frequency observation.
- `sgs_fetch_manifest`: request window, response count and retrieval status.

The authored series registry is a contract, not a loose list of codes. The pipeline
fails closed if returned metadata conflicts with the expected title, unit or
frequency.

## dlt rules

1. Preserve raw source values and add typed values; never replace the original text.
2. Use append-preserving raw tables. Canonical selection happens in dbt.
3. Treat file checksum and source-generated date as source version evidence.
4. Set schema contracts after the profiling spike; unexpected columns initially
   alert, and destructive schema changes fail.
5. Publish dlt load-package identifiers into audit models.
6. Do not rely only on dlt incremental cursors for COSIF files because an older
   reporting period can be reissued.

## dbt project layout

```text
dbt/
  models/
    staging/
      cosif/
      macro/
    core/
    marts/
    audit/
  seeds/
    macro_series_registry.csv
    reporting_lines.csv
    cosif_mapping_overrides.csv
  macros/
  tests/
```

### Staging

- One model per landed resource.
- Explicit UTF/legacy encoding and locale conversions.
- Original and parsed balances survive together.
- Document, institution, account and reporting-scope fields remain source-faithful.
- No account is filtered because it is unmapped.

### Core

- Select active file versions deterministically.
- Detect and publish restatements.
- Build effective-dated institution and account versions.
- Apply only reviewed account-to-reporting-line mappings.
- Retain a reason for every non-comparable cross-taxonomy item.

### Marts

- Publish only contract-governed dimensions, facts and bridges.
- Aggregate reporting lines reconcile to account detail.
- Keep additive components in SQL; governed ratios remain Power BI measures.
- Produce `contracts/mart-schema.yml` from actual database metadata plus authored
  descriptions.

## Dagster asset graph

```text
discover_cosif_files -> cosif_dlt_assets -------┐
                                                ├-> dbt_staging -> dbt_core -> dbt_marts
verify_macro_registry -> macro_dlt_assets ------┘                         │
                                                                           ├-> reconciliation_assets
                                                                           └-> mart_contract
```

- Use `dagster-dlt` so dlt resources appear as assets.
- Use `dagster-dbt` so dbt models and tests appear in the same lineage graph.
- Partition COSIF acquisition by source period and segment.
- Partition macro acquisition by series and date window where practical.
- Add freshness checks based on each source's publication calendar, not a universal
  daily expectation.
- The public deliverable is a reproducible local Dagster deployment and captured
  successful run, not a claim of hosted uptime.

## Minimum tests

| Control | Layer |
|---|---|
| URL and expected-period validation | acquisition |
| ZIP integrity, checksum and exact-once completed manifest | dlt |
| Source header and locale parsing | pytest/dlt |
| Unique canonical accounting grain | dbt core |
| One active source version per period and segment | dbt audit |
| Source balance to canonical balance reconciliation | dbt audit |
| Account-detail to reporting-line reconciliation | dbt audit |
| No cross-scope double count | dbt marts |
| Mapping coverage and non-comparable status completeness | dbt marts |
| Macro series metadata and native frequency | dlt/dbt |

## Definition of done for the data layer

1. A clean PostgreSQL database can acquire fixtures, land them and build all marts.
2. A bounded official sample covers at least 24 consecutive reporting months and both
   sides of the 2025 taxonomy boundary.
3. dlt and dbt tests pass; at least one seeded defect is shown failing and then fixed.
4. Dagster materialises the complete fixture asset graph successfully.
5. Reconciliation, mapping coverage, source freshness and restatement evidence are
   exported.
6. dbt docs and the frozen `contracts/mart-schema.yml` are generated.

## What the data layer must not do

- Hide unmapped accounts.
- Combine incompatible reporting scopes.
- Compute naive profitability from result accounts that reset during the year.
- Convert correlation into causal classification.
- Modify or delete prior raw file versions.

