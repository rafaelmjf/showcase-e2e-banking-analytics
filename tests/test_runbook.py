from pathlib import Path

from typer.main import get_command

from banking_analytics.cli import app


def test_runbook_covers_every_operational_cli_stage() -> None:
    runbook = Path("docs/runbook.md").read_text(encoding="utf-8")
    registered = set(get_command(app).commands)  # type: ignore[attr-defined]
    required = {
        "source-catalog",
        "download-cosif",
        "profile-cosif",
        "profile-cosif-population",
        "profile-sgs",
        "assess-readiness",
        "assess-source-profile",
        "certify-official-warehouse",
        "certify-reporting-marts",
        "load-official",
        "load-fixtures",
        "verify-fixtures",
    }

    assert required <= registered
    assert all(f"banking-data {command}" in runbook for command in required)


def test_runbook_orders_readiness_before_official_load() -> None:
    runbook = Path("docs/runbook.md").read_text(encoding="utf-8")

    assert runbook.index("banking-data assess-readiness") < runbook.index(
        "banking-data load-official"
    )
    assert "never falls back to fixtures" in runbook
    assert "Power BI may bind to the certified mart contract" in runbook
