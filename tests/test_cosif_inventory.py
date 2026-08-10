from pathlib import Path

import httpx
import pytest

from banking_analytics.bcb.cosif import (
    build_bank_url,
    build_source_inventory,
    iter_periods,
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
