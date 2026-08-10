# Checkpoint 0A — COSIF source availability

Updated: 2026-08-11

## Objective

Publish an inclusive month-by-month inventory of official COSIF `BANCOS` files from
January 2025 through the current month without downloading the file bodies.

## Delivered implementation

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
11 passed
```

The tests cover range construction, validation, official URL construction, 200/404
classification, the `HEAD`-to-range fallback, content-range size parsing, correct
classification of HTTP 502 as unknown, and stable CSV output.

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
(902,381 compressed bytes and 49,364 balance rows). It means only that the inventory
cannot be refreshed and independently validated at this checkpoint.

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

## Exit gate and next action

Status: **blocked on live validation**.

After the host recovers, run:

```powershell
uv run --locked banking-data source-inventory --start 202501 --end 202608 `
  --output artifacts/source_inventory.csv
```

Checkpoint 0A is complete only when the command reports zero errors and the CSV has
been reviewed for a continuous published range followed only by expected 404 future
periods. Do not begin checkpoint 0B before that gate passes.
