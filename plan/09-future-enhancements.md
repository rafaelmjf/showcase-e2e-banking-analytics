# 09 — Future enhancements

These are independent additions after the MVP. None is required for the first mart
contract, report or definition of done.

## Prioritisation rule

An enhancement must add a new question a reader can understand—not merely another
source or technology. Before acceptance it needs a source profile, stable join key,
license confirmation, named report outcome and evidence that it does not compromise
the existing mart contract.

## Priority 1 — Customer trust and conduct

### BCB ranking of complaints

Official source:
https://dadosabertos.bcb.gov.br/dataset/ranking-de-instituicoes-por-indice-de-reclamacoes

The source publishes institution-level complaint indices, complaint counts by type,
confirmed irregularities and customer denominators from systems including CCS, SCR
and FGC. The historical page currently exposes quarterly files through 2026.

Potential questions:

- Which banks have the highest confirmed complaints per million customers?
- Are complaint trends aligned with growth in customers or balance-sheet scale?
- Which irregularity categories drive deterioration?

Candidate grain: institution/conglomerate × period × complaint/irregularity category.

Gate: confirm stable CNPJ/conglomerate identifiers and avoid comparing raw complaint
counts without the published customer denominator.

Why first: it is the most understandable extension and adds a non-financial outcome.

## Priority 2 — Customer pricing

### Lending rates by financial institution and modality

Official source:
https://dadosabertos.bcb.gov.br/dataset/taxas-de-juros-de-operacoes-de-credito

The BCB publishes weighted average effective borrowing costs by institution and credit
modality for the reported five-business-day window.

Potential questions:

- How do personal-loan, vehicle-finance and credit-card rates differ across banks?
- Does a bank's funding structure provide useful context for its published rates?
- Which institutions consistently price above or below the visible comparison group?

Candidate grain: institution × reference window × borrower type × credit modality.

Gate: profile historical retention. If the API is only a rolling snapshot, label the
feature as current pricing or begin prospective collection; do not invent a backfill.

## Priority 3 — Digital banking reach and risk

### Pix statistics

Official source: https://dadosabertos.bcb.gov.br/dataset/pix

Monthly data starts in November 2020 and includes Pix keys by participant, transaction
volume/value, municipal transactions and periodic Pix fraud/MED information.

Potential questions:

- Which participants hold the largest Pix key base?
- How is Pix usage distributed geographically and between people/businesses?
- How are contested or fraudulent Pix transactions evolving?

Candidate grains vary by resource: participant × month × key type; municipality ×
month × customer type; and period × fraud category.

Gate: create a reviewed participant-to-bank identifier bridge and keep municipality,
participant and system-level metrics in separate facts.

## Priority 4 — Geographic banking footprint

### ESTBAN — monthly banking statistics by municipality

Official source:
https://www.bcb.gov.br/estatisticas/estatisticabancariamunicipios

ESTBAN publishes monthly balances for principal banking rubrics by institution and
municipality, with IBGE municipality codes and optional agency-level files.

Potential questions:

- Where are deposits and credit concentrated geographically?
- Which banks have the broadest or most concentrated municipal footprint?
- How does banking activity differ across regions?

Candidate grain: month × institution × municipality × ESTBAN rubric, with agency as
an optional deeper grain.

Gate: the public page advertises only the last six published months. Confirm a lawful,
stable historical acquisition path before presenting long-term trends.

## Priority 5 — Governed financial and regulatory indicators

### IF.data selected financial-institution data

Official source:
https://dadosabertos.bcb.gov.br/dataset/ifdata---dados-selecionados-de-instituies-financeiras

IF.data provides quarterly OData/JSON reports sourced from COSIF and SCR, with history
from March 2000 and current institution/conglomerate structures. It can add curated
profitability, credit-quality and regulatory views without reconstructing every ratio
from raw accounts.

Potential questions:

- How do profitability, credit quality and regulatory indicators differ by peer?
- Do the selected IF.data indicators reconcile directionally or exactly to COSIF
  components where definitions overlap?

Gate: use published metrics with their official definitions. Do not duplicate a COSIF
measure under a second name or mix institution and conglomerate scopes.

## Foundation enhancement — institution registry

### Institutions in operation

Official source:
https://bcb.gov.br/estabilidadefinanceira/relacao_instituicoes_funcionamento

Monthly files provide CNPJ, institution name, segment and address. This can enrich the
bank dimension and improve name/history handling without adding a report page.

Gate: add only if profiling proves that the COSIF files lack stable classification or
address attributes needed by an accepted enhancement.

## Lower-priority source families

- BCB payment-method and SPI statistics for system-level payment adoption.
- Term-deposit and financial-letter statistics for funding-market context.
- Leasing and vehicle-finance SGS series for a separate asset-finance market view.
- Pre-2025 COSIF history, taxonomy bridging and prudential-conglomerate comparison.

These may be valuable, but each risks turning the focused bank comparison into a broad
financial-system portal. They require a new report question and separate acceptance
decision.

