# 07 — Testing and governance

## Test strategy

Tests are organised around the main ways a banking report can mislead:

1. wrong source version,
2. wrong accounting grain,
3. double-counted reporting scope,
4. incorrect account mapping,
5. false continuity across taxonomy change,
6. incorrectly aligned macro frequency, and
7. semantic-measure context errors.

## Data-layer controls

| Control class | Examples |
|---|---|
| Acquisition | Expected URL, reporting period, ZIP integrity, retry and checksum |
| Schema | Required columns, encoding, delimiter, decimal parsing and source metadata |
| Grain | Unique period × scope × document × institution × agency × account in canonical active data |
| Version | One active file per segment/period; every supersession traceable |
| Reconciliation | Raw active balance = canonical balance = mapped + unmapped balance |
| Scope | No fact aggregate contains both institution and parent conglomerate |
| Taxonomy | Every 2025-boundary mapping has status, rule, version and reviewer |
| Hierarchy | Published parent and governed child rollups compared with explained differences |
| Macro | Metadata matches registry; date windows have no unexplained gaps or duplicate observations |

At least one deliberately corrupted fixture must fail each critical control family.
The evidence package records the failure, diagnosis and corrected passing run.

## Semantic-model regression testing

Use the same principle as the procurement showcase: measure × filter context.

Required contexts include:

- individual versus consolidated scope,
- institution versus peer group,
- pre-2025 versus post-2025 taxonomy,
- missing period versus reported zero,
- mapped versus unmapped account population, and
- macro filters at native and aligned frequency.

Expected values come from authored fixture cases, not by querying the semantic model
and accepting its own result.

## Governance artifacts

| Artifact | Purpose |
|---|---|
| Source registry | URL pattern, license, owner, expected cadence and schema |
| Macro series registry | Code, definition, unit, frequency and alignment rule |
| Reporting-line mapping | Effective-dated account mapping with reviewer and rationale |
| Measure contracts | Exact business interpretation and allowed filter scopes |
| ADRs | Important choices and their costs |
| Reconciliation evidence | Source-to-report values and row counts |
| Coverage statement | Segments, periods, taxonomy gaps and excluded ratios |
| Third-party notices | BCB and ODbL attribution |

## Documentation

The curated project guide will explain the problem, source, architecture, each layer,
ERDs, quality controls, macro alignment, observations and known limitations. Generated
dbt and Power BI documentation remain supporting evidence, not the newcomer-facing
story.

## Honesty rules

- Do not label analytical equity-to-assets as a regulatory capital ratio.
- Do not rank entities across incompatible scopes.
- Do not interpret absence as zero.
- Do not smooth over the 2025 taxonomy boundary.
- Do not call a macro relationship causal.
- Put freshness, mapping coverage and source limits on the report itself.

## Licensing governance

MIT covers project code and original documentation. BCB source databases and public
derivative databases remain under ODbL obligations. Produced works include a visible
BCB/ODbL attribution. License boundaries are stated in the README and third-party
notice rather than hidden in source comments.

