"""ontong_client.py

온통청년 청년정책 API를 호출하고 원본 응답을 보존합니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Protocol

import requests


ONTONG_POLICY_ENDPOINT = "https://www.youthcenter.go.kr/go/ythip/getPlcy"
DEFAULT_OUTPUT_DIR = Path("data") / "raw" / "ontong"
DEFAULT_PAGE_NUM = 1
DEFAULT_PAGE_SIZE = 10
DEFAULT_PAGE_TYPE = 1
DEFAULT_RTN_TYPE = "json"
DEFAULT_TIMEOUT_SECONDS = 10.0


class OntongClientError(RuntimeError):
    """온통청년 API 호출 또는 저장 과정에서 발생하는 기본 오류입니다."""


class OntongNetworkError(OntongClientError):
    """네트워크 오류가 발생했을 때 사용합니다."""


class OntongHttpError(OntongClientError):
    """HTTP 오류 응답을 받았을 때 사용합니다."""


class OntongEmptyResponseError(OntongClientError):
    """응답 본문이 비어 있을 때 사용합니다."""


class _Requester(Protocol):
    def get(
        self,
        url: str,
        *,
        params: dict[str, object],
        timeout: float,
    ) -> Any:
        ...


@dataclass(frozen=True)
class OntongFetchResult:
    raw_path: Path
    metadata_path: Path
    response_format: str
    response_size_bytes: int
    collected_at: str
    content_type: str | None


def fetch_ontong_policies(
    *,
    api_key: str,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    page_num: int = DEFAULT_PAGE_NUM,
    page_size: int = DEFAULT_PAGE_SIZE,
    page_type: int = DEFAULT_PAGE_TYPE,
    rtn_type: str = DEFAULT_RTN_TYPE,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    requester: _Requester = requests,
) -> OntongFetchResult:
    if not api_key.strip():
        raise OntongClientError("ONTONG_API_KEY is required.")

    params: dict[str, object] = {
        "apiKeyNm": api_key,
        "pageNum": page_num,
        "pageSize": page_size,
        "pageType": page_type,
        "rtnType": rtn_type,
    }
    response = _request_policy_page(
        requester=requester,
        params=params,
        timeout=timeout,
    )
    content = bytes(response.content)
    if not content.strip():
        raise OntongEmptyResponseError("Ontong API returned an empty response body.")

    collected_at = datetime.now(timezone.utc).isoformat()
    content_type = response.headers.get("Content-Type")
    response_format = _detect_response_format(content_type, content)
    extension = response_format
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = _timestamp_for_filename(collected_at)
    raw_path = _unique_path(
        output_dir / f"ontong_youth_policy_{timestamp}.{extension}"
    )
    raw_path.write_bytes(content)

    metadata_path = _unique_path(
        output_dir / f"{raw_path.stem}.metadata.json"
    )
    metadata = {
        "endpoint": ONTONG_POLICY_ENDPOINT,
        "pageNum": page_num,
        "pageSize": page_size,
        "pageType": page_type,
        "rtnType": rtn_type,
        "collected_at": collected_at,
        "response_format": response_format,
        "content_type": content_type,
        "response_size_bytes": len(content),
        "raw_file": raw_path.name,
    }
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    return OntongFetchResult(
        raw_path=raw_path,
        metadata_path=metadata_path,
        response_format=response_format,
        response_size_bytes=len(content),
        collected_at=collected_at,
        content_type=content_type,
    )


def _request_policy_page(
    *,
    requester: _Requester,
    params: dict[str, object],
    timeout: float,
) -> Any:
    try:
        response = requester.get(
            ONTONG_POLICY_ENDPOINT,
            params=params,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise OntongNetworkError("Could not connect to Ontong youth policy API.") from exc

    status_code = getattr(response, "status_code", None)
    if isinstance(status_code, int) and status_code >= 400:
        raise OntongHttpError(
            f"Ontong youth policy API returned HTTP status {status_code}."
        )

    return response


def _detect_response_format(content_type: str | None, content: bytes) -> str:
    normalized_content_type = (content_type or "").lower()
    stripped = content.lstrip()

    if "json" in normalized_content_type or stripped.startswith((b"{", b"[")):
        return "json"
    if "xml" in normalized_content_type or stripped.startswith(b"<"):
        return "xml"
    return "txt"


def _timestamp_for_filename(iso_timestamp: str) -> str:
    return (
        iso_timestamp.replace(":", "")
        .replace("-", "")
        .replace("+", "Z")
        .replace(".", "")
    )


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path

    for index in range(1, 1000):
        candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
        if not candidate.exists():
            return candidate

    raise OntongClientError("Could not create a unique output file path.")
