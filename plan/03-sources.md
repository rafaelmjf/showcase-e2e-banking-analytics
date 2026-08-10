# 03 — Sources

**Owner: data layer.**

## Source A — BCB COSIF balance files

Official periodic balance data for financial institutions and conglomerates.

| Property | Initial decision |
|---|---|
| Access | Parameterised BCB CSV ZIP downloads by reporting month and segment |
| License | Open Data Commons Open Database License (ODbL) |
| Initial period | January 2021 through latest published |
| Initial segments | Banks and prudential conglomerates |
| Source grain | Reporting date × document × institution/conglomerate × agency × COSIF account |
| Key fields | Date, document, CNPJ, agency, institution name, conglomerate code/name, taxonomy, account, account name, balance |
| Currency | BRL for the selected period |

### Confirmed current URL pattern

```text
https://www.bcb.gov.br/content/estabilidadefinanceira/cosif/
  {segment}/{yyyymm}{segment_code}.csv.zip
```

Relevant segment codes include `BANCOS`, `BLOPRUDENCIAL`, `COOPERATIVAS`,
`SOCIEDADES`, `CONSORCIOS`, `COMBINADOS` and `LIQUIDACAO`.

### Profiling evidence — 11 August 2026

- `202601BANCOS.csv.zip` was reachable and 902,381 bytes compressed.
- The expanded CSV was 6,124,204 bytes with 49,364 data rows.
- The file declares generation date `2026-08-03`.
- January, February and March 2026 bank files were reachable; April through June
  returned 404, consistent with the publication calendar at that date.
- The current file has four metadata/header lines before the data and uses semicolon
  delimiters plus comma decimals.

These figures size the source but are not yet a completeness certification.

### The 2025 boundary

The BCB introduced a new accounting standard from January 2025. Account structures
and report composition must therefore be treated as versioned taxonomies. Trend lines
crossing this boundary require one of three explicit statuses:

1. directly comparable,
2. mapped with a documented rule, or
3. not comparable.

No string-similarity mapping of account names is allowed to certify comparability.

### Source defects and risks to preserve

| Risk | Treatment |
|---|---|
| Reissued files | Append by checksum; expose active and superseded versions |
| Individual and consolidated overlap | Separate comparison scopes and prevent double counting |
| Mixed document codes | Retain document as part of the fact grain |
| Institution name changes | Type-2 dimension keyed by source identifier and effective period |
| Account taxonomy changes | Versioned account dimension and governed mapping bridge |
| Result accounts reset in June/December | Do not publish naive monthly profitability measures |
| Delayed publication | Report source period and retrieval freshness separately |
| Encoding and locale | Detect encoding; parse semicolon and comma-decimal explicitly |

## Source B — BCB SGS macroeconomic and credit series

Initial curated series registry:

| Theme | Candidate SGS code | Native frequency | Purpose |
|---|---:|---|---|
| Selic target | 432 | Event/daily observation | Monetary-policy regime |
| Effective Selic | 1178 | Daily | Realised interest-rate environment |
| IPCA | 433 | Monthly | Inflation context; verify current catalog metadata |
| IBC-Br | 24363 | Monthly | Economic activity context |
| USD/BRL | 10813 | Daily | Exchange-rate context |
| System credit balance | 20539 | Monthly | Market growth benchmark |
| System 90+ day delinquency | 21082 | Monthly | Credit-cycle risk benchmark |

Each series must have authored metadata: official title, definition, unit, frequency,
source URL, aggregation rule and whether revisions are possible. Codes are not accepted
into production from memory alone; the ingestion registry must verify the official
metadata endpoint.

## License and distribution

BCB catalog entries are ODbL. Full raw files will not be committed to Git. The public
repository will include acquisition code, synthetic contract fixtures, source
metadata and checksums. Any distributed derivative database or produced work must
carry the required attribution and license notice.

## Profiling gates before implementation

1. Download 24 consecutive months for banks and prudential conglomerates.
2. Record row counts, compressed bytes, schemas, document codes and institution counts.
3. Quantify duplicate business grains within and across segments.
4. Inspect replacements by downloading the same period on two different dates when
   possible.
5. Profile the 2024/2025 account transition and produce a first mapping-coverage table.
6. Validate every macro series, unit and alignment rule from official metadata.
7. Decide the primary comparison grain only after the duplicate analysis.

