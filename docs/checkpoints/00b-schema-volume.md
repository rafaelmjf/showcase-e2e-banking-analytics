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

[GitHub Actions run 31444663707](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31444663707)
then exercised a normal full GET rather than `HEAD` or a range request. The Ubuntu
runner passed Ruff and all 26 tests, retried the catalog-selected 202603 URL three
times, and produced the same HTTP 502 manifest state. No archive or profile was
fabricated, and the generated manifest was retained as a run artifact.

Status: **in progress; live download blocked by the BCB file endpoint**.

## Development-only mirror cross-check

To exercise the expected current data shape without misrepresenting it as official
evidence, commit `190cb06963bf3b59fa3b7ec281ed3aebf2ac64b2` from
[PulseDataLabs/PulseIFData](https://github.com/PulseDataLabs/PulseIFData) was inspected.
Its scraper identifies BCB as its source and preserves the current normalized fields,
but this mirror is not an MVP input and cannot pass the exit gate.

Observed in `data/bacen_balancetes_bancos.csv`:

- mirror SHA-256 `451cde33185b991f709a446d2c887b7e8910cb520505a3547911ce9337a786d7`;
- 6,982,690 bytes and 50,273 rows;
- one source period, 202603, captured on 2026-08-10;
- document 4010 only;
- 170 distinct CNPJ/name pairs, 1,011 account codes and 10-digit account codes on
  every row;
- expected normalized accounting fields plus the mirror's `data_captura` field.

This corroborates the expected March scale and current account-code width. It does
not certify the official ZIP checksum, raw encoding, metadata lines, row completeness
or source-generation date. The mirror file remains under ignored `data/work/` and is
not committed.

The mirror also provides a provisional accounting-identity check for later 0C work:

- class 1 `1000000009` is Ativo Realizável;
- class 2 `2000000008` is Ativo Permanente;
- class 3 `3000000007` is Compensação Ativa;
- `3999999009` is Total Geral do Ativo and includes class-3 control balances;
- for 113 institutions containing all four rows, `(class 1 + class 2)` reconciled to
  `(Total Geral do Ativo - Compensação Ativa)` within R$0.10;
- all provisional top-15 institutions had both class-1 and class-2 rows.

This prevents the misleading use of `3999999009` as ordinary total assets. The
identity and ranking remain provisional until the official archives pass 0B.

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
