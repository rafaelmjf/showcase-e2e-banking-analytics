# Handover

Updated: 2026-08-11

## Current state

The complete source-to-mart data layer is implemented and certified. WP0 checkpoints
0A through 0E, the isolated official warehouse, the final four-line COSIF mapping,
twelve dimensional consumption objects and the frozen mart contract are preserved as
repository evidence. PostgreSQL database `banking_official_202501_202603` contains
the certified `202501–202603` official build; the fixture database remains separate.
The dbt graph now contains 24 models, two governance seeds and 188 tests. Dagster
exposes five raw plus 26 dbt assets under the same 31 keys in fixture and official
modes, and official mode still fails construction when any evidence input is absent.
The version-controlled Power BI PBIP/TMDL layer is now implemented and verified against
the certified official warehouse, binding only to the twelve mart-contract objects.
A manual bounded official-sample workflow hard-gates the complete live route. Its
retained CI run demonstrates the blocked path; after BCB recovery, the full
202501–202603 local window passed all nine readiness controls without mutating the
warehouse.
The same frozen evidence passed both the core-only certification and the expanded
reporting-mart certification.
Generated dbt docs now describe every implemented source and model and are retained
as a CI artifact.
`docs/architecture.md` now provides the newcomer-facing project narrative and ERDs.
`docs/runbook.md` now provides the complete fixture/live recovery and evidence path.

The chosen stack remains dlt + PostgreSQL + dbt + Dagster + Power BI. The MVP is now
deliberately focused on individual bank files from January 2025 onward, a stable top-15
comparison population, five monthly macro themes, two report pages and a trust panel.

The official catalog currently contains 454 records, 453 active periods and one
superseded file version. The MVP range has 15 published months from 202501 through
202603. December 2025 has two catalog entries; the later 2026-04-01 publication is
selected deterministically as active.

Verification completed:

- `uv run --locked ruff check src tests` — passed;
- `BANKING_RUN_POSTGRES_TESTS=1 uv run --locked pytest` — 68 passed;
- 15/15 official COSIF archives downloaded and profiled with zero errors;
- all five SGS profiles completed the 202501–202603 window with 75 observations;
- the combined nine-control readiness assessment reported `ready`;
- the final 11-control source-profile assessment reported
  `ready_for_official_warehouse_certification`;
- all 11 official warehouse certification controls passed;
- official and fixture dbt both passed `214/214` expanded nodes;
- all 13 reporting-mart controls passed with 900 complete bank-month-line rows,
  exact account reconciliation and zero fixture contamination;
- expanded official Dagster run `8dff5096-2d50-418c-a8a7-8758c7ed63f4` succeeded;
- the earlier local and GitHub HTTP-502 runs remain retained failure-path evidence.

GitHub Actions [run 31444011968](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31444011968)
successfully read and parsed the official catalog with zero errors. Its catalog and
direct-probe results are committed under `artifacts/`.

An independent manual GitHub Actions path now exists at
`.github/workflows/source-availability.yml`. It runs the same locked tests and probe
on an Ubuntu runner and preserves the catalog and probe CSVs for 30 days. The latest
evidence is [run 31444011968](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31444011968).

The initial direct checks returned HTTP 502 for all 20 tested URLs. This was an 0B
file-download blocker, not an 0A publication-discovery blocker. HTTP failures remain
unknown accessibility, never false absence.

Checkpoint 0B is complete. All 15 active archives downloaded and profiled after the
service recovered: 15,163,509 compressed bytes, 831,038 parsed rows, zero malformed
rows and one stable source schema. The committed profile retains each source URL,
SHA-256, member size, generation date and volume observation. June and December
contain both documents 4010 and 4016; all other MVP files contain 4010 only. See
`docs/checkpoints/00b-schema-volume.md` and `artifacts/cosif_source_profile.csv`.

GitHub Actions [run 31444663707](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31444663707)
also attempted a normal full GET three times and received HTTP 502, ruling out a
`HEAD`/range-only issue. The 0B code path and failure artifact are verified.

The earlier development-only mirror predicted March's 50,273 rows, 170 institutions
and 1,011 accounts exactly. It remains ignored and non-authoritative; the official
archive now supplies the certified checksum, structure and generation evidence.

Checkpoint 0C is complete. The reproducible profiler ranks only individual document
4010 and excludes semiannual document 4016 from the monthly series. Total assets are
`1000000009 + 2000000008`; compensation class 3 is excluded and total-general is a
reference check only. The 202603 top 15 have 225/225 member/month observations and
explicit components, stable names, an unambiguous BRL 21.93 billion cutoff gap and
190/190 available reference checks within BRL 1.00. See
`docs/checkpoints/00c-total-assets-top15.md` and `artifacts/top15_population.csv`.

Checkpoint 0E is complete. Eleven fail-closed controls combine the retained catalog,
runtime archives, COSIF/SGS profiles, 75 macro observations, acquisition readiness,
0C population evidence, document scope and bounded reporting-line draft. The 16-row
contract freezes `BANCOS` base-individual scope, 202501–202603, document 4010 for
analytics, 4010/4016 at landing, the 202603 top 15, five macro codes and ODbL. Total
assets is certified; credit, deposits and equity remain drafts. The contract
explicitly says `warehouse_status=not_certified` and `mart_status=not_built`. See
`docs/checkpoints/00e-source-profile-decision.md`.

Checkpoint 0D is complete on its defined metadata and alignment gate. The strict
registry fixes SGS 4189, 433, 24363, 20539 and 21082 with their official titles,
units, monthly frequency, semantic treatment, publication-lag thresholds and source
links. The bounded profiler preserves native dates and decimals and fails on gaps,
duplicates or stale results. Ruff and all 33 tests pass.

[GitHub Actions run 31445125485](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31445125485)
independently verified the implementation and retained the original HTTP-502 failure
evidence. After service recovery, a bounded 202501–202603 retry returned all 75
expected observations with five complete profiles. The later official
warehouse/dbt/Dagster run has now certified WP3 ingestion. See
`docs/checkpoints/00d-macro-series.md`.

The official warehouse certification is complete. Direct dlt and Dagster dlt loads
left 831,038 COSIF balances, 15 manifests, 75 macro observations and five series
stable with zero fixture rows. Raw and core identities reconcile exactly; all 225
top-15 total-assets values match checkpoint 0C at BRL 0.00 maximum difference. The
official dbt build passed 117/117 nodes and Dagster run
`69dd1ce1-74e9-4ebb-85b5-af7c3fa155c0` succeeded. All 11 certification controls
passed. See `docs/checkpoints/11-official-warehouse-certification.md` and
`artifacts/official_warehouse_certification.csv`.

The fixture landing foundation now exercises the real dlt and PostgreSQL path with
strict typed schemas. A local repeat load left all five business-table counts stable
and passed the synthetic accounting identity. GitHub Actions
[run 31445840964](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31445840964)
repeated the test on PostgreSQL 18: Ruff and 37 tests passed, both sources loaded
twice, and all 11 database controls passed. The evidence is committed at
`artifacts/fixture_landing_evidence.csv`. This does not certify WP2/WP3 live loads.

The fixture-backed dbt staging/core checkpoint is also complete. Eleven table models
preserve source evidence, select one complete file version per period and publish
bank/account plus macro canonical objects. The final local build passed all 117
nodes. GitHub Actions
[run 31446214745](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31446214745)
reproduced 11 successful models and 106 passing tests with zero warnings, errors or
skips. At that checkpoint no reporting lines, top-15 population or marts were
claimed; the later 0C source profile now supplies the population decision only.

The fixture-backed Dagster checkpoint is complete. Five physical dlt outputs and 11
dbt models form one continuous 16-asset graph, with dbt tests emitted as asset checks.
[GitHub Actions run 31446855199](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31446855199)
reproduced the full job on PostgreSQL 18 in 1 minute 12 seconds: 38 Python tests,
definition validation, dlt materialization and both 117-node dbt builds succeeded.
See `docs/checkpoints/03-fixture-dagster.md`.

The official landing adapter checkpoint is complete as an implementation gate. It
reads persisted profiler evidence, rejects partial or mismatched source sets and
streams the exact production contracts into dlt. GitHub Actions
[run 31447549208](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31447549208)
passed 44 tests, including an isolated PostgreSQL load with exact raw counts
`(1, 2, 5, 5, 5)`, followed by the full 117-node dbt and Dagster regression. The
11 August live retry still returned HTTP 502 for COSIF and all five SGS series. See
`docs/checkpoints/04-official-landing-adapters.md`.

The Dagster source-mode checkpoint is complete. The default remains `fixture`;
`official` requires six explicit evidence/date variables and exposes
`official_end_to_end` over the same lineage. GitHub Actions
[run 31448066885](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31448066885)
passed 47 tests, materialized both official raw asset groups against an isolated
database, constructed the 16-asset official graph and then completed the full fixture
regression. See `docs/checkpoints/05-dagster-source-modes.md`.

The manual official-sample workflow is implemented and its failure path is verified.
[Run 31448296850](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31448296850)
passed 47 tests and parsed all 454 catalog records, then observed HTTP 502 for the
selected COSIF file and all five macro series. The acquisition gate failed exactly as
designed; PostgreSQL, official dbt and official Dagster steps were skipped, while
artifact `9085384703` retained both source outcomes. See
`docs/checkpoints/06-official-sample-gate.md`.

The live-readiness checkpoint is complete. Standard CI
[run 31448608102](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31448608102)
passed 49 tests and the full fixture regression. Bounded official
[run 31448688497](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31448688497)
then wrote nine controls: period/series/window coverage passed, five completeness
controls failed, and the overall state was `blocked`. Artifact `9085517313` retains
the full CSV; no official load ran. See `docs/checkpoints/07-live-readiness.md`.

The curated dbt catalog checkpoint is complete. GitHub Actions
[run 31448952033](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31448952033)
passed 49 tests, the 117-node build, Dagster materialization and `dbt docs generate`.
Downloaded artifact `9085610234` contains descriptions for all 11 models and all 5
sources plus `catalog.json` and `index.html`. The docs explicitly state that marts
and live certification are absent. See `docs/checkpoints/08-dbt-catalog.md`.

The current-state architecture guide is complete. It covers the problem, solution,
inputs, stack rationale, no-Data-Vault decision, implemented layer ERDs, quality
strategy, challenges and implemented/planned boundary. GitHub Actions
[run 31449192239](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31449192239)
passed 51 tests, including checks that all 16 data assets are named and the unbuilt
official/mart/Power BI boundary remains explicit. See
`docs/checkpoints/09-architecture-guide.md`.

The operational runbook checkpoint is complete. It now documents all eleven data CLI
stages, the fixture and official Dagster paths, eight gate diagnoses, evidence review
and the BI handoff boundary. GitHub Actions
[run 31449393897](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31449393897)
passed 53 tests and the complete fixture/dbt/docs/Dagster regression. See
`docs/checkpoints/10-operational-runbook.md`.

The reporting-mart checkpoint is complete. Mapping version `2026-08-11-v1` assigns
seven non-overlapping top-level accounts to total assets, credit portfolio, deposits
and equity. Twelve consumption objects are frozen in `contracts/mart-schema.yml`.
Both fixture and official dbt builds passed `214/214`; the retained 31-asset official
Dagster run `8dff5096-2d50-418c-a8a7-8758c7ed63f4` succeeded after deterministic
in-process execution removed a dlt local-state race. All 13 mart controls passed. See
`docs/checkpoints/12-reporting-marts.md` and
`artifacts/reporting_mart_certification.csv`.

The Power BI checkpoint is complete. `powerbi/BankingAnalytics.pbip` contains a TMDL
semantic model (eleven tables mapped to `analytics_marts`, a parameterized PostgreSQL
connection, sixteen governed measures) and a three-page report (Banking Pulse, Compare
Banks, Trust; twenty-eight visuals). Measures are frozen first in
`contracts/measure-contract.md`. Verified live against Power BI Desktop's Analysis
Services engine via TOM/ADOMD: 900 reporting-line rows, population total assets
`R$ 13,666,747,571,587` matching the warehouse, ratios and growth reconciled, all three
pages rendered. Balance measures are semi-additive (latest month); growth uses `EDATE`
because the date table is monthly-grain; `Current`/`Prior` are reserved VAR names in the
DAX parser (use `CurVal`/`PriorVal`). No mart or contract change was needed. See
`docs/checkpoints/13-powerbi-semantic-report.md`.

## Next action

The MVP data-and-BI layer is complete. Optional, non-blocking follow-ups: an
account-level drill-through page (reporting line to source COSIF accounts) and a default
macro-series filter on the Banking Pulse timeline. Any new source family (complaints,
rates, Pix, ESTBAN, IF.data) must not widen the frozen mart contract before a new ADR.

## Known cautions

- BCB data is ODbL; MIT applies only to original project code and documentation.
- The MVP excludes prudential conglomerates and pre-2025 history.
- The top 15 are individual legal entities, not a consolidated banking-system
  population; related group entities can both appear.
- Checksum evidence is retained, but restatement analytics are deferred.
- Result accounts reset in June and December; profitability is deferred.
- Source availability follows a publication calendar; missing future periods are not
  ingestion failures.
- HTTP 5xx responses are probe failures, not evidence that a period is missing.
- Macro relationships are context and must not be described as causal.
- Future complaints, rates, Pix, ESTBAN and IF.data enhancements must not expand the
  MVP contract before it is complete.
