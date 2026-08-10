# 06 — Semantic model and report

**Owner: BI layer.**

## Semantic model

Power BI imports only `marts` objects defined in `contracts/mart-schema.yml`.

The model exposes two related analytical paths:

1. Institution → reporting line → account balance.
2. Reporting month → native/aligned macroeconomic context.

Detailed account drill-through is available, but report pages lead with governed
financial questions rather than source fields.

## Candidate certified measures

Final account mappings must be proven before certification.

| Measure | Initial interpretation |
|---|---|
| Total assets | Published/mapped total assets within one reporting scope |
| Credit portfolio | Governed mapped credit accounts |
| Deposits | Governed mapped deposit accounts |
| Equity | Published/mapped equity line |
| Period and year-over-year growth | Change on a comparable scope and taxonomy basis |
| Credit share of assets | Credit portfolio divided by total assets |
| Deposit funding share | Deposits divided by the certified funding denominator |
| Equity-to-assets | Equity divided by total assets; analytical, not a regulatory capital ratio |
| Mapping coverage | Absolute mapped balance divided by eligible absolute balance |
| Restatement impact | Difference between active and prior source versions |

Every measure contract records grain, allowed scopes, sign convention, period logic,
taxonomy comparability, blank handling, owner and known limitations.

## Macro context measures

- Selic target and effective-rate context.
- Monthly and rolling-12-month inflation.
- IBC-Br level and change.
- System credit growth.
- System 90+ day delinquency.
- USD/BRL only where the selected balance-sheet story makes it relevant.

Macro series can be overlaid or used to segment periods into named regimes. They do
not prove that macro movements caused institution outcomes.

## Report pages

### 1. System and macro context

Market balance growth, asset/funding composition and system credit conditions shown
against interest-rate, inflation and activity regimes. This establishes context
before comparing institutions.

### 2. Institution and peer structure

Selected institution versus a compatible peer group: scale, growth, asset mix,
funding structure and equity. The scope selector never mixes individual and
consolidated statements.

### 3. Trust and comparability

Source freshness, active file versions, restatement impact, mapping coverage,
unmapped balances, missing periods, reconciliation status and the 2025 COSIF
transition. This page is part of the product, not appendix material.

## Interaction rules

- A visible scope selector is mandatory.
- Institution and peer comparisons use the same document and taxonomy-compatible
  period.
- Tooltips state source period separately from retrieval date.
- Drill-through identifies source file, checksum, document and COSIF accounts.
- Non-comparable periods break or annotate the trend rather than implying continuity.

## Explicitly deferred

- Profitability and return ratios until result-account periodisation is validated.
- Basel, liquidity and regulatory ratios unless sourced or reconstructed completely.
- Complaints and conduct-risk page.
- Forecasting, anomaly scoring and causal claims.
- Individual-customer, KYC and contract views.

