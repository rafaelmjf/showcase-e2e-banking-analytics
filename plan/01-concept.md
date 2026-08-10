# 01 — Concept

## Public-facing question

> **Where do Brazil's largest banks get their money, where do they put it, and how
> has that changed under high interest rates?**

Working product title: **Inside Brazil's Largest Banks: Lending, Funding and the
Interest-Rate Cycle**.

## Problem statement

Official bank disclosures are public but organised for regulatory reporting rather
than understandable comparison. A newcomer should not need to understand COSIF,
document codes or prudential consolidation before learning whether a bank is growing,
expanding lending or changing how it funds itself.

The analytical problem is therefore not obtaining more financial fields. It is
turning official balances into a small number of comparable, traceable questions
without hiding the accounting evidence underneath them.

## Proposed solution

Build a focused end-to-end product covering Brazil's largest banks from January 2025
onward. It combines current-standard COSIF balances with a small monthly macroeconomic
context set.

The MVP answers:

1. Which large banks expanded or contracted their balance sheets and lending?
2. Where is each bank's money deployed across the certified asset categories?
3. How do deposits, equity and other certified funding components differ by bank?
4. Which banks gained or lost share within the selected comparison population?
5. How did these patterns move alongside interest rates, inflation, economic activity
   and system credit conditions?
6. How complete, fresh and reconciled is the underlying account mapping?

## MVP boundary

| Area | Included |
|---|---|
| Institutions | Individual banks only; stable top 15 selected from latest complete period |
| Time | January 2025 through latest published |
| Accounting | Current COSIF standard only |
| Macroeconomics | Small curated monthly context set |
| Report | Two pages plus compact trust panel |
| History controls | File checksum and load manifest, without restatement analytics |

## Portfolio thesis

| Claim | Evidence |
|---|---|
| Financial-domain modelling | Governed mapping from current COSIF accounts to a few understandable reporting lines |
| Data engineering | Metadata-driven dlt ingestion of parameterised ZIP and SGS endpoints |
| Architecture judgment | Direct dimensional core instead of decorative Data Vault |
| Orchestration | Dagster asset graph spanning acquisition, landing, dbt and contract publication |
| Governance | Source-to-report reconciliation, mapping coverage and scope controls |
| BI product thinking | Human questions lead; regulatory account codes remain drill-through evidence |
| Communication | Curated guide, ERDs, metric contracts and explicit limitations |

## What it must not become

- Not a stock-picking or investment recommendation tool.
- Not a regulatory-capital calculator.
- Not a causal model of monetary policy effects.
- Not a leaderboard built from incompatible reporting scopes.
- Not KYC, customer or contract-lifecycle analytics.
- Not a dashboard containing every available COSIF account.
- Not a pre/post-2025 taxonomy harmonisation project in the MVP.

## The three showcase artifacts

1. A clear bank-comparison page understandable without prior COSIF knowledge.
2. A drill path from reporting line to bank, month, account, source file and checksum.
3. A Dagster run and reconciliation result proving clean reproducibility.

## Later product directions

After the MVP, separate enhancements can add customer trust, lending prices, Pix
adoption, geographic reach, regulatory indicators or pre-2025 history. They are
prioritised in [09-future-enhancements.md](09-future-enhancements.md) and do not expand
the MVP definition of done.

