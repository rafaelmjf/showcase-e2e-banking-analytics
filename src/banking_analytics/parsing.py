"""Shared strict parsers for source-shaped values."""

from decimal import Decimal, InvalidOperation


def parse_brl_decimal(value: str) -> Decimal:
    """Parse a Brazilian decimal while preserving its exact base-10 value."""
    normalized = value.strip().replace(".", "").replace(",", ".")
    try:
        parsed = Decimal(normalized)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid Brazilian decimal: {value!r}") from exc
    if not parsed.is_finite():
        raise ValueError(f"Non-finite Brazilian decimal: {value!r}")
    return parsed
