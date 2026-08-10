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

## Next action

Begin checkpoint 0B from `plan/08-delivery.md` using the catalog-selected active
URLs. Retry the bounded download first:

```powershell
uv run --locked banking-data source-inventory --start 202501 --end 202603 `
  --catalog artifacts/source_catalog.csv `
  --output artifacts/source_inventory.csv
```

When file access recovers, download active 202501–202603 files, record SHA-256 and
byte counts, then publish the schema/volume profile. The active December 2025 URL is
the replacement ending in `202512BANCOS.zip.csv.zip`, not the earlier conventional
filename.

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
