# End-to-End Brazilian Banking Analytics Showcase

Public, portfolio-grade banking analytics product built from official Banco Central
do Brasil (BCB) data.

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

The complete source-to-mart data layer is implemented and certified. Official COSIF
schema/volume profiling, the stable top-15 population, five-series macro contract,
dlt/PostgreSQL landing, dbt staging/core/marts and the expanded Dagster graph all pass
against the frozen `202501–202603` official window. The next delivery layer is the
Power BI PBIP/TMDL semantic model and report.

- The official BCB document catalog confirms the bank-file publication inventory.
- The MVP analytical period is January 2025 through the latest published month.
- The MVP uses banks only and the current COSIF standard; earlier history and
  consolidated scopes are explicitly deferred.
- Checkpoint 0A is complete: the official catalog confirms 15 published MVP months
  from January 2025 through March 2026 and identifies one superseded December 2025
  file. Checkpoint 0B is complete from all 15 active official archives: 831,038 rows,
  zero malformed rows and one stable schema are preserved in committed evidence.
- Checkpoint 0C ranks document 4010 individual institutions by class-1 plus class-2
  assets in 202603, freezes a stable top 15 across all 15 months and passes all 11
  scope, coverage, cutoff and reconciliation controls. The decision is documented in
  [the total-assets and population checkpoint](docs/checkpoints/00c-total-assets-top15.md).
- Checkpoint 0D fixes the exact five-series macro registry and monthly semantics. A
  fresh bounded live retry returned all 75 expected observations; the later official
  warehouse certification passed.
- Checkpoint 0E passed 11/11 consolidation controls and froze the exact official
  load contract as `ready_for_official_warehouse_certification`. Its bounded drafts
  have since been resolved by the versioned reporting-line mapping. See
  [the final source-profile decision](docs/checkpoints/00e-source-profile-decision.md).
- The official 202501–202603 route is certified in an isolated PostgreSQL database:
  repeated dlt loads remained stable, all 214 expanded dbt nodes passed, the 31-asset
  Dagster job succeeded and all 225 top-15 total-assets values reconciled exactly. See
  [the official warehouse checkpoint](docs/checkpoints/11-official-warehouse-certification.md).
- Synthetic contract fixtures load idempotently through dlt into PostgreSQL 18. The
  independent smoke run and its strict non-production boundary are documented in
  [the fixture landing checkpoint](docs/checkpoints/01-fixture-landing.md).
- The fixture-backed dbt graph builds 24 models plus two governance seeds and passes
  188 tests. Its original core-only checkpoint is documented in
  [the dbt core checkpoint](docs/checkpoints/02-fixture-dbt-core.md).
- The fixture Dagster graph now materializes five dlt raw assets, 24 dbt models and
  two seeds with continuous lineage. Its original 16-asset checkpoint is documented in
  [the Dagster checkpoint](docs/checkpoints/03-fixture-dagster.md).
- Verified COSIF and SGS profiler outputs now map into the same production dlt
  contracts and were exercised in an isolated PostgreSQL integration test. The live
  502 boundary is documented in
  [the official adapter checkpoint](docs/checkpoints/04-official-landing-adapters.md).
- Dagster defaults safely to fixtures and can switch to fully specified official
  evidence without changing any of the 31 asset keys. The fail-closed behavior and
  live boundary are documented in
  [the source-mode checkpoint](docs/checkpoints/05-dagster-source-modes.md).
- A manual official-sample workflow independently acquires both source families and
  blocks every downstream step unless all evidence is complete. Its verified HTTP
  502 failure path is documented in
  [the sample-gate checkpoint](docs/checkpoints/06-official-sample-gate.md).
- The same run emits nine machine-readable live-readiness controls. Its retained CI
  failure remains useful hard-gate evidence; a later full-window local retry passed
  all nine controls without loading the warehouse. The contract is documented in
  [the readiness checkpoint](docs/checkpoints/07-live-readiness.md).
- Generated dbt docs describe all five source tables, 24 implemented models and two
  governance seeds. The original core-only catalog checkpoint is documented in
  [the dbt catalog checkpoint](docs/checkpoints/08-dbt-catalog.md).
- A presentation-ready [architecture guide](docs/architecture.md) consolidates the
  problem, inputs, defended stack, layer ERDs, quality controls and the exact
  implemented/planned boundary.
- Checkpoint 12 certifies seven top-level account assignments, twelve dimensional
  consumption objects, `214/214` dbt nodes and the 31-asset official Dagster run.
  The frozen handoff is documented in
  [the reporting-mart checkpoint](docs/checkpoints/12-reporting-marts.md) and
  [mart contract](contracts/mart-schema.yml).

Start with the [architecture and project guide](docs/architecture.md), the
[implementation plan](plan/README.md), the live
[source-profile status](docs/source-profile.md), the [operational runbook](docs/runbook.md),
and the latest [handover](HANDOVER.md).

Public-facing framing: **Where do Brazil's largest banks get their money, where do
they put it, and how has that changed under high interest rates?**

## Repository boundary

Code and original documentation will be released under MIT. BCB databases are
licensed under ODbL and will not be blanket-relicensed as MIT. Full source files will
be acquired at runtime and kept outside Git; public outputs will carry the required
BCB and ODbL attribution. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## License

Project code and original documentation: [MIT](LICENSE).
