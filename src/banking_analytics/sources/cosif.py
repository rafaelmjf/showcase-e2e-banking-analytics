"""Download, validate and profile official COSIF bank archives."""

from __future__ import annotations

import csv
import hashlib
import io
import os
import re
import time
import zipfile
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import httpx

from banking_analytics.bcb.cosif import DEFAULT_USER_AGENT, iter_periods

REQUIRED_COLUMNS = {
    "DATA_BASE",
    "DOCUMENTO",
    "CNPJ",
    "NOME_INSTITUICAO",
    "CONTA",
    "NOME_CONTA",
    "SALDO",
}


@dataclass(frozen=True)
class DownloadRecord:
    """Outcome and evidence for one requested source period."""

    period: str
    source_url: str
    status: str
    http_status: int | None
    retrieved_at_utc: str
    sha256: str | None
    compressed_bytes: int | None
    archive_path: str | None
    member_count: int | None
    error: str | None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ProfileRecord:
    """Observed schema and volume metrics for one complete archive."""

    period: str
    source_url: str
    sha256: str
    compressed_bytes: int
    member_name: str
    uncompressed_bytes: int
    encoding: str
    delimiter: str
    header_line_number: int
    metadata_line_count: int
    columns: str
    row_count: int
    malformed_row_count: int
    document_count: int
    institution_count: int
    account_count: int
    declared_period_count: int
    declared_periods: str
    period_matches: bool
    source_generated_at: str | None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def download_catalog_files(
    url_by_period: Mapping[str, str],
    start_period: str,
    end_period: str,
    download_dir: Path,
    *,
    timeout_seconds: float = 120.0,
    max_attempts: int = 3,
    retry_delay_seconds: float = 1.0,
    transport: httpx.BaseTransport | None = None,
) -> list[DownloadRecord]:
    """Download every requested catalog period and retain per-period outcomes."""
    periods = list(iter_periods(start_period, end_period))
    missing = [period for period in periods if period not in url_by_period]
    if missing:
        raise ValueError(f"Catalog has no active URL for periods: {', '.join(missing)}")
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    headers = {"User-Agent": DEFAULT_USER_AGENT, "Accept": "application/zip"}
    with httpx.Client(
        headers=headers,
        follow_redirects=True,
        timeout=timeout_seconds,
        transport=transport,
    ) as client:
        return [
            _download_with_retries(
                client,
                period,
                url_by_period[period],
                download_dir,
                max_attempts=max_attempts,
                retry_delay_seconds=retry_delay_seconds,
            )
            for period in periods
        ]


def _download_with_retries(
    client: httpx.Client,
    period: str,
    source_url: str,
    download_dir: Path,
    *,
    max_attempts: int,
    retry_delay_seconds: float,
) -> DownloadRecord:
    retrieved_at_utc = datetime.now(UTC).replace(microsecond=0).isoformat()
    last_status: int | None = None
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return _download_one(
                client,
                period,
                source_url,
                download_dir,
                retrieved_at_utc=retrieved_at_utc,
            )
        except (httpx.HTTPError, OSError, ValueError, zipfile.BadZipFile) as exc:
            last_error = exc
            if isinstance(exc, httpx.HTTPStatusError):
                last_status = exc.response.status_code
                if last_status < 500 and last_status != httpx.codes.TOO_MANY_REQUESTS:
                    break
            if attempt < max_attempts and retry_delay_seconds:
                time.sleep(retry_delay_seconds * attempt)

    return DownloadRecord(
        period=period,
        source_url=source_url,
        status="error",
        http_status=last_status,
        retrieved_at_utc=retrieved_at_utc,
        sha256=None,
        compressed_bytes=None,
        archive_path=None,
        member_count=None,
        error=f"{type(last_error).__name__}: {last_error}",
    )


def _download_one(
    client: httpx.Client,
    period: str,
    source_url: str,
    download_dir: Path,
    *,
    retrieved_at_utc: str,
) -> DownloadRecord:
    period_dir = download_dir.resolve() / period
    period_dir.mkdir(parents=True, exist_ok=True)
    part_path = period_dir / f"{period}.part"
    digest = hashlib.sha256()
    compressed_bytes = 0
    response_status: int | None = None
    try:
        with client.stream("GET", source_url) as response:
            response_status = response.status_code
            response.raise_for_status()
            with part_path.open("wb") as handle:
                for chunk in response.iter_bytes():
                    digest.update(chunk)
                    compressed_bytes += len(chunk)
                    handle.write(chunk)

        checksum = digest.hexdigest()
        with zipfile.ZipFile(part_path) as archive:
            member_count = len(archive.infolist())
            if member_count < 1:
                raise ValueError("Archive contains no members")
            bad_member = archive.testzip()
            if bad_member:
                raise ValueError(f"Archive CRC failed for member {bad_member}")
            if not any(info.filename.lower().endswith(".csv") for info in archive.infolist()):
                raise ValueError("Archive contains no CSV member")

        final_path = period_dir / f"{checksum}.zip"
        os.replace(part_path, final_path)
        return DownloadRecord(
            period=period,
            source_url=source_url,
            status="complete",
            http_status=response_status,
            retrieved_at_utc=retrieved_at_utc,
            sha256=checksum,
            compressed_bytes=compressed_bytes,
            archive_path=str(final_path),
            member_count=member_count,
            error=None,
        )
    finally:
        part_path.unlink(missing_ok=True)


def write_download_manifest(records: Iterable[DownloadRecord], output_path: Path) -> int:
    """Write download evidence for one bounded acquisition run."""
    materialized = list(records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(DownloadRecord.__dataclass_fields__))
        writer.writeheader()
        writer.writerows(record.as_dict() for record in materialized)
    return len(materialized)


def read_complete_downloads(manifest_path: Path) -> list[DownloadRecord]:
    """Read complete records from a download manifest."""
    with manifest_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    records: list[DownloadRecord] = []
    for row in rows:
        if row["status"] != "complete":
            continue
        records.append(
            DownloadRecord(
                period=row["period"],
                source_url=row["source_url"],
                status=row["status"],
                http_status=int(row["http_status"]) if row["http_status"] else None,
                retrieved_at_utc=row["retrieved_at_utc"],
                sha256=row["sha256"] or None,
                compressed_bytes=(
                    int(row["compressed_bytes"]) if row["compressed_bytes"] else None
                ),
                archive_path=row["archive_path"] or None,
                member_count=int(row["member_count"]) if row["member_count"] else None,
                error=row["error"] or None,
            )
        )
    return records


def profile_downloads(records: Iterable[DownloadRecord]) -> list[ProfileRecord]:
    """Profile each complete archive in manifest order."""
    return [_profile_archive(record) for record in records]


def _profile_archive(record: DownloadRecord) -> ProfileRecord:
    if not record.archive_path or not record.sha256 or record.compressed_bytes is None:
        raise ValueError(f"Incomplete download record for period {record.period}")
    archive_path = Path(record.archive_path)
    if not archive_path.is_file():
        raise FileNotFoundError(archive_path)
    actual_checksum = _sha256_file(archive_path)
    if actual_checksum != record.sha256:
        raise ValueError(f"Checksum mismatch for period {record.period}")

    with zipfile.ZipFile(archive_path) as archive:
        csv_members = [
            info for info in archive.infolist() if info.filename.lower().endswith(".csv")
        ]
        if len(csv_members) != 1:
            raise ValueError(
                f"Expected exactly one CSV member for {record.period}; found {len(csv_members)}"
            )
        member = csv_members[0]
        with archive.open(member) as binary_handle:
            sample = binary_handle.read(65536)
        encoding = _detect_encoding(sample)
        with archive.open(member) as binary_handle:
            text_handle = io.TextIOWrapper(binary_handle, encoding=encoding, newline="")
            return _profile_csv_stream(record, member, text_handle)


def _profile_csv_stream(
    record: DownloadRecord,
    member: zipfile.ZipInfo,
    text_handle: io.TextIOWrapper,
) -> ProfileRecord:
    metadata_lines: list[str] = []
    header: list[str] | None = None
    header_line_number = 0
    reader = iter(text_handle)
    for line_number, line in enumerate(reader, start=1):
        candidate = line.strip().removeprefix("#")
        columns = [column.strip() for column in candidate.split(";")]
        if REQUIRED_COLUMNS.issubset(set(columns)):
            header = columns
            header_line_number = line_number
            break
        metadata_lines.append(line.rstrip("\r\n"))
    if header is None:
        raise ValueError(f"Required COSIF header not found for period {record.period}")

    indexes = {column: index for index, column in enumerate(header)}
    documents: set[str] = set()
    institutions: set[str] = set()
    accounts: set[str] = set()
    declared_periods: set[str] = set()
    row_count = 0
    malformed_row_count = 0
    csv_reader = csv.reader(reader, delimiter=";")
    for row in csv_reader:
        if not row or not any(cell.strip() for cell in row):
            continue
        row_count += 1
        if len(row) != len(header):
            malformed_row_count += 1
            continue
        documents.add(row[indexes["DOCUMENTO"]].strip())
        institutions.add(row[indexes["CNPJ"]].strip())
        accounts.add(row[indexes["CONTA"]].strip())
        declared_periods.add(row[indexes["DATA_BASE"]].strip())

    generated_at = _extract_generated_at(metadata_lines)
    return ProfileRecord(
        period=record.period,
        source_url=record.source_url,
        sha256=record.sha256 or "",
        compressed_bytes=record.compressed_bytes or 0,
        member_name=member.filename,
        uncompressed_bytes=member.file_size,
        encoding=text_handle.encoding,
        delimiter=";",
        header_line_number=header_line_number,
        metadata_line_count=len(metadata_lines),
        columns="|".join(header),
        row_count=row_count,
        malformed_row_count=malformed_row_count,
        document_count=len(documents),
        institution_count=len(institutions - {""}),
        account_count=len(accounts - {""}),
        declared_period_count=len(declared_periods - {""}),
        declared_periods="|".join(sorted(declared_periods - {""})),
        period_matches=declared_periods == {record.period},
        source_generated_at=generated_at,
    )


def _detect_encoding(sample: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252", "iso-8859-1"):
        try:
            sample.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    raise ValueError("Unable to detect source encoding")


def _extract_generated_at(metadata_lines: list[str]) -> str | None:
    text = " ".join(metadata_lines)
    match = re.search(r"\b(\d{2}/\d{2}/\d{4})\b", text)
    if match:
        return datetime.strptime(match.group(1), "%d/%m/%Y").date().isoformat()
    match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
    return match.group(1) if match else None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_source_profile(records: Iterable[ProfileRecord], output_path: Path) -> int:
    """Write per-file schema and volume observations."""
    materialized = list(records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ProfileRecord.__dataclass_fields__))
        writer.writeheader()
        writer.writerows(record.as_dict() for record in materialized)
    return len(materialized)
