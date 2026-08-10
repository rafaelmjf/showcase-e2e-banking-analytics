# Handover

Updated: 2026-08-11

## Current state

The public repository and revised MVP plan exist. WP0 checkpoint 0A has implemented
and tested the COSIF bank-file availability inventory command. No ingestion,
database models, Dagster assets or Power BI files have been implemented.

The chosen stack remains dlt + PostgreSQL + dbt + Dagster + Power BI. The MVP is now
deliberately focused on individual bank files from January 2025 onward, a stable top-15
comparison population, five monthly macro themes, two report pages and a trust panel.

The earlier source check confirmed the current BCB bulk URL pattern and a January
2026 bank file with 49,364 balance rows. The new command deliberately records HTTP
failures as unknown rather than incorrectly marking files absent, and falls back
from `HEAD` to a streamed range request when required.

Verification completed:

- `uv run --locked ruff check src tests` — passed;
- `uv run --locked pytest` — 11 passed;
- a live 202601 probe on 11 August 2026 — blocked by HTTP 502 from the official BCB
  host through both Python and direct `curl`;
- GitHub Actions run `31442891635` — locked installation, Ruff and 11 tests passed;
  the independent Ubuntu runner then observed HTTP 502 for all 20 periods from
  202501 through 202608 and preserved its CSV artifact.

The failed CSV was not retained as an availability artifact because it did not
establish availability. See `docs/checkpoints/00a-source-availability.md`.

An independent manual GitHub Actions path now exists at
`.github/workflows/source-availability.yml`. It runs the same locked tests and probe
on an Ubuntu runner and preserves the CSV for 30 days even when the probe fails. The
latest evidence is [run 31442891635](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31442891635).

## Next action

Resume checkpoint 0A from `plan/08-delivery.md` after the official host recovers:

```powershell
uv run --locked banking-data source-inventory --start 202501 --end 202608 `
  --output artifacts/source_inventory.csv
```

The command must finish with `errors=0`. Review the CSV, update the 0A checkpoint
record, commit it, and only then begin 0B (download and schema/volume profiling).
If the local BCB route still fails, dispatch the **Source availability checkpoint**
workflow with the same start and end periods and inspect its artifact.

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
