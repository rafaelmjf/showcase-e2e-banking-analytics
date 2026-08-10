# Checkpoint 0A — COSIF source availability

Updated: 2026-08-11

## Objective

Publish an inclusive month-by-month inventory of official COSIF `BANCOS` files from
January 2025 through the current month without downloading the file bodies.

## Delivered implementation

- official catalog discovery through BCB's `Documentos/byListGuid` endpoint;
- preservation of every catalog entry and historical filename variant;
- deterministic active-version selection by document publication timestamp;
- official URL construction for each `YYYYMM` period;
- inclusive period-range validation;
- `HEAD` probe with streamed one-byte range fallback;
- tri-state availability: `true`, `false` only for HTTP 404, and blank/unknown for
  transport or server failure;
- capture of status, content size/type, last-modified, ETag, probe method and UTC
  observation time;
- stable CSV output through the `banking-data source-inventory` command;
- non-zero command exit when any period remains unknown.

## Verification

```text
uv run --locked ruff check src tests
All checks passed!

uv run --locked pytest
21 passed
```

The tests cover catalog parsing, historical filenames, duplicate active-version
selection, range construction, catalog-selected URL use, 200/404 classification,
the `HEAD`-to-range fallback, HTTP 502 classification and stable CSV output.

## Live validation status

The following smoke probe was run on 11 August 2026:

```powershell
uv run --locked banking-data source-inventory --start 202601 --end 202601 `
  --output artifacts/source_inventory_smoke.csv
```

Result: `available=0, errors=1, latest=none`, with HTTP 502 from the official BCB
host. A direct `curl` request returned the same HTTP 502. The failed CSV was removed
because it is a connectivity observation, not a valid source-availability inventory.

This does not overturn the earlier successful profile of the same January 2026 URL
(902,381 compressed bytes and 49,364 balance rows). It established only that direct
file access was unavailable during the initial observation.

To separate a BCB-wide outage from a local network-path problem, the repository also
provides `.github/workflows/source-availability.yml`. This manual workflow runs the
locked verification and inventory on an Ubuntu GitHub-hosted runner, then preserves
the CSV artifact even if unknown periods make the job fail.

[GitHub Actions run 31442891635](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31442891635)
completed the independent check on 11 August 2026:

- locked dependency installation passed;
- Ruff passed;
- all 11 tests passed;
- 20 periods were probed from 202501 through 202608;
- every period returned HTTP 502 after the range fallback;
- the CSV was retained as the workflow artifact for 30 days.

This independently reproduces the endpoint failure. It does not provide evidence
that any of the 20 source files are absent.

A third local probe of the known January 2026 file at 2026-08-10 23:36:54 UTC again
returned HTTP 502 after the range fallback. The repeated external condition now
met the project's temporary blocked-work threshold. Work resumed after adding the
separate official-catalog evidence path described below.

The later [GitHub Actions run 31444011968](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31444011968)
reached the official catalog successfully and established:

- 454 catalog records and 453 active periods;
- zero catalog parsing errors;
- 15 published MVP periods from 202501 through 202603;
- one superseded version, for 202512;
- the active 202512 replacement was published on 2026-04-01 and uses the filename
  `202512BANCOS.zip.csv.zip`.

The same run's direct probes returned HTTP 502 for all 20 requested periods. The
catalog proves publication; the probes prove only that file bodies were inaccessible
from that runner at observation time.

## Exit gate and next action

Status: **complete**.

Evidence:

- `artifacts/source_catalog.csv` — official catalog snapshot;
- `artifacts/source_inventory.csv` — contemporaneous direct-access observation.

Checkpoint 0B must use only rows marked `is_active=True`. It remains at its download
gate until file access recovers; no 0B schema or volume conclusion is claimed yet.

Retry command:

```powershell
uv run --locked banking-data source-inventory --start 202501 --end 202603 `
  --catalog artifacts/source_catalog.csv `
  --output artifacts/source_inventory.csv
```

The inventory must report zero errors before downloading bodies, but this is now the
0B access gate rather than the 0A publication gate.
