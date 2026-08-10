# 02 — Architecture

## Stack

| Layer | Technology | Rationale |
|---|---|---|
| Acquisition | Python 3.12 and dlt | Custom ZIP and REST sources, incremental state, schema contracts and load metadata |
| Warehouse | PostgreSQL 18 | Portable, open, sufficient for the expected volume and directly consumable by Power BI |
| Transformation | dbt Core with `dbt-postgres` | Transparent SQL, tests, contracts, lineage and docs |
| Orchestration | Dagster with `dagster-dlt` and `dagster-dbt` | Asset-centric lineage and observability across ingestion and transformation |
| Modelling | Canonical accounting core to Kimball marts | Source shape is periodic accounting observations, not a multi-system identity-resolution problem |
| Semantic layer | Power BI semantic model in PBIP/TMDL | Reviewable model definition and target-market fit |
| Testing | pytest, dlt load checks, dbt tests and semantic regression tests | Controls live beside the logic they validate |
| Packaging | uv, Docker Compose and GitHub Actions | Reproducible local and CI execution |

## Data flow

```text
BCB COSIF ZIP files ------------------┐
                                     ├─> dlt landing ─> dbt staging ─> canonical core
BCB SGS JSON/CSV macro series -------┘                                  │
                                                                        v
                                  reporting-line bridge + monthly context marts
                                                                        │
                                                                        v
                                               Power BI semantic model and report
```

Dagster materialises and observes each source, dlt resource, dbt model group,
reconciliation artifact and BI contract as an asset.

## PostgreSQL schemas

| Schema | Contents |
|---|---|
| `raw_cosif` | Append-preserved COSIF file rows plus dlt metadata |
| `raw_macro` | Native-frequency SGS observations and series metadata |
| `stg` | Typed, renamed, source-faithful models |
| `core` | Canonical current-standard institution, document, account and observation logic |
| `marts` | BI-facing dimensions, facts and monthly context |
| `audit` | File manifests, reconciliation results and data-quality outcomes |

## Key decisions

### dlt rather than Airbyte

BCB acquisition requires parameterised historical URLs, ZIP inspection, embedded
metadata lines, Portuguese decimal parsing, file checksums and explicit treatment of
reissued files. Python code is the clearest interface for those rules. dlt provides
state and loading without introducing a separate connector service and control UI.

Cost: fewer prebuilt UI demonstrations than Airbyte, and custom source code remains
our responsibility.

### dbt rather than SQLMesh for release one

Dagster can represent dbt models as native assets, and dbt supplies familiar tests,
contracts and documentation. SQLMesh offers strong environments, plans and audits,
but would overlap with Dagster's orchestration and asset state while adding another
new operating model.

Cost: no SQLMesh virtual environments or plan/apply demonstration.

### No Data Vault

The dominant grain is an official periodic statement identified by institution,
document, account and reporting date. Checksum-aware landing plus a current-standard
canonical core is sufficient for the MVP. A vault would add objects without solving a
real multi-source identity problem.

Cost: source-history logic must be explicit in manifests and canonical-selection
models rather than inherited from vault patterns.

### Preserve source evidence without MVP restatement analytics

Every file version is identified by source URL, checksum, generation date and
retrieval timestamp. Canonical models select the latest complete version. The MVP
exposes file lineage and active-version status but does not build a restatement fact,
bi-temporal mart or public restatement analysis.

### Native macro evidence plus a small monthly context

Source observations retain their published dates for lineage. The MVP exposes only a
small monthly context mart. Any non-monthly source must have one named alignment rule,
such as monthly average or month-end; no frequency is silently changed.

## Deliberately excluded from release one

- Airbyte
- SQLMesh
- Data Vault
- Cloud warehouse or Fabric Lakehouse
- Hosted Dagster
- Machine learning or causal inference
- DirectQuery
- Prudential-conglomerate comparison
- Pre-2025 COSIF history and taxonomy bridging
- Restatement analytics
