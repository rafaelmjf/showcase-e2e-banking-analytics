from pathlib import Path

import httpx
import pytest

from banking_analytics.bcb.cosif import (
    build_bank_url,
    build_source_catalog,
    build_source_inventory,
    iter_periods,
    parse_bank_catalog,
    read_active_catalog_urls,
    write_source_catalog,
    write_source_inventory,
)


def test_iter_periods_is_inclusive_and_crosses_year() -> None:
    assert list(iter_periods("202411", "202502")) == [
        "202411",
        "202412",
        "202501",
        "202502",
    ]


@pytest.mark.parametrize("period", ["2025", "202500", "202513", "ABCDEF"])
def test_invalid_period_is_rejected(period: str) -> None:
    with pytest.raises(ValueError, match="Invalid reporting period"):
        build_bank_url(period)


def test_start_after_end_is_rejected() -> None:
    with pytest.raises(ValueError, match="start_period"):
        list(iter_periods("202502", "202501"))


def test_build_bank_url_uses_official_pattern() -> None:
    assert build_bank_url("202601").endswith("/Bancos/202601BANCOS.csv.zip")


def test_inventory_captures_available_and_missing_periods() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "202501" in str(request.url):
            return httpx.Response(
                200,
                headers={
                    "content-length": "1234",
                    "content-type": "application/x-zip-compressed",
                    "etag": '"example"',
                },
            )
        return httpx.Response(404, headers={"content-length": "99"})

    records = build_source_inventory(
        "202501",
        "202502",
        transport=httpx.MockTransport(handler),
    )

    assert records[0].available is True
    assert records[0].probe_method == "HEAD"
    assert records[0].content_length_bytes == 1234
    assert records[0].etag == '"example"'
    assert records[1].available is False
    assert records[1].status_code == 404


def test_inventory_falls_back_to_streamed_get_and_reads_total_size() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "HEAD":
            return httpx.Response(502)
        assert request.headers["range"] == "bytes=0-0"
        return httpx.Response(
            206,
            headers={
                "content-range": "bytes 0-0/902381",
                "content-length": "1",
                "content-type": "application/x-zip-compressed",
            },
        )

    record = build_source_inventory(
        "202601",
        "202601",
        transport=httpx.MockTransport(handler),
    )[0]

    assert record.available is True
    assert record.probe_method == "GET_RANGE"
    assert record.status_code == 206
    assert record.content_length_bytes == 902381
    assert record.error is None


def test_server_error_is_unknown_not_missing() -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(502))
    record = build_source_inventory("202601", "202601", transport=transport)[0]

    assert record.available is None
    assert record.status_code == 502
    assert record.error == "HTTP 502"


def test_write_source_inventory_creates_stable_csv(tmp_path: Path) -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(200))
    records = build_source_inventory("202501", "202501", transport=transport)
    output = tmp_path / "nested" / "inventory.csv"

    assert write_source_inventory(records, output) == 1
    content = output.read_text(encoding="utf-8")
    assert content.startswith("period,url,probe_method,available,status_code")
    assert "202501" in content


def test_parse_bank_catalog_preserves_files_and_anomalies() -> None:
    payload = {
        "conteudo": [
            {
                "Titulo": "Balancete Bancos 03/2026",
                "DataDocumento": "2026-05-31T00:00:00",
                "Url": "/content/estabilidadefinanceira/cosif/Bancos/202603BANCOS.csv.zip",
            },
            {"Titulo": "Unexpected document", "Url": "/not-a-bank-file.pdf"},
            "unexpected",
        ]
    }

    records = parse_bank_catalog(payload, discovered_at_utc="2026-08-11T00:00:00+00:00")

    assert records[0].period == "202603"
    assert records[0].period_version == 1
    assert records[0].is_active is True
    assert records[0].source_url == (
        "https://www.bcb.gov.br/content/estabilidadefinanceira/cosif/Bancos/"
        "202603BANCOS.csv.zip"
    )
    assert records[0].error is None
    assert records[1].period is None
    assert records[1].error == "Unrecognized or missing bank file URL"
    assert records[2].error == "Catalog item is not an object"


def test_build_source_catalog_uses_official_catalog() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/Documentos/byListGuid")
        assert request.url.params["pasta"] == "/Bancos"
        return httpx.Response(
            200,
            json={
                "conteudo": [
                    {
                        "Url": (
                            "/content/estabilidadefinanceira/cosif/Bancos/"
                            "202603BANCOS.csv.zip"
                        )
                    }
                ]
            },
        )

    records = build_source_catalog(transport=httpx.MockTransport(handler))

    assert [record.period for record in records] == ["202603"]


@pytest.mark.parametrize(
    ("url", "period"),
    [
        ("/content/cosif/Bancos/202301BANCOS.csv", "202301"),
        ("/content/cosif/Bancos/202212BANCOS.ZIP", "202212"),
        ("/content/cosif/Bancos/202512BANCOS.zip.csv.zip", "202512"),
    ],
)
def test_catalog_accepts_official_historical_filename_variants(
    url: str,
    period: str,
) -> None:
    record = parse_bank_catalog(
        {"conteudo": [{"Url": url}]},
        discovered_at_utc="2026-08-11T00:00:00+00:00",
    )[0]

    assert record.period == period
    assert record.error is None


def test_write_source_catalog_creates_stable_csv(tmp_path: Path) -> None:
    records = parse_bank_catalog(
        {
            "conteudo": [
                {
                    "Url": (
                        "/content/estabilidadefinanceira/cosif/Bancos/"
                        "202603BANCOS.csv.zip"
                    )
                }
            ]
        },
        discovered_at_utc="2026-08-11T00:00:00+00:00",
    )
    output = tmp_path / "catalog.csv"

    assert write_source_catalog(records, output) == 1
    assert output.read_text(encoding="utf-8").startswith(
        "period,period_version,is_active,title,source_url,document_date,"
        "discovered_at_utc,error"
    )


def test_parse_bank_catalog_requires_content_list() -> None:
    with pytest.raises(ValueError, match="conteudo"):
        parse_bank_catalog({}, discovered_at_utc="2026-08-11T00:00:00+00:00")


def test_catalog_selects_latest_duplicate_as_active() -> None:
    records = parse_bank_catalog(
        {
            "conteudo": [
                {
                    "DataDocumento": "2025-12-01T03:00:00Z",
                    "Url": "/content/cosif/Bancos/202512BANCOS.csv.zip",
                },
                {
                    "DataDocumento": "2026-04-01T22:13:22Z",
                    "Url": "/content/cosif/Bancos/202512BANCOS.zip.csv.zip",
                },
            ]
        },
        discovered_at_utc="2026-08-11T00:00:00+00:00",
    )

    assert [(record.period_version, record.is_active) for record in records] == [
        (1, False),
        (2, True),
    ]


def test_inventory_uses_catalog_selected_url() -> None:
    observed_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        observed_urls.append(str(request.url))
        return httpx.Response(200)

    replacement_url = (
        "https://www.bcb.gov.br/content/estabilidadefinanceira/cosif/Bancos/"
        "202512BANCOS.zip.csv.zip"
    )
    build_source_inventory(
        "202512",
        "202512",
        url_by_period={"202512": replacement_url},
        transport=httpx.MockTransport(handler),
    )

    assert observed_urls == [replacement_url]


def test_read_active_catalog_urls(tmp_path: Path) -> None:
    records = parse_bank_catalog(
        {
            "conteudo": [
                {
                    "DataDocumento": "2025-12-01T03:00:00Z",
                    "Url": "/content/cosif/Bancos/202512BANCOS.csv.zip",
                },
                {
                    "DataDocumento": "2026-04-01T22:13:22Z",
                    "Url": "/content/cosif/Bancos/202512BANCOS.zip.csv.zip",
                },
            ]
        },
        discovered_at_utc="2026-08-11T00:00:00+00:00",
    )
    output = tmp_path / "catalog.csv"
    write_source_catalog(records, output)

    active = read_active_catalog_urls(output)

    assert active == {
        "202512": (
            "https://www.bcb.gov.br/content/cosif/Bancos/"
            "202512BANCOS.zip.csv.zip"
        )
    }
