from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from banking_analytics.fixtures import (
    build_cosif_fixture_manifests,
    build_macro_metadata_fixture,
    parse_brl_decimal,
    read_cosif_fixture,
    read_macro_fixture,
)
from banking_analytics.pipelines.cosif import cosif_balance_row, cosif_landing_source
from banking_analytics.pipelines.fixtures import build_macro_fixture_fetches
from banking_analytics.pipelines.macro import macro_landing_source, sgs_observation

ROOT = Path(__file__).resolve().parents[1]


def test_brazilian_decimal_parser_is_exact() -> None:
    assert parse_brl_decimal("1.234.567,89") == Decimal("1234567.89")


def test_cosif_fixture_has_stable_identity_and_reconciles() -> None:
    rows = read_cosif_fixture(ROOT / "fixtures" / "cosif_balance_rows.csv")
    manifests = build_cosif_fixture_manifests(rows)

    assert len(rows) == 24
    assert len(manifests) == 2
    assert {manifest["row_count"] for manifest in manifests} == {12}
    assert len(list(cosif_balance_row(rows))) == 24
    assert set(cosif_landing_source(manifests, rows).resources) == {
        "cosif_file_manifest",
        "cosif_balance_row",
    }

    by_bank_month: dict[tuple[str, str], dict[str, Decimal]] = defaultdict(dict)
    for row in rows:
        by_bank_month[(str(row["source_period"]), str(row["cnpj"]))][str(row["conta"])] = (
            row["saldo"]  # type: ignore[assignment]
        )
    for balances in by_bank_month.values():
        assert balances["1000000009"] + balances["2000000008"] == (
            balances["3999999009"] - balances["3000000007"]
        )


def test_dlt_column_hints_do_not_collide() -> None:
    cosif_schema = cosif_balance_row([]).compute_table_schema()["columns"]
    macro_schema = sgs_observation([]).compute_table_schema()["columns"]

    assert set(cosif_schema) == {
        "source_period",
        "documento",
        "cnpj",
        "agencia",
        "nome_instituicao",
        "cod_congl",
        "nome_congl",
        "taxonomia",
        "conta",
        "nome_conta",
        "saldo_raw",
        "saldo",
        "source_url",
        "source_checksum",
        "source_generated_at",
        "retrieved_at_utc",
        "file_row_number",
    }
    assert set(macro_schema) == {
        "series_code",
        "source_observation_date",
        "report_month",
        "value_raw",
        "value",
        "retrieved_at_utc",
        "source_url",
        "fixture",
    }
    assert all(key == value["name"] for key, value in cosif_schema.items())
    assert all(key == value["name"] for key, value in macro_schema.items())


def test_macro_fixture_covers_registry_and_months() -> None:
    observations = read_macro_fixture(ROOT / "fixtures" / "macro_observations.csv")
    metadata = build_macro_metadata_fixture(ROOT / "config" / "macro_series_registry.csv")
    fetches = build_macro_fixture_fetches(observations)

    assert len(observations) == 15
    assert len(metadata) == 5
    assert len(fetches) == 5
    assert {row["series_code"] for row in metadata} == {
        "4189",
        "433",
        "24363",
        "20539",
        "21082",
    }
    assert {row["response_count"] for row in fetches} == {3}
    assert set(macro_landing_source(metadata, observations, fetches).resources) == {
        "sgs_series_metadata",
        "sgs_observation",
        "sgs_fetch_manifest",
    }
