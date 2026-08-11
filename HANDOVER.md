# Handover

Updated: 2026-08-11

## Current state

WP0 checkpoint 0A is complete. The official COSIF document catalog and direct file
probe are implemented, tested and preserved as repository evidence. No ingestion,
database models, Dagster assets or Power BI files have been implemented.

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

## Next action

Resume checkpoint 0B from `plan/08-delivery.md` using the catalog-selected active
URLs. Retry one bounded download first:

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
- Future complaints, rates, Pix, ESTBAN and IF.data enhancements must not expand the
  MVP contract before it is complete.
