# Handover

Updated: 2026-08-11

## Current state

WP0 checkpoints 0A and 0D are complete. The official COSIF document catalog and the
five-series macro contract are implemented, tested and preserved as repository
evidence. Fixture-backed dlt/PostgreSQL landing, dbt staging/core and a 16-asset
Dagster graph are complete; no certified live landing, reporting marts or Power BI
files have been implemented. Fixture success is not live-data certification.
The production COSIF/SGS evidence-to-dlt adapters are also implemented and verified
against isolated mocked source bodies, but remain unexecuted on live observations.

The chosen stack remains dlt + PostgreSQL + dbt + Dagster + Power BI. The MVP is now
deliberately focused on individual bank files from January 2025 onward, a stable top-15
comparison population, five monthly macro themes, two report pages and a trust panel.

The official catalog currently contains 454 records, 453 active periods and one
superseded file version. The MVP range has 15 published months from 202501 through
202603. December 2025 has two catalog entries; the later 2026-04-01 publication is
selected deterministically as active.

Verification completed:

- `uv run --locked ruff check src tests` — passed;
- `uv run --locked pytest` — 21 passed;
- a live 202601 probe on 11 August 2026 — blocked by HTTP 502 from the official BCB
  host through both Python and direct `curl`;
- GitHub Actions run `31442891635` — locked installation, Ruff and 11 tests passed;
  the independent Ubuntu runner then observed HTTP 502 for all 20 periods from
  202501 through 202608 and preserved its CSV artifact.

GitHub Actions [run 31444011968](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31444011968)
successfully read and parsed the official catalog with zero errors. Its catalog and
direct-probe results are committed under `artifacts/`.

An independent manual GitHub Actions path now exists at
`.github/workflows/source-availability.yml`. It runs the same locked tests and probe
on an Ubuntu runner and preserves the catalog and probe CSVs for 30 days. The latest
evidence is [run 31444011968](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31444011968).

Direct access to all 20 tested URLs still returned HTTP 502. This is now an 0B file
download blocker, not an 0A publication-discovery blocker. HTTP failures remain
unknown accessibility, never false absence.

Checkpoint 0B's downloader and profiler are implemented. They stream atomically,
retain SHA-256 and byte evidence, validate ZIP/CRC/CSV structure, detect encoding and
the source header, and produce the required per-period counts. Ruff and all 26 tests
pass. A bounded live 202603 download failed cleanly with HTTP 502 and retained no
partial file. See `docs/checkpoints/00b-schema-volume.md`.

GitHub Actions [run 31444663707](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31444663707)
also attempted a normal full GET three times and received HTTP 502, ruling out a
`HEAD`/range-only issue. The 0B code path and failure artifact are verified.

A development-only current mirror was also profiled to stress-check expected scale:
202603 has 50,273 rows, 170 CNPJ/name pairs, 1,011 accounts and only document 4010.
It is explicitly non-authoritative, ignored under `data/work/`, and does not satisfy
the 0B exit gate.

Checkpoint 0D is complete on its defined metadata and alignment gate. The strict
registry fixes SGS 4189, 433, 24363, 20539 and 21082 with their official titles,
units, monthly frequency, semantic treatment, publication-lag thresholds and source
links. The bounded profiler preserves native dates and decimals and fails on gaps,
duplicates or stale results. Ruff and all 33 tests pass.

[GitHub Actions run 31445125485](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31445125485)
independently verified the implementation and retained both output files. All five
official SGS calls returned HTTP 502, so live observation materialisation remains an
explicit WP3 blocker rather than fabricated evidence. See
`docs/checkpoints/00d-macro-series.md`.

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
skips. No reporting lines, top-15 population or marts have been claimed.

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

## Next action

Add a source-mode switch to the Dagster code location so the same five raw asset keys
can use either fixture inputs or fully verified official evidence. Default to fixture
mode and fail definition loading when official mode lacks an explicit evidence path.
Retry one bounded 0B download first at each source checkpoint; also retry the 0D live
acquisition command when the BCB services recover:

```powershell
uv run --locked banking-data download-cosif --start 202603 --end 202603 `
  --catalog artifacts/source_catalog.csv --attempts 1
```

When that succeeds, run the full download and profile commands recorded in the 0B
checkpoint. The active December 2025 URL is the replacement ending in
`202512BANCOS.zip.csv.zip`, not the earlier conventional filename.

Do not begin the full dbt model until findings are recorded in
`docs/source-profile.md`.

## Known cautions

- BCB data is ODbL; MIT applies only to original project code and documentation.
- The MVP excludes prudential conglomerates and pre-2025 history.
- Checksum evidence is retained, but restatement analytics are deferred.
- Result accounts reset in June and December; profitability is deferred.
- Source availability follows a publication calendar; missing future periods are not
  ingestion failures.
- HTTP 5xx responses are probe failures, not evidence that a period is missing.
- Macro relationships are context and must not be described as causal.
- Future complaints, rates, Pix, ESTBAN and IF.data enhancements must not expand the
  MVP contract before it is complete.
