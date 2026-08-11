# Checkpoint 0D — five-series macro profile

Updated: 2026-08-11

## Objective

Fix the exact official definitions, units, native frequency, reporting-month rules
and revision treatment for the five MVP context series before ingestion or semantic
measures are built.

## Accepted registry

| SGS | Theme | Official unit | Native monthly interpretation | Curated derivation |
|---:|---|---|---|---|
| 4189 | Selic | Percentual ao ano | Annualized value calculated from the accumulated monthly Selic | Latest level; never sum or average |
| 433 | IPCA | Variação percentual mensal | Monthly inflation rate | Rolling 12 months by geometric compounding, never addition |
| 24363 | IBC-Br | Índice | Unadjusted monthly activity index | Level and year-over-year change; no seasonally misleading month-over-month claim |
| 20539 | System credit | Unidades monetárias correntes | End-of-period SFN credit stock, free plus directed | Level and year-over-year change; never sum across months |
| 21082 | 90+ delinquency | Percentual | Share of SFN credit with at least one installment more than 90 days late | Level and percentage-point change; never average across months |

The source observation date is retained verbatim. `report_month` is its calendar
`YYYYMM`, which handles the SGS series' mixed first-day and end-of-month date
conventions without pretending that every observation is a month-end stock.

The authored contract is `config/macro_series_registry.csv`. It contains each of the
five codes exactly once and includes title, unit, frequency, source start, semantics,
alignment, derivation, expected publication lag, revision policy, catalog URL and SGS
metadata URL.

## Implementation delivered

- strict registry parsing and exact required-code validation;
- bounded official BCData JSON URLs with explicit start and end dates;
- retry and per-series failure isolation;
- lossless decimal parsing, including comma-decimal fixture coverage;
- native observation date plus explicit `report_month` output;
- duplicate date, duplicate month, internal gap and expected-lag controls;
- durable observation and profile CSV outputs, including five failure rows when the
  API is unavailable;
- CLI command `banking-data profile-sgs`;
- independent GitHub Actions workflow with a hard exit gate and retained artifacts.

## Verification

```text
uv run --locked ruff check src tests
All checks passed!

uv run --locked pytest
33 passed
```

Local execution against 2025-01-01 through 2026-07-31 reached all five official API
URLs but received HTTP 502 for each. It correctly emitted zero observations and five
error profiles.

[GitHub Actions run 31445125485](https://github.com/rafaelmjf/showcase-e2e-banking-analytics/actions/runs/31445125485)
independently repeated the locked run on Ubuntu. The implementation checks passed and
the workflow retained both CSV artifacts; all five official API calls again returned
HTTP 502, so the workflow's acquisition gate failed as designed.

The definitions, units, monthly frequencies and source start dates were validated
against the official BCB Open Data catalog records. The catalog identifies 4189 as
annualized monthly Selic in percent per year, 433 as monthly IPCA variation, 24363 as
a monthly index, 20539 as a monthly end-of-period credit balance and 21082 as a
monthly percentage. The exact reporting treatment above is an authored semantic
decision, not source metadata.

Status: **complete for checkpoint 0D's metadata and alignment exit gate**. Live
observation acquisition recovered on 11 August 2026: a bounded 202501–202603 local
retry returned 75 observations, five complete profiles and no gaps or duplicates.
WP3 ingestion is still uncertified until those inputs pass the official warehouse,
dbt and Dagster route. The committed completeness evidence is
[`macro_source_profile.csv`](../../artifacts/macro_source_profile.csv).

## Resume command

```powershell
uv run --locked banking-data profile-sgs `
  --registry config/macro_series_registry.csv `
  --start 2025-01-01 --end 2026-07-31 `
  --observations artifacts/generated/macro_observations.csv `
  --profile artifacts/generated/macro_profile.csv
```

The live acquisition gate requires five complete profile rows, no duplicates or
internal gaps, and freshness lag within each registry threshold. A 5xx result is an
access failure, never an inferred missing observation.
