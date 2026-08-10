# 04 — Data model

**Owner: data layer.**

## Modelling strategy

Use an append-preserved raw layer, a canonical accounting core and consumption-first
dimensional marts. The model must keep source account detail available while preventing
Power BI users from accidentally combining incompatible reporting scopes or taxonomy
versions.

## Raw landing

### `raw_cosif.balance_row`

One row exactly as published, augmented with:

- `source_url`
- `source_period`
- `source_segment`
- `source_checksum`
- `source_generated_at`
- `retrieved_at`
- `file_row_number`
- dlt load identifiers

The landing key is `source_checksum + file_row_number`. It is not the analytical
business key.

### `raw_macro.observation`

One fetched observation with series code, observation date, raw value, retrieval
timestamp and dlt load identifiers. Series metadata is landed separately from values.

## Canonical core

| Object | Grain and purpose |
|---|---|
| `core.cosif_file_version` | One downloaded file checksum; status and supersession chain |
| `core.institution_period` | One source institution identity and reporting period |
| `core.cosif_account_version` | One account code within a taxonomy version and effective interval |
| `core.account_balance` | Active file version × period × scope × document × institution × agency × account |
| `core.reporting_line_mapping` | COSIF account version × governed reporting line × effective interval |
| `core.macro_series` | One verified SGS series and its semantic metadata |
| `core.macro_observation` | Series × native observation date |

Canonical selection is deterministic and traceable. Superseded values remain in raw
and audit objects.

## Consumption marts

### Dimensions

| Dimension | Notes |
|---|---|
| `dim_financial_institution` | Type 2; CNPJ root, name, conglomerate membership and comparison scope |
| `dim_cosif_account` | Versioned account hierarchy, effective dates and taxonomy version |
| `dim_reporting_line` | Curated business-facing lines such as total assets, credit, deposits and equity |
| `dim_document` | Document code, reporting scope and allowed comparisons |
| `dim_macro_series` | Definition, unit, frequency and monthly-alignment method |
| `dim_date` | Day, month, quarter and year attributes |
| `dim_source_file` | URL, checksum, generation date, retrieval date and active status |

### Facts and bridges

| Object | Grain |
|---|---|
| `fact_account_balance` | Institution × report period × document × account × source version |
| `bridge_account_reporting_line` | Account taxonomy version × reporting line × effective interval |
| `fact_reporting_line_balance` | Institution × period × document × curated reporting line |
| `fact_macro_observation` | Macro series × native observation date |
| `fact_monthly_economic_context` | Month × curated macro series after documented alignment |
| `fact_restatement` | Business grain × old file version × new file version |

`fact_reporting_line_balance` is an auditable convenience fact. It must reconcile to
the contributing account balances and expose the mapping version used.

## Hierarchy and sign rules

1. Account hierarchy comes from official COSIF structure and effective dates, not
   fixed-position guesses alone.
2. Raw balances retain the published sign.
3. Presentation signs, if required, are defined by reporting line and never overwrite
   raw balances.
4. Parent totals are not recomputed and presented as official unless reconciled to
   the published parent account.
5. Mapping coverage and unmapped balances are visible measures.

## Comparison scopes

Every fact row carries a scope such as individual institution, prudential conglomerate
or cooperative combination. Semantic measures must require a single compatible scope.
The model will not sum individual banks and their parent conglomerates into one total.

## Unknown and non-comparable conventions

- Unknown members are explicit dimension rows.
- Unmapped COSIF accounts remain in `fact_account_balance` and map to an explicit
  `Unmapped` reporting line in aggregated views.
- Cross-taxonomy status is `direct`, `mapped` or `not_comparable`.
- A missing source period is distinguished from a reported zero.

