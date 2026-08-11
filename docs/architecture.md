# Brazilian Banking Analytics — architecture and project guide

Updated: 2026-08-11

## Problem statement

Brazilian banking disclosures contain the evidence needed to explain how institutions
fund themselves, deploy capital and change through different interest-rate and credit
conditions. The raw material is difficult to use directly: balances arrive as large
account-level files, account meaning is hierarchical, files can be republished, bank
and conglomerate scopes must not be mixed, and macro series have different units and
interpretation rules.

The public-facing question is intentionally simpler than the source:

> Where do Brazil's largest banks get their money, where do they put it, and how has
> that changed under high interest rates?

## Proposed solution

Build a reproducible analytical product that retains official evidence but exposes a
small governed banking vocabulary:

```mermaid
flowchart LR
    A["BCB COSIF bank files"] --> C["dlt evidence landing"]
    B["BCB SGS macro series"] --> C
    C --> D["dbt typed staging"]
    D --> E["dbt canonical core"]
    E --> F["Certified dimensional marts"]
    F --> G["Power BI semantic model (TMDL)"]
    G --> H["Banking Pulse + Compare Banks + Trust"]
```

The current implementation reaches the consumption layer end to end. Checkpoint 12
certifies the materialized top-15 population, four reporting lines, twelve mart objects
and exact account-level reconciliation; checkpoint 13 adds the version-controlled Power
BI PBIP/TMDL semantic model, sixteen governed measures and a three-page report bound
only to that frozen contract. The MVP is complete.

## Input data

### COSIF bank documents

The BCB catalog publishes one individual-bank file per reporting month. The MVP starts
in January 2025 to remain within the current COSIF standard and avoid a premature
cross-taxonomy bridge. Important source fields are:

| Field | Meaning in this project |
|---|---|
| `DATA_BASE` | Reporting month (`YYYYMM`) |
| `DOCUMENTO` | BCB document type; rank monthly 4010 and retain semiannual 4016 as excluded evidence |
| `CNPJ` / `NOME_INSTITUICAO` | Institution identity and source name |
| `CONTA` / `NOME_CONTA` | COSIF account code and description |
| `SALDO` | Locale-formatted balance in Brazilian reais |
| `COD_CONGL` / `NOME_CONGL` | Retained source context, not a license to sum scopes |
| `TAXONOMIA` | Source taxonomy context when present |

The acquisition manifest adds URL, SHA-256, source generation date, retrieval time,
completion state and row count. December 2025 currently has two published versions;
the later catalog record is selected deterministically. Full bodies remain outside
Git and retain the BCB ODbL boundary.

### Monthly macro context

The governed registry fixes five BCB SGS series from the beginning:

| Code | Theme | Native interpretation | MVP treatment |
|---|---|---|---|
| 4189 | Policy rate | Monthly Selic, annualized on a 252-business-day basis | Preserve native value; do not aggregate |
| 433 | Inflation | Monthly IPCA percentage change | Preserve monthly value; derive 12-month compounding later |
| 24363 | Activity | Unadjusted IBC-Br index | Level and year-over-year comparison only |
| 20539 | Credit | Month-end total credit portfolio stock | Never sum across months; compare levels/YoY |
| 21082 | Credit quality | Month-end total delinquency percentage | Percentage-point change, not additive aggregation |

Every observation retains its native date, exact decimal text/value, request URL and
retrieval timestamp. Macro relationships provide context and must not be presented as
causal explanations of bank performance.

## Architecture strategy and stack

| Layer | Choice | Why it fits |
|---|---|---|
| Acquisition | Python 3.12 + dlt | BCB files need custom ZIP/header/encoding semantics and SGS needs bounded API validation. dlt adds typed schema contracts, merge identities and load-package state without a service-heavy connector platform. |
| Warehouse | PostgreSQL 18 | Portable, transparent SQL, sufficient for the bounded volume and directly consumable by Power BI. It also makes local/CI parity straightforward. |
| Transformation | dbt Core + dbt-postgres | Explicit lineage, a frozen mart contract, 188 current tests, generated documentation and a mature Dagster integration. |
| Orchestration | Dagster + `dagster-dlt` + `dagster-dbt` | Models the platform as 31 observable assets. Fixture and official modes preserve identical keys, so operational source choice does not fracture lineage. |
| Consumption | Power BI PBIP/TMDL | Matches the portfolio's BI focus and allows governed measures, version-controlled metadata and a clear mart-only boundary. Implemented in checkpoint 13. |
| Packaging/CI | uv, Docker Compose, GitHub Actions | Locked Python resolution, PostgreSQL 18 parity and independently retained evidence for every checkpoint. |

### Why no Data Vault

Data Vault is useful when many independently changing source systems, business keys
and audit histories must be integrated. This MVP has one official source authority,
stable reporting identities and a short current-standard window. Checksum manifests
already preserve the required source evidence. Adding hubs, links and satellites
would increase navigation and transformation cost without solving a present problem.

The direct pattern—evidence landing, typed staging, canonical core, dimensional
marts—therefore demonstrates architectural judgment rather than a tool preference.
Restatement analytics or additional source families can trigger a new ADR later.

### Why dlt rather than Airbyte

Airbyte would add an always-on connector service while the difficult work remains
custom: locating the source header inside a ZIP, decoding CP1252, parsing Brazilian
decimals and enforcing catalog-selected file versions. dlt keeps that domain code
small and testable while still providing state, schema and merge behavior.

### Why dbt rather than SQLMesh

SQLMesh is a credible alternative, but dlt and Dagster already own ingestion and
orchestration state. Adding SQLMesh environments would introduce a third control
plane. dbt supplies the needed SQL contracts, tests, docs and asset integration with
less conceptual duplication for this project.

## Implemented layers

### Raw evidence landing

The five raw tables preserve source-shaped records and immutable acquisition context.
The relationships are logical lineage relationships; PostgreSQL foreign keys are not
required for ingestion.

```mermaid
erDiagram
    cosif_file_manifest ||--o{ cosif_balance_row : "source_checksum"
    sgs_series_metadata ||--o{ sgs_observation : "series_code"
    sgs_series_metadata ||--o{ sgs_fetch_manifest : "series_code"

    cosif_file_manifest {
        text source_checksum PK
        text source_period
        date source_generated_at
        timestamptz retrieved_at_utc
        text status
        bigint row_count
        boolean fixture
    }
    cosif_balance_row {
        text source_checksum PK
        bigint file_row_number PK
        text cnpj
        text conta
        text saldo_raw
        decimal saldo
    }
    sgs_series_metadata {
        text series_code PK
        text unit
        text observation_semantics
        text monthly_alignment
    }
    sgs_observation {
        text series_code PK
        date source_observation_date PK
        text report_month
        text value_raw
        decimal value
    }
    sgs_fetch_manifest {
        text series_code PK
        date requested_start_date PK
        date requested_end_date PK
        boolean fixture PK
        text status
        bigint response_count
    }
```

### Typed staging

Staging is deliberately boring: rename Portuguese source columns, apply PostgreSQL
types, convert `YYYYMM` to a month date and expose lineage fields consistently. It
does not map COSIF accounts, aggregate balances or reinterpret macro values.

| Model | Grain and responsibility |
|---|---|
| `stg_cosif_file_manifest` | One typed file version/checksum |
| `stg_cosif_balance_row` | One typed physical account row inside a checksum |
| `stg_sgs_series_metadata` | One governed series definition |
| `stg_sgs_observation` | One native series/date observation |
| `stg_sgs_fetch_manifest` | One bounded request outcome |

### Canonical core

```mermaid
erDiagram
    cosif_file_manifest ||--o{ account_balance : "selected source_checksum"
    bank_period ||--o{ account_balance : "report_month + institution_cnpj"
    cosif_account ||--o{ account_balance : "account_code"
    macro_series ||--o{ macro_observation : "series_code"
    reporting_line_mapping }o--|| cosif_account : "account_code"

    cosif_file_manifest {
        text source_checksum PK
        text source_period
        boolean is_selected
        bigint declared_row_count
    }
    account_balance {
        text source_checksum PK
        bigint file_row_number PK
        date report_month
        text institution_cnpj
        text account_code
        decimal balance_amount
        boolean is_fixture
    }
    bank_period {
        text bank_period_key PK
        date report_month
        text institution_cnpj
        text institution_name
    }
    cosif_account {
        text account_code PK
        text account_name
    }
    macro_series {
        text series_code PK
        text display_name
        text unit
        text derived_metric
    }
    macro_observation {
        text series_code PK
        date source_observation_date PK
        date report_month
        decimal value
        boolean is_fixture
    }
    reporting_line_mapping {
        text account_code PK
        text reporting_line_key
        text mapping_version
        integer presentation_multiplier
    }
```

`cosif_file_manifest` retains all landed versions and marks one complete version per
period. `account_balance` only contains rows from that selected version. `bank_period`
and `cosif_account` are current canonical entities. `reporting_line_mapping` promotes
the versioned seven-account governance seed into the canonical layer. A Type-2 bank
history is unnecessary for the unchanged 15-month names. Macro definitions and observations
remain separate so semantic rules are governed rather than embedded in a generic
value column.

### Certified consumption marts

```mermaid
erDiagram
    dim_bank ||--o{ fact_account_balance : bank_key
    dim_date ||--o{ fact_account_balance : month_key
    dim_cosif_account ||--o{ fact_account_balance : account_key
    dim_source_file ||--o{ fact_account_balance : source_file_key
    dim_bank ||--o{ fact_reporting_line_balance : bank_key
    dim_date ||--o{ fact_reporting_line_balance : month_key
    dim_reporting_line ||--o{ fact_reporting_line_balance : reporting_line_key
    dim_source_file ||--o{ fact_reporting_line_balance : source_file_key
    dim_cosif_account ||--o{ bridge_account_reporting_line : account_key
    dim_reporting_line ||--o{ bridge_account_reporting_line : reporting_line_key
    dim_macro_series ||--o{ fact_macro_observation : macro_series_key
    dim_date ||--o{ fact_macro_observation : month_key
    dim_macro_series ||--o{ fact_monthly_economic_context : macro_series_key
    dim_date ||--o{ fact_monthly_economic_context : month_key
```

`dim_bank` materializes the frozen top 15; `dim_cosif_account`, `dim_reporting_line`,
`dim_document`, `dim_macro_series`, `dim_date` and `dim_source_file` provide governed
descriptive and provenance attributes. `bridge_account_reporting_line` preserves the
seven exact account assignments. `fact_account_balance` supports source-account
drill-through, `fact_reporting_line_balance` exposes four audited bank-month lines,
`fact_macro_observation` preserves native series dates, and
`fact_monthly_economic_context` supplies authored monthly alignment without causal
interpretation. The full ordered schema is frozen in `contracts/mart-schema.yml`.

## Orchestration and operational gates

The default `fixture_end_to_end` job materializes all five raw assets followed by 24
dbt models and two governance seeds. `BANKING_SOURCE_MODE=official` exposes
`official_end_to_end` with the same keys, but only when every persisted evidence path
and macro bound is explicit. The job uses deterministic in-process execution because
multiprocess code-location imports can race while dlt initializes shared local
pipeline schema storage on Windows.

Before an official load, `assess-readiness` publishes eight source controls and one
overall decision. The retained CI run demonstrates the HTTP-502 failure path and
skips PostgreSQL, dbt and Dagster instead of loading partial evidence. After service
recovery, a full-window local retry passed all nine controls; downstream live
execution remains a separate certification gate.

Checkpoint 0E adds a second, non-mutating consolidation gate. Its 11 controls pin the
catalog, runtime archives, COSIF/SGS profiles, fixed population, document scope and
bounded reporting-line draft. That historical source contract led to the isolated
warehouse certification and then the versioned mart mapping. Checkpoint 12 now
freezes the twelve-object consumption contract after all thirteen reporting-mart
controls passed.

## Quality strategy

Current automated evidence includes:

- strict dlt column/type contracts and deterministic merge identities;
- checksum, ZIP CRC, member, encoding, delimiter, header and period validation;
- exact five-series registry and bounded monthly completeness controls;
- source, staging and core null/unique/accepted-value tests;
- file manifest versus account-row reconciliation;
- synthetic accounting identity reconciliation;
- macro grain and continuity tests;
- stable raw-to-dbt asset keys and executable Dagster checks;
- machine-readable ready/blocked controls before live mutation.
- exact seven-account reporting mapping and non-overlap controls;
- stable 15-bank by 15-month population coverage;
- account-level to reporting-line reconciliation and ordered contract-schema checks.

The current dbt graph contains 24 models, two seeds and 188 tests. Both fixture and
official builds pass `214/214`; the official mart certification additionally proves
zero fixture rows, all 900 bank-month-line combinations and exact BRL reconciliation.

## Important observations and challenges

1. **Official service availability:** local and GitHub runners previously received
   HTTP 502 from both source families. The services later recovered and supplied a
   complete local profile. HTTP 5xx remains unknown availability, never evidence that
   a period is absent.
2. **Headers are not necessarily row one:** COSIF files include metadata lines before
   the semicolon-delimited header. Acquisition searches for the required field set
   and records the header line number.
3. **Encoding and decimals are source semantics:** observed files use CP1252 and
   Brazilian values such as `1.234,56`. Raw text is retained beside exact `Decimal`
   values; floating point is not used.
4. **Republished months:** checksum is the immutable version identity. Catalog
   publication order plus generation/retrieval timestamps produces one deterministic
   selected version, while all manifests remain auditable.
5. **Scope cannot be casually summed:** individual institutions and consolidated or
   prudential scopes represent different populations. The MVP admits only individual
   bank files.
6. **Profitability is deferred:** COSIF result accounts reset in June and December;
   balance-sheet reporting lines are safer for the first release.
7. **Monthly macro values are heterogeneous:** rates, percentages, indexes and stocks
   cannot share one aggregation rule. The registry authors treatment per series.
8. **Generated artifacts matter:** clean Linux CI exposed terminal-width and missing
   dbt-manifest assumptions that local Windows state had hidden. Tests now avoid
   rendered CLI assertions and declare when a generated manifest is required.

## Implemented versus planned boundary

| Capability | State |
|---|---|
| Official catalog and active-version resolution | Implemented and live-verified |
| COSIF/SGS acquisition, profiling and readiness code | Implemented; COSIF 0B and a bounded live readiness retry passed |
| Strict dlt landing and PostgreSQL path | Fixture and mocked-official integration verified |
| dbt staging/core/marts/tests/docs | Implemented; fixture and official builds pass 214/214 |
| Dagster fixture and official modes | Implemented as a stable 31-asset graph |
| Full official Dagster + dbt run | Certified for 202501–202603; 214/214 dbt nodes and the 31-asset job passed |
| Total-assets definition and stable top-15 population | Profiled and certified in checkpoint 0C |
| Final source-profile decision | Complete; 11/11 controls passed |
| Reporting-line mapping and dimensional marts | Certified under mapping version `2026-08-11-v1` |
| Mart schema contract | Frozen for all twelve consumption objects |
| Power BI TMDL, pages and trust panel | Implemented and verified live (checkpoint 13) |

## Where to continue

1. Start with [the current handover](../HANDOVER.md) for the latest gate and exact
   retry command.
2. Use [the implementation plan](../plan/README.md) for scope and work-package
   sequencing.
3. Use [the source profile](source-profile.md) for live findings and blockers.
4. Generate the dbt catalog using the commands in [the dbt README](../dbt/README.md).
5. Review [third-party notices](../THIRD_PARTY_NOTICES.md) before publishing any BCB
   derivative data.
