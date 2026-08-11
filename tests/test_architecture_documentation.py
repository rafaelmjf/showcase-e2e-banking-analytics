from pathlib import Path


def test_architecture_lists_every_implemented_data_asset() -> None:
    architecture = Path("docs/architecture.md").read_text(encoding="utf-8")
    dbt_models = {
        path.stem
        for path in Path("dbt/models").rglob("*.sql")
        if path.is_file()
    }
    raw_tables = {
        "cosif_file_manifest",
        "cosif_balance_row",
        "sgs_series_metadata",
        "sgs_observation",
        "sgs_fetch_manifest",
    }

    missing = sorted(name for name in dbt_models | raw_tables if name not in architecture)

    assert len(dbt_models) == 11
    assert not missing, f"Architecture guide is missing implemented assets: {missing}"


def test_architecture_keeps_unimplemented_consumption_layer_explicit() -> None:
    architecture = Path("docs/architecture.md").read_text(encoding="utf-8")

    assert "The current implementation stops at the canonical core" in architecture
    assert "Full official Dagster + dbt run | Defined; not certified" in architecture
    assert "Power BI TMDL, pages and trust panel | Planned" in architecture
