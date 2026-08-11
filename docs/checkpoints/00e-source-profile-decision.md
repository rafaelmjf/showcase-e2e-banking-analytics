# WP0 checkpoint 0E — final source-profile decision

Updated: 2026-08-11

## Objective

Consolidate checkpoints 0A through 0D into one fail-closed, machine-readable
implementation decision; freeze the exact official-load boundary; and publish a
bounded reporting-line draft without claiming unfinished mappings or warehouse work.

## Decision

Status: **complete; 11/11 controls passed**.

The source profile is `ready_for_official_warehouse_certification`. This means the
retained evidence is complete enough to execute the next official
PostgreSQL/dbt/Dagster certification run. It does **not** mean that the warehouse is
already certified, that reporting marts exist, or that Power BI may bind to them.

## Frozen official-load boundary

| Decision | Frozen value |
|---|---|
| COSIF segment and grain | `BANCOS`, base individual CNPJ |
| Source window | 202501–202603 inclusive |
| Landing documents | 4010 and 4016 |
| Analytical document | Monthly individual document 4010 only |
| Total assets | `1000000009 + 2000000008` |
| Population | 202603 top 15, fixed across the full window |
| Macro series | SGS 4189, 433, 24363, 20539 and 21082 |
| Macro window | 202501–202603 inclusive |
| Source-data license | ODbL |

Document 4016 remains preserved at landing but is excluded from ranking and monthly
trends because it duplicates June and December positions. Compensation class 3 is
excluded from total assets. Total-general less compensation remains a reference
reconciliation, not the analytical measure.

## Bounded reporting-line draft

Only total assets is certified at this checkpoint. The other mappings are explicitly
provisional and cannot be relabelled as certified by the 0E gate:

| Reporting line | Status | 4010 account boundary | Next proof required |
|---|---|---|---|
| Total assets | Certified | `1000000009 + 2000000008` | Carry into official core reconciliation |
| Credit portfolio | Draft | Core `1600000007`; candidates `1700000000`, `1810000000` | Decide candidate inclusion and reconcile |
| Deposits | Draft | `4100000009` | Reconcile the future mapped mart |
| Equity | Draft | `6000000004` | Reconcile the future mapped mart |

The core credit account appears in 225/225 selected member-months. Leasing appears
in 67/225 and other credit-characteristic balances in 210/225, so silently summing
all three would be an authored accounting choice, not a source fact. Deposits and
equity each appear in 225/225 but remain draft until mart-level reconciliation.

## Machine-readable gate

`banking-data assess-source-profile` rereads the retained catalog, archive manifest,
COSIF and macro profiles, raw macro observations, nine-control acquisition result,
0C evidence, full population coverage and reporting-line draft. It also confirms
that every referenced COSIF archive still exists before returning ready.

The gate writes:

- `checkpoint_0e_controls.csv`: 10 prerequisite controls plus the overall decision;
- `source_profile_contract.csv`: 16 frozen, bounded, decision or pending records.

The two pending records deliberately say `warehouse_status=not_certified` and
`mart_status=not_built`. Any missing evidence, altered boundary, incomplete archive,
misrepresented draft or coverage mismatch makes the overall control `blocked`.

## Retained evidence

- [11-control decision](../../artifacts/checkpoint_0e_controls.csv)
- [16-row source contract](../../artifacts/source_profile_contract.csv)
- [Reporting-line draft](../../config/reporting_line_draft.csv)
- [Consolidated source profile](../source-profile.md)

## Next gate

Execute the frozen 202501–202603 evidence through official dlt/PostgreSQL, dbt and
Dagster modes. Preserve raw/core counts, checksums, fixture flags, dbt results and
Dagster asset checks. Reporting-line marts remain out of scope until the draft
mappings are resolved and reconciled.
