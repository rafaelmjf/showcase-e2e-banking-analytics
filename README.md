# End-to-End Brazilian Banking Analytics Showcase

Planning scaffold for a public, portfolio-grade banking analytics product built from
official Banco Central do Brasil (BCB) data.

The project will combine institution-level COSIF account balances with a compact
macroeconomic context layer. It is intended to demonstrate source acquisition,
revision-aware ingestion, accounting hierarchy modelling, dimensional marts,
orchestration, data-quality controls, a governed Power BI semantic model, and clear
public documentation.

## Planned stack

| Layer | Technology |
|---|---|
| Acquisition and landing | Python 3.12 + dlt |
| Warehouse | PostgreSQL 18 |
| Transformation and tests | dbt Core + dbt-postgres |
| Orchestration | Dagster with `dagster-dlt` and `dagster-dbt` |
| Semantic model and report | Power BI, PBIP and TMDL |
| Packaging and CI | uv, Docker Compose and GitHub Actions |

The stack deliberately differs from the procurement showcase while remaining
coherent. Airbyte and SQLMesh were evaluated but are not in the initial build; the
reasoning is recorded in [ADR 0001](docs/adr/0001-initial-stack.md).

## Current status

WP0 source profiling is in progress. The acquisition profilers and a fixture-backed
dlt/PostgreSQL landing, dbt staging/core and Dagster asset graph are implemented; no
certified live landing, reporting marts or BI model has been completed yet.

- The official BCB document catalog confirms the bank-file publication inventory.
- The MVP analytical period is January 2025 through the latest published month.
- The MVP uses banks only and the current COSIF standard; earlier history and
  consolidated scopes are explicitly deferred.
- Checkpoint 0A is complete: the official catalog confirms 15 published MVP months
  from January 2025 through March 2026 and identifies one superseded December 2025
  file. Checkpoint 0B's checksum/ZIP/schema profiler is implemented and tested, and
  is waiting for recovery of direct file access after HTTP 502.
- Checkpoint 0D fixes the exact five-series macro registry and monthly semantics;
  live SGS materialization is also waiting for recovery from HTTP 502.
- Synthetic contract fixtures load idempotently through dlt into PostgreSQL 18. The
  independent smoke run and its strict non-production boundary are documented in
  [the fixture landing checkpoint](docs/checkpoints/01-fixture-landing.md).
- The fixture-backed dbt graph builds 11 staging/core models and passes 106 tests.
  Its scope and official-data boundary are documented in
  [the dbt core checkpoint](docs/checkpoints/02-fixture-dbt-core.md).
- The fixture Dagster graph materializes five dlt raw assets and 11 dbt assets with
  continuous lineage. Its independently reproduced boundary is documented in
  [the Dagster checkpoint](docs/checkpoints/03-fixture-dagster.md).

Start with the [implementation plan](plan/README.md), the live
[source-profile status](docs/source-profile.md), and the latest [handover](HANDOVER.md).

Public-facing framing: **Where do Brazil's largest banks get their money, where do
they put it, and how has that changed under high interest rates?**

## Repository boundary

Code and original documentation will be released under MIT. BCB databases are
licensed under ODbL and will not be blanket-relicensed as MIT. Full source files will
be acquired at runtime and kept outside Git; public outputs will carry the required
BCB and ODbL attribution. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## License

Project code and original documentation: [MIT](LICENSE).
