# Checkpoint 0B — COSIF schema and volume

Updated: 2026-08-11

## Objective

Download every active official bank archive from 202501 through 202603, validate its
integrity and checksum, and publish per-period schema and volume observations.

## Implementation delivered

- active catalog URL enforcement, including the 202512 replacement filename;
- streamed downloads with bounded retries and atomic `.part` files;
- SHA-256, compressed bytes, HTTP status, retrieval time and archive-member evidence;
- ZIP CRC validation and required CSV-member validation;
- checksum revalidation before profiling;
- encoding detection, dynamic COSIF header discovery and semicolon parsing;
- row, malformed-row, document, institution, account and declared-period metrics;
- source generation-date extraction and period-consistency control;
- stable download-manifest and source-profile CSV outputs;
- CLI commands `download-cosif` and `profile-cosif`.

## Verification

```text
uv run --locked ruff check src tests
All checks passed!

uv run --locked pytest
26 passed
```

The fixture tests cover successful ZIP download, exact checksum and bytes, invalid
ZIP cleanup, manifest round-trip, CP1252 metadata, dynamic four-line header parsing,
volume counts, malformed rows and checksum tampering.

## Live status

A bounded download of the catalog-selected 202603 file was attempted at
2026-08-10 23:59:26 UTC. It produced a manifest error row with HTTP 502, no checksum
and no retained partial file. The failure is correctly isolated and recoverable, but
there is not yet an official archive body to certify.

Status: **in progress; live download blocked by the BCB file endpoint**.

## Resume commands

```powershell
uv run --locked banking-data download-cosif `
  --start 202501 --end 202603 `
  --catalog artifacts/source_catalog.csv `
  --download-dir data/downloads/cosif `
  --manifest artifacts/generated/cosif_download_manifest.csv

uv run --locked banking-data profile-cosif `
  --manifest artifacts/generated/cosif_download_manifest.csv `
  --output artifacts/generated/cosif_source_profile.csv
```

The exit gate requires 15 complete manifest rows, no download errors, no malformed
rows, one declared period matching each requested period, stable required columns,
and the committed schema/volume profile. Checkpoint 0C must not be certified before
this gate passes.
