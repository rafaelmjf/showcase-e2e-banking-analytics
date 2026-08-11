# Dagster orchestration

The asset graph uses `dagster-dlt` for the five raw landing assets and `dagster-dbt`
for the 11 staging/core models. Custom dlt asset keys match dbt source keys, so
lineage is continuous instead of showing duplicate raw tables.

`BANKING_SOURCE_MODE` defaults to `fixture`. Setting it to `official` preserves the
same asset keys but requires every persisted evidence input before the code location
will load:

```powershell
$env:BANKING_SOURCE_MODE = "official"
$env:BANKING_OFFICIAL_COSIF_MANIFEST = "artifacts/generated/cosif_download_manifest.csv"
$env:BANKING_OFFICIAL_COSIF_PROFILE = "artifacts/generated/cosif_source_profile.csv"
$env:BANKING_OFFICIAL_MACRO_OBSERVATIONS = "artifacts/generated/macro_observations.csv"
$env:BANKING_OFFICIAL_MACRO_PROFILE = "artifacts/generated/macro_profile.csv"
$env:BANKING_OFFICIAL_MACRO_START = "2025-01-01"
$env:BANKING_OFFICIAL_MACRO_END = "2026-03-31"
```

Official mode exposes `official_end_to_end`; fixture mode exposes
`fixture_end_to_end`. An unknown mode or missing evidence path fails definition
validation before a run begins.

Prepare the dbt manifest, validate the code location and execute the graph:

```powershell
uv run --locked dbt parse --project-dir dbt --profiles-dir dbt
uv run --locked dagster definitions validate -f orchestration/definitions.py -a defs
uv run --locked dagster job execute `
  -f orchestration/definitions.py -a defs -j fixture_end_to_end
```

The graph is synthetic until the official source gates pass.
