# Dagster orchestration

The fixture-backed asset graph uses `dagster-dlt` for the five raw landing assets and
`dagster-dbt` for the 11 staging/core models. Custom dlt asset keys match dbt source
keys, so lineage is continuous instead of showing duplicate raw tables.

Prepare the dbt manifest, validate the code location and execute the graph:

```powershell
uv run --locked dbt parse --project-dir dbt --profiles-dir dbt
uv run --locked dagster definitions validate -f orchestration/definitions.py -a defs
uv run --locked dagster job execute `
  -f orchestration/definitions.py -a defs -j fixture_end_to_end
```

The graph is synthetic until the official source gates pass.
