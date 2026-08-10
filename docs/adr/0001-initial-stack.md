# ADR 0001: Use dlt, PostgreSQL, dbt and Dagster

- Status: accepted for initial implementation
- Date: 2026-08-11

## Decision

- Python 3.12 and uv for the project runtime.
- dlt for COSIF file and SGS API acquisition, state and landing.
- PostgreSQL 18 for raw, canonical, audit and mart schemas.
- dbt Core with `dbt-postgres` for transformations, contracts, tests and docs.
- Dagster with `dagster-dlt` and `dagster-dbt` for local asset orchestration.
- Power BI Import mode with PBIP/TMDL for the semantic and report layers.
- Docker Compose and GitHub Actions for reproducibility.

## Context

The procurement showcase already demonstrates bespoke Python ingestion, PostgreSQL,
dbt, Data Vault and Airflow. This project should show different engineering choices
without turning stack novelty into unnecessary risk.

BCB sources are public parameterised files and APIs with domain-specific parsing and
revision semantics. They benefit from code-first ingestion more than from a general
connector platform. The final consumer remains Power BI, so a conventional relational
warehouse and stable consumption contract are valuable.

## Alternatives

### Airbyte

Rejected for release one. It provides a strong connector platform and UI, but these
sources still require custom URL discovery, ZIP parsing, embedded metadata handling
and revision logic. Running Airbyte beside Dagster would add operational weight and a
second orchestration surface without removing the custom code.

### SQLMesh

Rejected for release one. Its plan/apply workflow, audits and virtual environments are
valuable, but adopting SQLMesh together with dlt and Dagster would introduce three
stateful control planes. dbt's first-class Dagster integration, contracts and docs fit
the evidence requirements better for the initial build.

### DuckDB

Rejected as the primary warehouse. It would simplify local analytics, but PostgreSQL
offers a smoother Power BI connection and clearer multi-process behavior for Dagster.

## Cost

PostgreSQL is reused from the prior showcase and therefore does not demonstrate a new
warehouse. dbt is also retained. The differentiation comes from dlt, Dagster, direct
dimensional modelling, revision-aware periodic reporting and the COSIF taxonomy
boundary. Airbyte and SQLMesh experience is not claimed by this release.

