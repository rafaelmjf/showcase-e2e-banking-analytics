import csv
import hashlib
import io
import zipfile
from pathlib import Path

import httpx

from banking_analytics.sources.cosif import (
    download_catalog_files,
    profile_downloads,
    read_complete_downloads,
    write_download_manifest,
    write_source_profile,
)


def _archive_bytes(*, period: str = "202601", malformed: bool = False) -> bytes:
    rows = [
        "#Arquivo de balancetes das instituições",
        "#Gerado em 03/08/2026",
        "#Valores em reais",
        (
            "#DATA_BASE;DOCUMENTO;CNPJ;AGENCIA;NOME_INSTITUICAO;COD_CONGL;"
            "NOME_CONGL;TAXONOMIA;CONTA;NOME_CONTA;SALDO"
        ),
        f"{period};4010;00000000;;BCO DO BRASIL S.A.;;;BANCO;1000000009;Ativo;10,00",
        f"{period};4010;60746948;;BCO BRADESCO S.A.;;;BANCO;1000000009;Ativo;20,00",
        f"{period};4010;60746948;;BCO BRADESCO S.A.;;;BANCO;2100000003;Passivo;5,00",
    ]
    if malformed:
        rows.append(f"{period};4010;too;short")
    content = ("\r\n".join(rows) + "\r\n").encode("cp1252")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(f"{period}BANCOS.csv", content)
    return buffer.getvalue()


def test_download_validates_zip_and_writes_checksum(tmp_path: Path) -> None:
    body = _archive_bytes()
    transport = httpx.MockTransport(lambda _: httpx.Response(200, content=body))
    url = "https://www.bcb.gov.br/content/cosif/Bancos/202601BANCOS.csv.zip"

    records = download_catalog_files(
        {"202601": url},
        "202601",
        "202601",
        tmp_path / "downloads",
        max_attempts=1,
        retry_delay_seconds=0,
        transport=transport,
    )

    record = records[0]
    assert record.status == "complete"
    assert record.sha256 == hashlib.sha256(body).hexdigest()
    assert record.compressed_bytes == len(body)
    assert record.member_count == 1
    assert Path(record.archive_path or "").is_file()


def test_download_retains_error_without_partial_file(tmp_path: Path) -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(200, content=b"not a zip"))

    record = download_catalog_files(
        {"202601": "https://example.test/202601.zip"},
        "202601",
        "202601",
        tmp_path / "downloads",
        max_attempts=1,
        retry_delay_seconds=0,
        transport=transport,
    )[0]

    assert record.status == "error"
    assert "BadZipFile" in (record.error or "")
    assert not list((tmp_path / "downloads").rglob("*.part"))


def test_download_manifest_and_profile_round_trip(tmp_path: Path) -> None:
    body = _archive_bytes()
    transport = httpx.MockTransport(lambda _: httpx.Response(200, content=body))
    records = download_catalog_files(
        {"202601": "https://example.test/202601.zip"},
        "202601",
        "202601",
        tmp_path / "downloads",
        max_attempts=1,
        retry_delay_seconds=0,
        transport=transport,
    )
    manifest = tmp_path / "manifest.csv"
    profile_path = tmp_path / "profile.csv"

    assert write_download_manifest(records, manifest) == 1
    profiles = profile_downloads(read_complete_downloads(manifest))
    assert write_source_profile(profiles, profile_path) == 1

    profile = profiles[0]
    assert profile.row_count == 3
    assert profile.malformed_row_count == 0
    assert profile.document_count == 1
    assert profile.institution_count == 2
    assert profile.account_count == 2
    assert profile.declared_periods == "202601"
    assert profile.period_matches is True
    assert profile.source_generated_at == "2026-08-03"
    assert profile.header_line_number == 4
    assert profile.encoding == "cp1252"

    output_rows = list(csv.DictReader(profile_path.open(encoding="utf-8")))
    assert output_rows[0]["period"] == "202601"


def test_profile_reports_malformed_rows(tmp_path: Path) -> None:
    body = _archive_bytes(malformed=True)
    transport = httpx.MockTransport(lambda _: httpx.Response(200, content=body))
    records = download_catalog_files(
        {"202601": "https://example.test/202601.zip"},
        "202601",
        "202601",
        tmp_path / "downloads",
        max_attempts=1,
        retry_delay_seconds=0,
        transport=transport,
    )

    profile = profile_downloads(records)[0]

    assert profile.row_count == 4
    assert profile.malformed_row_count == 1


def test_profile_rejects_checksum_mismatch(tmp_path: Path) -> None:
    body = _archive_bytes()
    transport = httpx.MockTransport(lambda _: httpx.Response(200, content=body))
    records = download_catalog_files(
        {"202601": "https://example.test/202601.zip"},
        "202601",
        "202601",
        tmp_path / "downloads",
        max_attempts=1,
        retry_delay_seconds=0,
        transport=transport,
    )
    archive_path = Path(records[0].archive_path or "")
    archive_path.write_bytes(b"tampered")

    try:
        profile_downloads(records)
    except ValueError as exc:
        assert "Checksum mismatch" in str(exc)
    else:
        raise AssertionError("Checksum mismatch was not rejected")
