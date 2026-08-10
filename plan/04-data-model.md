# 04 — Data model

**Owner: data layer.**

## Modelling strategy

Use source-evidence landing, a small canonical accounting core and consumption-first
dimensional marts. The MVP covers only current-standard individual bank data from
January 2025 onward.

## Raw landing

### `raw_cosif.balance_row`

One source row augmented with:

- `source_url`
- `source_period`
- `source_checksum`
- `source_generated_at`
- `retrieved_at`
- `file_row_number`
- dlt load identifiers

The landing identity is `source_checksum + file_row_number`; it is not the analytical
business key.

### `raw_macro.observation`

One fetched observation with series code, source date, raw value, retrieval timestamp
and dlt load identifiers. Series metadata lands separately.

## Canonical core

| Object | Grain and purpose |
|---|---|
| `core.cosif_file_manifest` | One fetched period/checksum and its completion/active status |
| `core.bank_period` | One bank CNPJ and reporting month |
| `core.cosif_account` | One current-standard account code and hierarchy attributes |
| `core.account_balance` | Active file × month × document × bank × agency × account |
| `core.reporting_line_mapping` | Current COSIF account × governed reporting line |
| `core.macro_series` | One verified series and its semantic metadata |
| `core.macro_observation` | Series × source observation date |

Canonical selection is deterministic and traceable to the source checksum. Historical
file evidence remains available without becoming an MVP analytical fact.

## Consumption marts

### Dimensions

| Dimension | Notes |
|---|---|
| `dim_bank` | Stable top-15 population; CNPJ, display name and source-period attributes |
| `dim_cosif_account` | Current-standard hierarchy and account description |
| `dim_reporting_line` | Small business-facing set needed by the report |
| `dim_document` | Document code and allowed interpretation |
| `dim_macro_series` | Definition, unit, frequency and monthly rule |
| `dim_date` | Day, month, quarter and year attributes |
| `dim_source_file` | URL, checksum, generation date, retrieval date and active status |

### Facts and bridge

| Object | Grain |
|---|---|
| `fact_account_balance` | Bank × report month × document × account × active source file |
| `bridge_account_reporting_line` | Current account × reporting line |
| `fact_reporting_line_balance` | Bank × report month × document × reporting line |
| `fact_macro_observation` | Macro series × source observation date |
| `fact_monthly_economic_context` | Month × curated macro series after documented alignment |

`fact_reporting_line_balance` is an auditable convenience fact. It must reconcile to
contributing account balances and expose the mapping version.

## Hierarchy and sign rules

1. Account hierarchy comes from the current official COSIF structure.
2. Raw balances retain the published sign.
3. Presentation signs are defined by reporting line and never overwrite raw balances.
4. Parent totals are not presented as recomputed official totals unless reconciled.
5. Unmapped balances remain visible and count toward mapping-coverage controls.

## Top-15 rule

Select the top 15 banks by certified total assets in the latest complete period at
contract freeze. Persist that membership as an authored, reproducible model so the
same banks are compared over every MVP month. Banks outside the set remain in raw and
core data but are excluded from the primary report marts.

## Unknown conventions

- Unknown members are explicit dimension rows.
- Unmapped accounts map to an explicit `Unmapped` reporting line in aggregated views.
- Missing source periods remain missing; they are never converted to reported zero.
- A failed or unavailable future-period URL is a manifest state, not a balance row.

## Deferred model objects

- Prudential-conglomerate facts and scope bridges
- Pre-2025 account versions and cross-taxonomy mappings
- Restatement fact and bi-temporal consumption views
- Complaint, Pix, ESTBAN, lending-rate and IF.data facts

