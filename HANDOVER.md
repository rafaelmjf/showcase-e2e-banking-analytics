# Handover

Updated: 2026-08-11

## Current state

The local project scaffold and implementation plan exist. No ingestion, database
models, Dagster assets or Power BI files have been implemented.

The chosen stack is dlt + PostgreSQL + dbt + Dagster + Power BI. The first source
profile confirmed the current BCB bulk URL pattern and a January 2026 bank file with
49,364 balance rows. See `plan/03-sources.md` for evidence and gates.

## Next action

Execute WP0 from `plan/08-delivery.md`:

1. download 24 consecutive months for banks and prudential conglomerates;
2. profile schemas, document codes, institutions, accounts, duplicates and volume;
3. profile the 2024/2025 COSIF transition;
4. validate the macro series registry from official metadata; and
5. decide the primary comparison grain.

Do not begin the full data model until the duplicate-scope and taxonomy findings are
recorded in `docs/source-profile.md`.

## Known cautions

- BCB data is ODbL; MIT applies only to original project code and documentation.
- Individual banks and prudential conglomerates overlap and must not be summed.
- The COSIF standard changed from January 2025.
- Result accounts reset in June and December; profitability is deferred.
- Source availability follows a publication calendar and missing future periods are
  not ingestion failures.

