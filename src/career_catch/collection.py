"""collection.py

온통청년 API 페이지 수집과 SQLite 적재 흐름을 조합합니다.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timezone
import json
from json import JSONDecodeError
from math import ceil
from pathlib import Path
from typing import Any

from career_catch.ontong_client import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PAGE_SIZE,
    DEFAULT_TIMEOUT_SECONDS,
    OntongClientError,
    OntongFetchResult,
    fetch_ontong_policies,
)
from career_catch.ontong_parser import parse_policy_page
from career_catch.sqlite_store import (
    connect_database,
    count_policies,
    initialize_database,
    upsert_policies,
)


DEFAULT_START_PAGE = 1
DEFAULT_MAX_PAGES = 2


class OntongCollectionError(RuntimeError):
    """온통청년 여러 페이지 수집 중 발생하는 기본 오류입니다."""


class OntongPageFetchError(OntongCollectionError):
    """특정 페이지 API 호출 또는 저장이 실패했을 때 사용합니다."""


class OntongPayloadError(OntongCollectionError):
    """API 응답 구조가 기대와 다를 때 사용합니다."""


@dataclass(frozen=True)
class PageCollectionSummary:
    page_num: int
    raw_path: Path
    input_policy_count: int


@dataclass(frozen=True)
class OntongCollectionResult:
    db_path: Path
    fetched_pages: tuple[int, ...]
    page_policy_counts: tuple[tuple[int, int], ...]
    fetched_policies: int
    stored_policies: int
    total_available: int
    page_summaries: tuple[PageCollectionSummary, ...]


FetchPage = Callable[..., OntongFetchResult]


def collect_ontong_policy_pages(
    *,
    api_key: str,
    db_path: str | Path,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    start_page: int = DEFAULT_START_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
    max_pages: int = DEFAULT_MAX_PAGES,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    fetch_page: FetchPage = fetch_ontong_policies,
    verified_at: datetime | None = None,
    reference_date: date | None = None,
) -> OntongCollectionResult:
    _validate_positive_int(start_page, "start_page")
    _validate_positive_int(page_size, "page_size")
    _validate_positive_int(max_pages, "max_pages")

    database = Path(db_path)
    database.parent.mkdir(parents=True, exist_ok=True)
    connection = connect_database(database)

    page_summaries: list[PageCollectionSummary] = []
    fetched_policies = 0
    total_available: int | None = None
    seen_pages: set[int] = set()
    next_page = start_page

    effective_verified_at = verified_at or _utc_now_naive()
    effective_reference_date = reference_date or effective_verified_at.date()

    try:
        initialize_database(connection)
        for _ in range(max_pages):
            if next_page in seen_pages:
                raise OntongCollectionError(
                    f"Duplicate pageNum call blocked: {next_page}."
                )
            seen_pages.add(next_page)

            fetch_result = _fetch_page(
                fetch_page=fetch_page,
                api_key=api_key,
                output_dir=Path(output_dir),
                page_num=next_page,
                page_size=page_size,
                timeout=timeout,
            )
            payload = _read_raw_json(fetch_result.raw_path)
            page_payload = _validate_page_payload(
                payload,
                requested_page=next_page,
                requested_page_size=page_size,
            )
            total_available = page_payload.total_count

            records = tuple(
                parse_policy_page(
                    payload,
                    verified_at=effective_verified_at,
                    reference_date=effective_reference_date,
                )
            )
            upsert_policies(connection, records)

            input_count = len(records)
            page_summaries.append(
                PageCollectionSummary(
                    page_num=next_page,
                    raw_path=fetch_result.raw_path,
                    input_policy_count=input_count,
                )
            )
            fetched_policies += input_count

            if input_count == 0 or _is_last_page(page_payload):
                break
            next_page += 1

        stored_policies = count_policies(connection)
    finally:
        connection.close()

    return OntongCollectionResult(
        db_path=database,
        fetched_pages=tuple(summary.page_num for summary in page_summaries),
        page_policy_counts=tuple(
            (summary.page_num, summary.input_policy_count)
            for summary in page_summaries
        ),
        fetched_policies=fetched_policies,
        stored_policies=stored_policies,
        total_available=total_available if total_available is not None else 0,
        page_summaries=tuple(page_summaries),
    )


@dataclass(frozen=True)
class _ValidatedPagePayload:
    total_count: int
    page_num: int
    page_size: int


def _fetch_page(
    *,
    fetch_page: FetchPage,
    api_key: str,
    output_dir: Path,
    page_num: int,
    page_size: int,
    timeout: float,
) -> OntongFetchResult:
    try:
        return fetch_page(
            api_key=api_key,
            output_dir=output_dir,
            page_num=page_num,
            page_size=page_size,
            timeout=timeout,
        )
    except OntongClientError as exc:
        raise OntongPageFetchError(f"Failed to fetch pageNum {page_num}.") from exc


def _read_raw_json(raw_path: Path) -> dict[str, object]:
    try:
        payload = json.loads(raw_path.read_text(encoding="utf-8"))
    except JSONDecodeError as exc:
        raise OntongPayloadError("Saved raw response is not valid JSON.") from exc

    if not isinstance(payload, dict):
        raise OntongPayloadError("Saved raw response root must be an object.")
    return payload


def _validate_page_payload(
    payload: dict[str, object],
    *,
    requested_page: int,
    requested_page_size: int,
) -> _ValidatedPagePayload:
    if payload.get("resultCode") != 200:
        raise OntongPayloadError("Ontong API resultCode must be 200.")

    result = payload.get("result")
    if not isinstance(result, dict):
        raise OntongPayloadError("Ontong API result must be an object.")

    pagging = result.get("pagging")
    if not isinstance(pagging, dict):
        raise OntongPayloadError("Ontong API result.pagging is required.")

    total_count = _require_int(pagging.get("totCount"), "totCount")
    page_num = _require_int(pagging.get("pageNum"), "pageNum")
    page_size = _require_int(pagging.get("pageSize"), "pageSize")

    if page_num != requested_page:
        raise OntongPayloadError(
            f"Requested pageNum {requested_page} but response pageNum was {page_num}."
        )
    if page_size != requested_page_size:
        raise OntongPayloadError(
            f"Requested pageSize {requested_page_size} but response pageSize was {page_size}."
        )

    items = result.get("youthPolicyList")
    if not isinstance(items, list):
        raise OntongPayloadError("Ontong API result.youthPolicyList must be a list.")

    return _ValidatedPagePayload(
        total_count=total_count,
        page_num=page_num,
        page_size=page_size,
    )


def _require_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise OntongPayloadError(f"result.pagging.{field_name} must be an integer.")
    if value < 0:
        raise OntongPayloadError(
            f"result.pagging.{field_name} must be greater than or equal to 0."
        )
    return value


def _is_last_page(page_payload: _ValidatedPagePayload) -> bool:
    if page_payload.total_count == 0:
        return True
    return page_payload.page_num >= ceil(
        page_payload.total_count / page_payload.page_size
    )


def _validate_positive_int(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field_name} must be a positive integer.")


def _utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)
