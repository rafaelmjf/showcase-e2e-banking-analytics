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
- The initial analytical period is January 2021 through the latest published month.
- The 2025 COSIF redesign is treated as a first-class comparability boundary.

Start with the [implementation plan](plan/README.md).

## Repository boundary

Code and original documentation will be released under MIT. BCB databases are
licensed under ODbL and will not be blanket-relicensed as MIT. Full source files will
be acquired at runtime and kept outside Git; public outputs will carry the required
BCB and ODbL attribution. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## License

Project code and original documentation: [MIT](LICENSE).

