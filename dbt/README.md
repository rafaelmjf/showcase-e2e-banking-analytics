# dbt project

This project transforms dlt landing tables into source-faithful staging and a small
canonical core. The current executable sample is synthetic and remains marked as a
fixture throughout the lineage.

```powershell
uv run --locked dbt build --project-dir dbt --profiles-dir dbt
uv run --locked dbt docs generate --project-dir dbt --profiles-dir dbt
uv run --locked dbt docs serve --project-dir dbt --profiles-dir dbt --port 8081
```

Marts and the top-15 population are intentionally withheld until official WP0
checkpoints 0B and 0C pass. The generated catalog therefore describes five raw
sources, five staging models and six canonical core models only.
