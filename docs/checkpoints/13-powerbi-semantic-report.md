# Checkpoint 13 — Power BI semantic model and report

Date: 2026-08-11

## Decision

The version-controlled Power BI PBIP layer is implemented and verified against the
certified official warehouse. It binds only to the twelve consumption objects in
`contracts/mart-schema.yml`; raw, staging and core schemas remain off-limits. The
data contract was not widened — no new marts, no re-certification.

## What was built

A PBIP project under `powerbi/`:

- **`BankingAnalytics.SemanticModel`** — TMDL model with eleven import tables mapped to
  `analytics_marts`, a parameterized PostgreSQL connection (`WarehouseServer`,
  `WarehouseDatabase`), sixteen governed measures, and the relationships that form two
  clean stars (reporting-line balances and source-account drill-through) plus the macro
  context fact. `discourageImplicitMeasures` is on; every balance measure is
  semi-additive (latest month in context, never a cross-month sum).
- **`BankingAnalytics.Report`** — three pages (Banking Pulse, Compare Banks, Trust),
  twenty-eight visuals, on the shared base theme. The Trust page is served entirely
  from existing dimensions plus a static certification note; reconciliation status is a
  certification-time fact, not a live warehouse figure.

Measure definitions are frozen first in `contracts/measure-contract.md` with status
(Certified / Draft / Deferred), denominators, and limits — the data layer does not
compute business ratios.

## Verification

Verified live against Power BI Desktop's local Analysis Services engine via TOM/ADOMD
(the `connect-pbid` skill), not only on disk:

- all 109 TMDL `sourceColumn`s exist in `analytics_marts`; the model refreshes;
- 900 reporting-line rows, 15 months, 15 banks loaded;
- population totals at 202603 match the warehouse exactly: total assets
  `R$ 13,666,747,571,587`, credit `R$ 4.83 tri`, deposits `R$ 4.58 tri`, equity
  `R$ 1.22 tri`; all four lines are positive (sign convention confirmed, multiplier 1);
- ratios reconcile (population credit share 35.3%, deposit funding 33.5%,
  equity-to-assets 8.9%); comparison-population share sums to 100%;
- MoM growth 3.3% and YoY growth 12.5% at the population/latest month; YoY is defined
  only for 202601–202603, as the contract states;
- all three pages render correctly (captured from the live instance via the Desktop
  Bridge).

## Notable engineering findings

1. **Semi-additive balances.** A balance sheet is a stock; summing total assets across
   fifteen months produced a meaningless `R$ 190T`. Every balance measure now returns
   the latest month in context via `LASTNONBLANK`.
2. **Monthly-grain date table.** `dim_date` has fifteen month rows, so `DATEADD`/daily
   time intelligence fails. Period-over-period uses `EDATE` + `FILTER(ALL('Date'), …)`.
3. **Reserved VAR names.** The DAX parser rejects `Current` and `Prior` as VAR names —
   the measure silently compiles to a `SYNTAXERROR` stub. Renamed to `CurVal` /
   `PriorVal`. Recorded in `.claude/rules/connect-pbid.md`.
4. **Mixed balance-sheet sides.** The four reporting lines span assets, liabilities and
   equity and are never summed; every ratio divides by total assets, the only certified
   denominator.

## Next boundary

The MVP is complete: source-to-mart data layer plus the certified BI layer. Optional
follow-ups (not required for the MVP): an account-level drill-through page and a
default macro-series filter on Banking Pulse.
