import hashlib
import zipfile
from decimal import Decimal
from pathlib import Path

from banking_analytics.sources.cosif import DownloadRecord, ProfileRecord, profile_downloads
from banking_analytics.sources.cosif_population import (
    PopulationAnalysis,
    PopulationControl,
    profile_cosif_population,
    write_population_analysis,
)


def _official_evidence(
    tmp_path: Path,
    *,
    missing_component: tuple[str, str] | None = None,
    reference_difference: tuple[str, str, Decimal] | None = None,
) -> tuple[list[DownloadRecord], list[ProfileRecord]]:
    downloads: list[DownloadRecord] = []
    for period in ("202505", "202506"):
        rows = [
            "#Arquivo de balancetes das instituições",
            "#Gerado em 03/03/2025",
            "#Valores em reais",
            (
                "#DATA_BASE;DOCUMENTO;CNPJ;AGENCIA;NOME_INSTITUICAO;COD_CONGL;"
                "NOME_CONGL;TAXONOMIA;CONTA;NOME_CONTA;SALDO"
            ),
        ]
        documents = ("4010", "4016") if period == "202506" else ("4010",)
        for document in documents:
            for number in range(1, 17):
                cnpj = f"{number:08d}"
                total_assets = Decimal(2_000 - number * 50)
                realizable = total_assets * Decimal("0.9")
                permanent = total_assets - realizable
                compensation = Decimal("10.00")
                total_general = total_assets + compensation
                if reference_difference and reference_difference[:2] == (period, cnpj):
                    total_general -= reference_difference[2]
                balances = (
                    ("1000000009", "Ativo Realizável", realizable),
                    ("2000000008", "Ativo Permanente", permanent),
                    ("3000000007", "Compensação Ativa", compensation),
                    ("3999999009", "TOTAL GERAL DO ATIVO", total_general),
                )
                for account_code, account_name, amount in balances:
                    if missing_component == (period, cnpj) and account_code == "2000000008":
                        continue
                    amount_raw = f"{amount:.2f}".replace(".", ",")
                    rows.append(
                        f"{period};{document};{cnpj};;BANCO {number:02d};;;"
                        f"BANCOS MULTIPLOS;{account_code};{account_name};{amount_raw}"
                    )
        archive_path = tmp_path / f"{period}.zip"
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(f"{period}BANCOS.csv", "\r\n".join(rows).encode("cp1252"))
        body = archive_path.read_bytes()
        downloads.append(
            DownloadRecord(
                period=period,
                source_url=f"https://example.test/{period}.zip",
                status="complete",
                http_status=200,
                retrieved_at_utc="2026-08-11T00:00:00+00:00",
                sha256=hashlib.sha256(body).hexdigest(),
                compressed_bytes=len(body),
                archive_path=str(archive_path),
                member_count=1,
                error=None,
            )
        )
    return downloads, profile_downloads(downloads)


def _control(analysis: PopulationAnalysis, name: str) -> PopulationControl:
    return next(control for control in analysis.controls if control.control_name == name)


def test_population_profile_uses_4010_and_freezes_latest_top_15(tmp_path: Path) -> None:
    downloads, profiles = _official_evidence(tmp_path)

    analysis = profile_cosif_population(downloads, profiles)

    assert analysis.passed
    assert len(analysis.period_profiles) == 2
    assert analysis.period_profiles[-1].document_4016_institutions == 16
    assert len(analysis.population) == 15
    assert len(analysis.monthly_balances) == 30
    assert analysis.population[0].institution_cnpj == "00000001"
    assert analysis.population[-1].institution_cnpj == "00000015"
    assert {row.document_code for row in analysis.monthly_balances} == {"4010"}
    assert {row.institution_cnpj for row in analysis.monthly_balances} == {
        f"{number:08d}" for number in range(1, 16)
    }


def test_population_gate_fails_when_a_frozen_member_lacks_a_component(
    tmp_path: Path,
) -> None:
    downloads, profiles = _official_evidence(
        tmp_path, missing_component=("202505", "00000001")
    )

    analysis = profile_cosif_population(downloads, profiles)

    control = _control(analysis, "top_population_components_are_explicit")
    assert control.passed is False
    assert analysis.passed is False


def test_population_gate_fails_material_reference_difference(tmp_path: Path) -> None:
    downloads, profiles = _official_evidence(
        tmp_path,
        reference_difference=("202505", "00000001", Decimal("2.00")),
    )

    analysis = profile_cosif_population(downloads, profiles)

    control = _control(analysis, "top_population_reference_reconciliation")
    assert control.passed is False
    assert analysis.passed is False


def test_population_evidence_writer_publishes_all_outputs(tmp_path: Path) -> None:
    downloads, profiles = _official_evidence(tmp_path)
    analysis = profile_cosif_population(downloads, profiles)

    counts = write_population_analysis(analysis, tmp_path / "evidence")

    assert counts == {
        "period_profile": 2,
        "population": 15,
        "monthly_balances": 30,
        "controls": 11,
    }
    assert (tmp_path / "evidence" / "checkpoint_0c_controls.csv").is_file()
