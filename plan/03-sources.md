# 03 — Sources

**Owner: data layer.**

## Source A — BCB COSIF bank balance files

Official periodic balance data for financial institutions.

| Property | MVP decision |
|---|---|
| Access | Parameterised BCB CSV ZIP downloads by reporting month and segment |
| License | Open Data Commons Open Database License (ODbL) |
| Period | January 2025 through latest published |
| Segment | Banks (`BANCOS`) only |
| Source grain | Reporting date × document × institution × agency × COSIF account |
| Key fields | Date, document, CNPJ, agency, institution name, taxonomy, account, account name, balance |
| Currency | BRL |

### Confirmed current URL pattern

```text
https://www.bcb.gov.br/content/estabilidadefinanceira/cosif/
  Bancos/{yyyymm}BANCOS.csv.zip
```

Other segments exist but are not MVP inputs.

### Profiling evidence — 11 August 2026

- `202601BANCOS.csv.zip` was reachable and 902,381 bytes compressed.
- The expanded CSV was 6,124,204 bytes with 49,364 data rows.
- The file declares generation date `2026-08-03`.
- January, February and March 2026 bank files were reachable; April through June
  returned 404, consistent with the publication calendar at that date.
- The current file has four metadata/header lines before the data and uses semicolon
  delimiters plus comma decimals.

These figures size the source but are not a completeness certification.

### MVP source controls

| Risk | Treatment |
|---|---|
| Reissued file | Store URL, checksum, generation date and retrieval time in the manifest; load the latest complete file |
| Mixed document codes | Retain document as part of the fact grain |
| Institution name change | Preserve CNPJ and source-period name; promote to Type 2 only if profiling proves necessary |
| Encoding and locale | Detect encoding; parse semicolon and comma-decimal explicitly |
| Delayed publication | Report source period separately from retrieval freshness |
| Missing account mapping | Retain account and expose unmapped coverage |

The MVP does not publish a restatement fact or a cross-taxonomy mapping. File evidence
is retained so those features can be added later without reacquiring history.

## Source B — BCB monthly macroeconomic and credit context

The MVP publishes a deliberately small monthly set:

| Theme | Candidate source | MVP treatment |
|---|---|---|
| Selic | SGS 4189 or an explicitly month-aligned target series | One monthly interest-rate context value |
| IPCA | SGS 433 | Monthly inflation and rolling 12-month measure |
| Economic activity | SGS 24363, IBC-Br | Monthly level and change |
| System credit balance | SGS 20539 | Monthly market growth benchmark |
| System 90+ day delinquency | SGS 21082 | Monthly credit-cycle risk benchmark |

Exact codes, definitions, units and aggregation rules must be verified from official
metadata during profiling. USD/BRL is excluded unless the selected balance-sheet story
shows a clear need.

Each accepted series receives authored metadata: official title, definition, unit,
frequency, source URL, monthly rule and revision behavior.

## Top-15 comparison population

The selected institutions are the top 15 banks by the certified total-assets line in
the latest complete source period available when the MVP contract is frozen. That set
is held stable across earlier MVP months so entry and exit do not create artificial
market-share changes. The report states that it is a comparison population, not the
entire Brazilian financial system.

## License and distribution

BCB catalog entries are ODbL. Full raw files are not committed to Git. The public
repository includes acquisition code, synthetic contract fixtures, source metadata
and checksums. Public produced works carry BCB and ODbL attribution.

## Profiling gates before implementation

1. Download every available `BANCOS` month from January 2025 onward.
2. Record rows, bytes, columns, document codes, institutions and accounts by month.
3. Confirm the current COSIF structure is internally consistent over the period.
4. Identify the official total-assets account and select the stable top 15.
5. Draft only the reporting lines needed by the two report pages.
6. Validate each macro series, unit and monthly rule from official metadata.
7. Publish a source profile before freezing dbt models or report measures.

## Future source families

Institution-level complaints, IF.data, lending rates, Pix, ESTBAN and institution
registry data are intentionally deferred. See [09-future-enhancements.md](09-future-enhancements.md).

