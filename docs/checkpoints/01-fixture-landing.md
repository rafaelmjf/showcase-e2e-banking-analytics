# Foundation checkpoint — fixture-backed dlt landing

Updated: 2026-08-11

## Objective

Prove the raw landing contracts, PostgreSQL destination, dlt load behavior and
deterministic identities while official BCB body endpoints are unavailable. This is
an implementation foundation, not a substitute for WP0 source certification.

## Delivered

- synthetic contract fixtures for two COSIF months and three fictional institutions;
- three synthetic months for each accepted macro series;
- separate `raw_cosif` and `raw_macro` dlt sources and PostgreSQL datasets;
- source-faithful raw balance text beside a typed `numeric(38,2)` value;
- file checksum plus source row number as the balance landing identity;
- native SGS date plus an explicit `YYYYMM` report key;
- merge identities for manifests, metadata, observations and fetch windows;
- strict per-resource column/type contracts after table creation;
- validated environment settings with compose-compatible defaults;
- reusable load and verification commands;
- a PostgreSQL 18 CI service that loads twice and preserves control evidence.

The files under `fixtures/` are authored synthetic values. Every institution name is
marked `FIXTURE`, every source URL uses the `fixture://` scheme and fixture flags are
preserved where applicable.

## Verification

Local PostgreSQL 18 loaded both sources successfully twice. Business-table counts
were identical before and after the second load:

| Table | Rows | Unique landing identities |
|---|---:|---:|
| `raw_cosif.cosif_file_manifest` | 2 | 2 |
| `raw_cosif.cosif_balance_row` | 24 | 24 |
| `raw_macro.sgs_series_metadata` | 5 | 5 |
| `raw_macro.sgs_observation` | 15 | 15 |
| `raw_macro.sgs_fetch_manifest` | 5 | 5 |

All six bank-month groups also reconciled class 1 plus class 2 to total general
assets minus class-3 controls within R$0.01.

[GitHub Actions run 31445840964](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31445840964)
independently created PostgreSQL 18, passed Ruff and all 37 tests, loaded both sources
twice, passed all 11 database controls and retained the evidence artifact. The
committed LF-normalized copy is `artifacts/fixture_landing_evidence.csv` with SHA-256
`0AAD8A6DDD8DBF18C3586CCBEC374BE32F94D0B209AC6B1E8C22F04332678E9C`.

## Commands

```powershell
docker compose up -d warehouse
uv run --locked banking-data load-fixtures --project-root .
uv run --locked banking-data verify-fixtures
```

## Boundary

This proves fixture schemas and mechanics only. WP2 and WP3 are not complete until
official COSIF archives and SGS observations load through these contracts. WP0 0B,
0C and 0E remain open, and the fixture totals must never be shown as Brazilian bank
facts.
