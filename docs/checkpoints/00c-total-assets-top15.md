# Checkpoint 0C — total assets and stable top 15

Updated: 2026-08-11

## Objective

Define a defensible total-assets measure for the current COSIF standard, resolve the
4010/4016 scope overlap and publish one stable 15-institution comparison population
from the latest complete official period.

## Official document and account semantics

The BCB's [balance-file documentation](https://www.bcb.gov.br/estabilidadefinanceira/balancetesbalancospatrimoniais)
defines document 4010 as the analytical trial balance produced monthly or, for
limited cases, quarterly. Document 4016 is the analytical balance sheet produced
semiannually. The current
[4010/4016 layout](https://www.bcb.gov.br/content/estabilidadefinanceira/cosif_leiautes/Leiaute_4010_xmlV0.pdf)
states that both contain individual-institution closing balances and that zero-balance
accounts may be omitted.

The official MVP files contain 4010 in all 15 months and 4016 only in June and
December. Both are base-individual positions, but admitting both would duplicate the
same semester-end institution/month. The governed rule is therefore:

- rank and report only document 4010;
- retain document 4016 as source evidence, excluded from monthly facts and ranking;
- key membership by institution CNPJ, not name or conglomerate.

The source account contract is stable across every official file:

| Account | Official source name | 0C treatment |
|---|---|---|
| `1000000009` | Ativo Realizável | Included |
| `2000000008` | Ativo Permanente | Included |
| `3000000007` | Compensação Ativa | Excluded from ordinary assets |
| `3999999009` | TOTAL GERAL DO ATIVO | Reference check only |

The [Cosif account rules](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=4858&tipo=RESOLU%C3%87%C3%83O+CMN)
distinguish patrimonial accounts from compensation accounts. The certified analytical
measure is consequently:

```text
total_assets_brl = balance(1000000009) + balance(2000000008)
```

Where the source publishes `3999999009`, the independent reference is:

```text
balance(1000000009) + balance(2000000008)
  = balance(3999999009) - balance(3000000007)
```

Missing source accounts are interpreted as zero only for the direct class-1/class-2
calculation because the official layout permits omission of zero balances. A missing
reference-total row is not interpreted as zero; that observation is simply not
reference-reconcilable.

## Reproducible implementation

`banking-data profile-cosif-population` reopens only checksum-verified archives and
profile pairs, streams the real landing contract and writes four evidence files. It
fails closed when document scope, account names, relevant row uniqueness, population
size, cutoff, period coverage, explicit top-15 components, name stability or
reference reconciliation fails.

```powershell
uv run --locked banking-data profile-cosif-population `
  --manifest artifacts/generated/cosif_download_manifest.csv `
  --profile artifacts/cosif_source_profile.csv `
  --freeze-period 202603 `
  --output-dir artifacts/generated/checkpoint-0c `
  --population-size 15 `
  --reconciliation-tolerance 1.00
```

## Results

The 202603 4010 file contains 170 institutions. All 170 explicitly report class 1;
158 explicitly report class 2. The 12 omitted class-2 balances are each below the
top-15 cutoff even if treated as zero, and every selected institution reports both
components in all 15 months.

The frozen population is:

| Rank | CNPJ | Institution | 202603 total assets (BRL) |
|---:|---|---|---:|
| 1 | `00000000` | BCO DO BRASIL S.A. | 2,494,074,551,827.91 |
| 2 | `00360305` | CAIXA ECONOMICA FEDERAL | 2,341,423,338,307.41 |
| 3 | `60701190` | ITAÚ UNIBANCO S.A. | 2,164,397,264,382.12 |
| 4 | `60746948` | BCO BRADESCO S.A. | 1,926,307,365,486.70 |
| 5 | `90400888` | BCO SANTANDER (BRASIL) S.A. | 1,213,439,691,355.34 |
| 6 | `33657248` | BNDES | 992,991,681,842.85 |
| 7 | `30306294` | BANCO BTG PACTUAL S.A. | 657,008,685,477.61 |
| 8 | `60872504` | ITAÚ UNIBANCO HOLDING S.A. | 472,332,053,191.96 |
| 9 | `58160789` | BCO SAFRA S.A. | 268,618,255,022.50 |
| 10 | `01181521` | BCO COOPERATIVO SICREDI S.A. | 227,959,636,918.20 |
| 11 | `33264668` | BCO XP S.A. | 226,236,808,448.08 |
| 12 | `02038232` | BANCO SICOOB S.A. | 203,794,132,364.99 |
| 13 | `33479023` | BCO CITIBANK S.A. | 169,214,767,576.76 |
| 14 | `92702067` | BCO DO ESTADO DO RS S.A. | 164,204,676,808.38 |
| 15 | `59588111` | BCO VOTORANTIM S.A. | 144,744,662,576.46 |

Rank 16 is BCO J.P. MORGAN S.A. at BRL 122,814,827,585.16. The cutoff gap is
BRL 21,929,834,991.30, so no tie-break rule is required.

All 15 CNPJs and source names are present and unchanged across all 15 months: 225 of
225 required member/month observations passed. The reference total is available for
190 of those observations; all 190 reconcile within BRL 1.00 and the maximum absolute
difference is BRL 0.51.

The period profile deliberately preserves reference outliers outside the selected
population, including material discrepancies in some smaller institutions. Therefore
`3999999009` is not promoted as the analytical total-assets measure and no whole-system
reconciliation claim is made.

## Interpretation boundary

This is a stable comparison population of individual legal entities. It is not a
prudential-conglomerate ranking and must not be labelled the Brazilian banking
system's market share. The set includes both Itaú Unibanco S.A. and Itaú Unibanco
Holding S.A. because the MVP contract is explicitly base-individual; economic overlap
between group entities is not removed without a governed consolidation source.

Status: **complete; all 11 machine-readable controls passed**. Checkpoint 0E can now
freeze the final source-profile decision before official warehouse certification.
