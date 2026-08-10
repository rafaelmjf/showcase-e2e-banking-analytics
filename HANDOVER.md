# Handover

Updated: 2026-08-11

## Current state

The public repository and revised MVP plan exist. No ingestion, database models,
Dagster assets or Power BI files have been implemented.

The chosen stack remains dlt + PostgreSQL + dbt + Dagster + Power BI. The MVP is now
deliberately focused on individual bank files from January 2025 onward, a stable top-15
comparison population, five monthly macro themes, two report pages and a trust panel.

The first source check confirmed the current BCB bulk URL pattern and a January 2026
bank file with 49,364 balance rows.

## Next action

Execute WP0 from `plan/08-delivery.md`:

1. download every available `BANCOS` month from January 2025 onward;
2. profile schemas, document codes, institutions, accounts and volume;
3. verify the official total-assets account and freeze the latest-period top 15;
4. validate the five monthly macro themes from official metadata; and
5. draft only the reporting-line mappings needed by Banking Pulse and Compare Banks.

Do not begin the full dbt model until findings are recorded in
`docs/source-profile.md`.

## Known cautions

- BCB data is ODbL; MIT applies only to original project code and documentation.
- The MVP excludes prudential conglomerates and pre-2025 history.
- Checksum evidence is retained, but restatement analytics are deferred.
- Result accounts reset in June and December; profitability is deferred.
- Source availability follows a publication calendar; missing future periods are not
  ingestion failures.
- Future complaints, rates, Pix, ESTBAN and IF.data enhancements must not expand the
  MVP contract before it is complete.

