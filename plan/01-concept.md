# 01 — Concept

## Problem statement

Public bank disclosures are technically available but difficult to interpret. They
arrive as periodic files organised around regulatory documents and COSIF accounts,
not around the questions a portfolio analyst, finance leader or risk stakeholder
would ask. Institution names change, consolidated and individual views can be mixed,
accounting taxonomies evolve, reporting frequencies differ and macroeconomic context
is stored separately.

The result is a familiar BI problem: abundant data, weak comparability and a high risk
of producing confident but misleading ratios.

## Proposed solution

Build **Brazilian Banking and Macroeconomic Intelligence**, a governed analytical
product that turns official BCB disclosures into comparable institution and peer-group
views while preserving the lineage to source document and COSIF account.

The product answers:

1. Which institutions and peer groups are growing or contracting?
2. How are assets, credit, funding and equity composition changing?
3. Which movements are institution-specific and which reflect the system-wide cycle?
4. How do balance structures differ across banks and prudential conglomerates?
5. Where are apparent trends affected by reporting frequency, restatement or the 2025
   COSIF redesign?
6. How did institutions behave across different interest-rate, inflation, activity
   and credit-risk environments?

## Portfolio thesis

| Claim | Evidence |
|---|---|
| Financial-domain modelling | Effective-dated COSIF hierarchy and governed reporting-line bridge |
| Data engineering | Metadata-driven dlt ingestion of parameterised ZIP and SGS endpoints |
| Architecture judgment | Direct dimensional core instead of decorative Data Vault |
| Orchestration | Dagster asset graph spanning acquisition, landing, dbt and contract publication |
| Governance | Source-to-report reconciliation, restatement history and comparable-scope flags |
| BI product thinking | Peer and macro context rather than an account-code browser |
| Communication | Curated guide, ERDs, metric contracts and explicit limitations |

## What it must not become

- Not a stock-picking or investment recommendation tool.
- Not a regulatory capital calculator unless every required definition is sourced and
  reconciled.
- Not a causal model of monetary policy effects.
- Not a leaderboard built from incomparable individual and consolidated statements.
- Not KYC, customer or contract-lifecycle analytics; the public source has none of
  those grains.
- Not a dashboard containing every available COSIF account.

## Product boundary

The first release covers balance-sheet structure and macroeconomic context. Complaints,
leasing-market series, profitability and regulatory ratios are extensions only after
their definitions and comparability are proven.

## The three showcase artifacts

1. A source-to-report drill path from a Power BI reporting line to institution,
   period, COSIF account, source file and checksum.
2. A 2025 taxonomy-transition view showing which trends are comparable, mapped or
   intentionally broken.
3. A Dagster asset run and reconciliation result proving that a clean environment can
   reproduce the published marts.

