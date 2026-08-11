# dbt project

This project transforms dlt landing tables into source-faithful staging, canonical
core and certified dimensional reporting marts.

```powershell
uv run --locked dbt build --project-dir dbt --profiles-dir dbt
uv run --locked dbt docs generate --project-dir dbt --profiles-dir dbt
uv run --locked dbt docs serve --project-dir dbt --profiles-dir dbt --port 8081
```

The graph contains five staging models, seven core models, twelve marts and two
governance seeds. Its 188 tests cover source identities, selected-file reconciliation,
stable population, the exact seven-account mapping, dimensional grains, foreign-key
relationships, four-line coverage and account-to-reporting-line reconciliation.

Both fixture and official builds pass `214/214`. Official-only tests are conditional
on fixture lineage, so fixture CI remains useful without pretending to certify live
coverage. The stable BI boundary is frozen in
[`contracts/mart-schema.yml`](../contracts/mart-schema.yml).
