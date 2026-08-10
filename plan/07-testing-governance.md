# 07 — Testing and governance

## Test strategy

Tests target the main ways the focused MVP could mislead:

1. wrong or incomplete source file,
2. wrong accounting grain,
3. incorrect account-to-reporting-line mapping,
4. changing comparison population,
5. missing values presented as zero,
6. incorrectly aligned macro context, and
7. semantic-measure filter errors.

## Data-layer controls

| Control class | Examples |
|---|---|
| Acquisition | Expected URL/period, ZIP integrity, retry, checksum and completion status |
| Schema | Required columns, encoding, delimiter, decimal parsing and embedded metadata |
| Grain | Unique month × document × bank × agency × account in canonical active data |
| Active file | One latest complete source file per reporting month |
| Reconciliation | Raw active balance = canonical balance = mapped + unmapped balance |
| Population | Top-15 membership is selected once and remains stable across MVP months |
| Mapping | Every eligible account is mapped or explicitly `Unmapped` |
| Macro | Metadata matches registry; monthly values have no unexplained gaps/duplicates |

At least one deliberately corrupted fixture must fail each critical control family.
The evidence package records the failure, diagnosis and corrected passing run.

## Semantic-model regression testing

Use measure × filter context. Required contexts include:

- one bank, multiple banks and the full stable top 15,
- selected bank versus peer median,
- missing period versus reported zero,
- mapped versus unmapped accounts,
- first available month and latest complete month, and
- macro filters at source and report month.

Expected values come from authored fixtures, not from accepting the semantic model's
own query output.

## Governance artifacts

| Artifact | Purpose |
|---|---|
| Source registry | URL pattern, license, owner, expected cadence and schema |
| Macro series registry | Code, definition, unit and monthly rule |
| Reporting-line mapping | Account mapping with reviewer and rationale |
| Population definition | Latest-period top-15 selection and freeze date |
| Measure contracts | Exact interpretation and filter behavior |
| ADRs | Important choices and their costs |
| Reconciliation evidence | Source-to-report values and row counts |
| Coverage statement | Banks, January 2025+, excluded history and ratios |
| Third-party notices | BCB and ODbL attribution |

## Documentation

The curated guide explains the public question, source, architecture, layer ERDs,
mapping logic, macro context, quality controls and limitations. Generated dbt and
Power BI documentation remain supporting evidence.

## Honesty rules

- Do not label equity-to-assets as a regulatory capital ratio.
- Do not imply that the top 15 represent the entire financial system.
- Do not interpret absence as zero.
- Do not claim pre-2025 comparability in the MVP.
- Do not call a macro relationship causal.
- Put freshness, mapping coverage and scope limits on the report.

## Licensing governance

MIT covers project code and original documentation. BCB source and public derivative
databases remain under ODbL obligations. Produced works include visible BCB/ODbL
attribution.

