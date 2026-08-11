"""dlt resources for source-faithful COSIF landing."""

from __future__ import annotations

from collections.abc import Iterable

import dlt

STRICT_COLUMNS = {"tables": "evolve", "columns": "freeze", "data_type": "freeze"}


def _text(*, nullable: bool = False) -> dict[str, object]:
    """Return a fresh dlt hint because dlt annotates column dictionaries in place."""
    return {"data_type": "text", "nullable": nullable}

MANIFEST_COLUMNS = {
    "source_period": _text(),
    "source_url": _text(),
    "source_checksum": _text(),
    "source_generated_at": {"data_type": "date", "nullable": False},
    "retrieved_at_utc": {"data_type": "timestamp", "nullable": False, "timezone": True},
    "status": _text(),
    "is_active": {"data_type": "bool", "nullable": False},
    "row_count": {"data_type": "bigint", "nullable": False},
    "fixture": {"data_type": "bool", "nullable": False},
}

BALANCE_COLUMNS = {
    "source_period": _text(),
    "documento": _text(),
    "cnpj": _text(),
    "agencia": _text(nullable=True),
    "nome_instituicao": _text(),
    "cod_congl": _text(nullable=True),
    "nome_congl": _text(nullable=True),
    "taxonomia": _text(nullable=True),
    "conta": _text(),
    "nome_conta": _text(),
    "saldo_raw": _text(),
    "saldo": {"data_type": "decimal", "nullable": False, "precision": 38, "scale": 2},
    "source_url": _text(),
    "source_checksum": _text(),
    "source_generated_at": {"data_type": "date", "nullable": False},
    "retrieved_at_utc": {"data_type": "timestamp", "nullable": False, "timezone": True},
    "file_row_number": {"data_type": "bigint", "nullable": False},
}


@dlt.resource(
    name="cosif_file_manifest",
    write_disposition="merge",
    primary_key=["source_checksum"],
    columns=MANIFEST_COLUMNS,
    schema_contract=STRICT_COLUMNS,
)
def cosif_file_manifest(rows: Iterable[dict[str, object]]):
    """One immutable source-version identity plus active/completion state."""
    yield from rows


@dlt.resource(
    name="cosif_balance_row",
    write_disposition="merge",
    primary_key=["source_checksum", "file_row_number"],
    columns=BALANCE_COLUMNS,
    schema_contract=STRICT_COLUMNS,
)
def cosif_balance_row(rows: Iterable[dict[str, object]]):
    """Source-faithful rows with raw and typed balances side by side."""
    yield from rows


@dlt.source(name="cosif_landing")
def cosif_landing_source(
    manifests: Iterable[dict[str, object]], balances: Iterable[dict[str, object]]
):
    """Return the bounded COSIF raw landing source."""
    return cosif_file_manifest(manifests), cosif_balance_row(balances)
