# Measure Contract

**Version 0.1. Total Assets is certified; every other measure is draft.**

## What this document is

This project publishes numbers about Brazil's largest banks. This document defines
what each of those numbers means, before any of them is built in Power BI.

That order matters. If a number is defined only by the DAX that calculates it, then
the code becomes the definition, and nobody can say whether it is right — only whether
it runs. Writing the definition first makes the calculation checkable against
something.

Each measure below has a plain description, the rule used to calculate it, a status
saying how settled that rule is, and — where relevant — a note on what the number
cannot tell you.

## Who decides what

| Role | Responsibility |
|---|---|
| Data layer | Delivers the certified marts and guarantees their shape. Does not define business measures. |
| Measure owner | Decides contested definitions, approves certification. |
| BI layer | Implements the approved definitions in DAX against `contracts/mart-schema.yml`. |

The data layer deliberately does **not** compute analytical ratios such as
equity-to-assets, because those depend on a judgement call about the denominator, and
judgement calls belong somewhere they can be seen and argued with.

## Status meanings

| Status | Meaning |
|---|---|
| **Certified** | Approved. The official number. Changing it requires a recorded decision. |
| **Draft** | The definition looks right but has not been formally approved. |
| **Deferred** | Cannot be built meaningfully yet. The reason is stated. |

## Terms used here

**COSIF** — the Brazilian central bank's standard chart of accounts. Every balance is
tagged with a COSIF account code; the codes are hierarchical, so a parent account
already contains its children.

**Reporting line** — a small governed grouping of top-level COSIF accounts (total
assets, credit portfolio, deposits, equity), frozen under mapping version
`2026-08-11-v1` in `contracts/mart-schema.yml`.

**Stable population** — the top 15 individual institutions ranked by total assets at
202603, held fixed across all fifteen months so comparisons are like-for-like.

**Grain** — the level of detail one row represents. The primary fact
(`fact_reporting_line_balance`) is one bank × month × reporting line.

**Additive** — a measure that can be safely summed across categories. A balance is
additive across banks; a percentage is not — it must be recalculated at each level.

## The reporting lines are not one balance sheet

The four reporting lines span **different sides** of the balance sheet: total assets
and credit portfolio are asset-side, deposits are a liability, equity is equity.
**They must never be summed together.** Every visual treats each line as a standalone
magnitude, and every ratio below divides by total assets — the only certified
denominator.

## The measures

### Balance measures

All read `fact_reporting_line_balance[presentation_balance_amount]`. The mapping's
`presentation_multiplier` is `1` for all seven accounts, so presentation equals the
reported sum; the column is used so a future sign convention flows through without a
measure rewrite.

| Measure | Rule | Status |
|---|---|---|
| **Total Assets** | `SUM(presentation_balance_amount)` filtered to the `total_assets` line | **Certified** — the certified checkpoint 0C total-assets line |
| **Credit Portfolio** | same, `credit_portfolio` line | Draft — mapping certified, analytical label draft (0E) |
| **Deposits** | same, `deposits` line | Draft |
| **Equity** | same, `equity` line | Draft |

### Ratio measures

Every ratio wraps its line filter in `KEEPFILTERS` and uses `DIVIDE` for safe blank
handling. The denominator is always **Total Assets** unless stated.

| Measure | Rule | Status | Note |
|---|---|---|---|
| **Credit Share of Assets** | `DIVIDE([Credit Portfolio], [Total Assets])` | Draft | How much of the balance sheet is lending. |
| **Deposit Funding Share** | `DIVIDE([Deposits], [Total Assets])` | Draft | Deposits relative to assets. There is **no** mapped total-funding (total-liabilities) denominator in the certified contract, so this is a deposit-to-assets ratio, not deposits ÷ total funding. |
| **Equity-to-Assets** | `DIVIDE([Equity], [Total Assets])` | Draft | An analytical structure measure. **Not** a Basel or regulatory capital ratio. |
| **Comparison-Population Share** | `DIVIDE([Total Assets], CALCULATE([Total Assets], ALLSELECTED(Bank)))` | Draft | A bank's share of the fixed top-15 total. |

### Growth measures

Time intelligence on the marked Date table (`dim_date`, monthly grain).

| Measure | Rule | Status | Note |
|---|---|---|---|
| **Total Assets MoM Growth** | prior month via `EDATE(MAX(Date[Month]), -1)` + `FILTER(ALL(Date), ...)`, then `DIVIDE(cur - prior, prior)` | Draft | Month-over-month; available for 14 of 15 months. `EDATE`, not `DATEADD`: the date table is monthly-grain, which `DATEADD` cannot shift. |
| **Total Assets YoY Growth** | same with `EDATE(..., -12)` | Draft | **Only defined for 202601, 202602, 202603** — the window is 15 months, so only three months have a prior-year comparator. Pages must not lead with YoY. |

The MoM/YoY pattern applies to each balance measure by swapping the base measure.

### Comparison measures (page 2)

| Measure | Rule | Status |
|---|---|---|
| **Peer Median (Total Assets)** | `MEDIANX(VALUES(Bank[bank_key]), [Total Assets])` | Draft |

The same `MEDIANX` shape produces peer medians for any balance or ratio measure.

### Deferred

| Measure | Why deferred |
|---|---|
| **Mapping Coverage / Unmapped Amount** | No meaningful single denominator exists: `fact_account_balance` holds hierarchical COSIF codes (a parent already contains its children), so summing "all accounts" double-counts. A single coverage ratio across the mixed-side reporting lines is not defensible. Coverage, if needed, is expressed per-side (e.g. credit share of assets already is asset-side coverage). |
| **Profitability / return ratios** | COSIF result accounts reset in June and December; periodisation is not yet validated. |
| **Basel / liquidity / regulatory ratios** | Require IF.data, which is out of MVP scope. |
| **Rolling-12-month IPCA** | Only computable for the last four months of the window; monthly IPCA is preserved, compounding is a later phase. |

## Trust and provenance (not measures)

The Trust page reads existing certified marts directly — no new warehouse objects:

- latest source period, active checksum, retrieval date, selected-file status →
  `dim_source_file` (filtered to `is_selected`);
- observed months and any gap → `dim_date`;
- mapping version and status → `dim_reporting_line`;
- **reconciliation status** is a certification-time fact, not a live warehouse figure.
  It is shown as a static statement — "reporting-line balances reconcile to mapped
  source accounts at BRL 0.00; total assets reconcile to checkpoint 0C at BRL 0.00
  (mapping `2026-08-11-v1`, certified 2026-08-11)" — sourced from
  `artifacts/reporting_mart_certification.csv`. A live table is deliberately avoided
  because the warehouse does not re-reconcile on refresh.

## Rules that apply to every measure

- **Never sum the four reporting lines** — they span different balance-sheet sides.
- **Every ratio uses `KEEPFILTERS`** so a line filter narrows the user's selection
  instead of replacing it, and `DIVIDE` so an empty denominator returns blank.
- **Percentages are never added up** — each rate is recalculated at its display level.
- **Missing values are never shown as zero.**
- **Macro series are context, never causal** — no visual or caption may state that a
  macro movement caused a bank outcome.
- **Balances are nominal BRL** — no inflation adjustment or rebasing.
