# 06 — Semantic model and report

**Owner: BI layer.**

## Public product

**Inside Brazil's Largest Banks: Lending, Funding and the Interest-Rate Cycle**

The report explains the selected banks in familiar language. COSIF account codes are
available through drill-through and trust details, not used as the page hierarchy.

Power BI imports only objects defined in `contracts/mart-schema.yml`.

## Candidate certified measures

Final account mappings must be proven before certification.

| Measure | Initial interpretation |
|---|---|
| Total assets | Certified current-standard total-assets line |
| Credit portfolio | Governed mapped credit accounts |
| Deposits | Governed mapped deposit accounts |
| Equity | Published/mapped equity line |
| Period and year-over-year growth | Change within the January 2025+ comparable period |
| Credit share of assets | Credit portfolio divided by total assets |
| Deposit funding share | Deposits divided by its certified denominator |
| Equity-to-assets | Analytical structure measure, not a regulatory capital ratio |
| Comparison-population share | Bank amount divided by the stable top-15 total |
| Mapping coverage | Mapped eligible balance divided by total eligible balance |

Every measure contract records grain, sign convention, period logic, blank handling,
owner and known limitations.

## Monthly context

- Selic interest-rate environment
- Monthly and rolling-12-month IPCA
- IBC-Br level/change
- System credit growth
- System 90+ day delinquency

Context can be shown beside banking trends or used for named periods. It does not
prove that macro movements caused bank outcomes.

## Report page 1 — Banking pulse

Answers: how large is the selected market, who is growing, where is the money deployed
and what was the macro environment?

Suggested content:

- Selected-population assets, credit, deposits and equity
- Growth and share change by bank
- Asset/funding mix
- A compact interest-rate, inflation and credit-cycle timeline

## Report page 2 — Compare banks

Answers: how does a selected bank differ from peers?

Suggested content:

- Bank versus top-15 median and selected peers
- Scale, lending growth, deposit funding and equity structure
- Trend and composition comparison
- Drill-through to contributing reporting lines and source accounts

## Compact trust panel

Available from both pages rather than built as a third full report page:

- Latest source period and retrieval date
- Active file checksum
- Reconciliation status
- Mapping coverage and unmapped amount
- Missing periods
- Scope statement: individual banks, January 2025 onward, stable top 15

## Interaction rules

- A visible bank and peer selector is mandatory.
- The comparison population stays fixed across the report period.
- Tooltips state source period separately from retrieval date.
- Drill-through identifies source file, checksum, document and COSIF accounts.
- Missing values are not displayed as zero.

## Explicitly deferred

- Profitability and return ratios until result-account periodisation is validated.
- Basel, liquidity and regulatory ratios until IF.data is added and governed.
- Complaints, lending rates, Pix and geographic banking pages.
- Pre-2025 history and prudential-conglomerate scope.
- Forecasting, anomaly scoring and causal claims.

