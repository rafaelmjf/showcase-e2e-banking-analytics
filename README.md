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

Planning and source profiling only. No production data pipeline or BI model has been
implemented yet.

- The official BCB balance-sheet bulk-download pattern is confirmed.
- A January 2026 banks file was profiled: 0.90 MB compressed, 6.12 MB expanded and
  49,364 balance rows.
- Bank files for January through March 2026 were reachable on 11 August 2026.
- The MVP analytical period is January 2025 through the latest published month.
- The MVP uses banks only and the current COSIF standard; earlier history and
  consolidated scopes are explicitly deferred.

Start with the [implementation plan](plan/README.md).

Public-facing framing: **Where do Brazil's largest banks get their money, where do
they put it, and how has that changed under high interest rates?**

## Repository boundary

Code and original documentation will be released under MIT. BCB databases are
licensed under ODbL and will not be blanket-relicensed as MIT. Full source files will
be acquired at runtime and kept outside Git; public outputs will carry the required
BCB and ODbL attribution. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## License

Project code and original documentation: [MIT](LICENSE).
