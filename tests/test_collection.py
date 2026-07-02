"""test_collection.py

온통청년 여러 페이지 수집과 SQLite 적재 흐름을 테스트합니다.
"""

from __future__ import annotations

from datetime import date, datetime
import importlib.util
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from career_catch.collection import (
    OntongPageFetchError,
    OntongPayloadError,
    collect_ontong_policy_pages,
)
from career_catch.ontong_client import OntongFetchResult, OntongHttpError
from career_catch.sqlite_store import (
    connect_database,
    count_policies,
    initialize_database,
)


VERIFIED_AT = datetime(2026, 7, 1, 0, 0, 0)
REFERENCE_DATE = date(2026, 7, 1)


def load_collect_script():
    script_path = (
        Path(__file__).resolve().parents[1] / "scripts" / "collect_ontong_pages.py"
    )
    spec = importlib.util.spec_from_file_location(
        "collect_ontong_pages_script",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_policy_item(policy_id: str, **overrides: object) -> dict[str, object]:
    item: dict[str, object] = {
        "plcyNo": policy_id,
        "plcyNm": f"Policy {policy_id}",
        "plcyExplnCn": "Collected policy summary",
        "zipCd": "11680",
        "sprtTrgtMinAge": "19",
        "sprtTrgtMaxAge": "39",
        "jobCd": "0013010",
        "schoolCd": "0049010",
        "earnCndSeCd": "0043001",
        "earnMinAmt": "0",
        "earnMaxAmt": "0",
        "aplyPrdSeCd": "0057002",
        "aplyYmd": "",
        "sbizCd": "0014010",
    }
    item.update(overrides)
    return item


def make_payload(
    *,
    page_num: int,
    page_size: int = 10,
    total_count: int = 20,
    items: list[dict[str, object]] | object | None = None,
) -> dict[str, object]:
    if items is None:
        items = [make_policy_item(f"policy-{page_num}-{index}") for index in range(10)]

    return {
        "resultCode": 200,
        "resultMessage": "ok",
        "result": {
            "pagging": {
                "totCount": total_count,
                "pageNum": page_num,
                "pageSize": page_size,
            },
            "youthPolicyList": items,
        },
    }


class FakePageFetcher:
    def __init__(
        self,
        payloads: dict[int, dict[str, object]],
        *,
        fail_on_page: int | None = None,
    ) -> None:
        self.payloads = payloads
        self.fail_on_page = fail_on_page
        self.calls: list[int] = []
        self.raw_paths: list[Path] = []

    def __call__(
        self,
        *,
        api_key: str,
        output_dir: Path,
        page_num: int,
        page_size: int,
        timeout: float,
    ) -> OntongFetchResult:
        self.calls.append(page_num)
        if self.fail_on_page == page_num:
            raise OntongHttpError("HTTP status 500")

        output_dir.mkdir(parents=True, exist_ok=True)
        raw_path = output_dir / f"page_{page_num}.json"
        raw_path.write_text(
            json.dumps(self.payloads[page_num], ensure_ascii=False),
            encoding="utf-8",
        )
        metadata_path = output_dir / f"page_{page_num}.metadata.json"
        metadata_path.write_text("{}", encoding="utf-8")
        self.raw_paths.append(raw_path)
        return OntongFetchResult(
            raw_path=raw_path,
            metadata_path=metadata_path,
            response_format="json",
            response_size_bytes=raw_path.stat().st_size,
            collected_at="2026-07-01T00:00:00+00:00",
            content_type="application/json",
        )


def collect_with_fetcher(tmp_path: Path, fetcher: FakePageFetcher, **kwargs: object):
    return collect_ontong_policy_pages(
        api_key="test-key",
        db_path=tmp_path / "policies.sqlite3",
        output_dir=tmp_path / "raw",
        fetch_page=fetcher,
        verified_at=VERIFIED_AT,
        reference_date=REFERENCE_DATE,
        **kwargs,
    )


def test_collects_two_pages_sequentially_and_stores_policies(tmp_path: Path):
    fetcher = FakePageFetcher(
        {
            1: make_payload(page_num=1, total_count=20),
            2: make_payload(page_num=2, total_count=20),
        }
    )

    result = collect_with_fetcher(tmp_path, fetcher, max_pages=2)

    assert fetcher.calls == [1, 2]
    assert result.fetched_pages == (1, 2)
    assert result.page_policy_counts == ((1, 10), (2, 10))
    assert result.fetched_policies == 20
    assert result.stored_policies == 20
    assert result.total_available == 20


def test_stops_at_last_page_from_total_count_and_page_size(tmp_path: Path):
    fetcher = FakePageFetcher(
        {
            1: make_payload(page_num=1, total_count=11),
            2: make_payload(
                page_num=2,
                total_count=11,
                items=[make_policy_item("last-page-policy")],
            ),
        }
    )

    result = collect_with_fetcher(tmp_path, fetcher, max_pages=10)

    assert fetcher.calls == [1, 2]
    assert result.fetched_policies == 11
    assert result.stored_policies == 11


def test_stops_when_max_pages_is_reached(tmp_path: Path):
    fetcher = FakePageFetcher(
        {
            1: make_payload(page_num=1, total_count=100),
            2: make_payload(page_num=2, total_count=100),
            3: make_payload(page_num=3, total_count=100),
        }
    )

    result = collect_with_fetcher(tmp_path, fetcher, max_pages=2)

    assert fetcher.calls == [1, 2]
    assert result.fetched_pages == (1, 2)


def test_stops_when_youth_policy_list_is_empty(tmp_path: Path):
    fetcher = FakePageFetcher(
        {
            1: make_payload(page_num=1, total_count=100, items=[]),
            2: make_payload(page_num=2, total_count=100),
        }
    )

    result = collect_with_fetcher(tmp_path, fetcher, max_pages=10)

    assert fetcher.calls == [1]
    assert result.fetched_policies == 0
    assert result.stored_policies == 0


def test_response_page_num_mismatch_raises_clear_error(tmp_path: Path):
    fetcher = FakePageFetcher({1: make_payload(page_num=2, total_count=20)})

    with pytest.raises(OntongPayloadError, match="Requested pageNum 1"):
        collect_with_fetcher(tmp_path, fetcher)


def test_missing_pagging_raises_clear_error(tmp_path: Path):
    payload = make_payload(page_num=1)
    del payload["result"]["pagging"]
    fetcher = FakePageFetcher({1: payload})

    with pytest.raises(OntongPayloadError, match="pagging"):
        collect_with_fetcher(tmp_path, fetcher)


def test_invalid_pagging_value_type_raises_clear_error(tmp_path: Path):
    payload = make_payload(page_num=1)
    payload["result"]["pagging"]["totCount"] = "20"
    fetcher = FakePageFetcher({1: payload})

    with pytest.raises(OntongPayloadError, match="totCount"):
        collect_with_fetcher(tmp_path, fetcher)


def test_invalid_policy_list_type_raises_clear_error(tmp_path: Path):
    fetcher = FakePageFetcher(
        {1: make_payload(page_num=1, total_count=20, items={"not": "a list"})}
    )

    with pytest.raises(OntongPayloadError, match="youthPolicyList"):
        collect_with_fetcher(tmp_path, fetcher)


def test_middle_page_api_error_is_wrapped_with_page_number(tmp_path: Path):
    fetcher = FakePageFetcher(
        {
            1: make_payload(page_num=1, total_count=30),
            2: make_payload(page_num=2, total_count=30),
        },
        fail_on_page=2,
    )

    with pytest.raises(OntongPageFetchError, match="pageNum 2"):
        collect_with_fetcher(tmp_path, fetcher, max_pages=3)


def test_duplicate_policy_id_does_not_increase_sqlite_rows(tmp_path: Path):
    fetcher = FakePageFetcher(
        {
            1: make_payload(
                page_num=1,
                page_size=1,
                total_count=2,
                items=[make_policy_item("duplicate-policy")],
            ),
            2: make_payload(
                page_num=2,
                page_size=1,
                total_count=2,
                items=[make_policy_item("duplicate-policy")],
            ),
        }
    )

    result = collect_with_fetcher(tmp_path, fetcher, max_pages=2, page_size=1)

    assert result.fetched_policies == 2
    assert result.stored_policies == 1

    connection = connect_database(tmp_path / "policies.sqlite3")
    try:
        initialize_database(connection)
        assert count_policies(connection) == 1
    finally:
        connection.close()


def test_raw_save_fetcher_is_called_for_each_page(tmp_path: Path):
    fetcher = FakePageFetcher(
        {
            1: make_payload(page_num=1, total_count=20),
            2: make_payload(page_num=2, total_count=20),
        }
    )

    collect_with_fetcher(tmp_path, fetcher, max_pages=2)

    assert fetcher.calls == [1, 2]
    assert len(fetcher.raw_paths) == 2
    assert all(path.exists() for path in fetcher.raw_paths)


def test_collect_cli_help_does_not_read_secret_or_touch_database(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    script = load_collect_script()
    db_path = tmp_path / "policies.sqlite3"

    def fail_if_called(*args: object, **kwargs: object) -> None:
        pytest.fail("API key loading or collection should not run for --help.")

    monkeypatch.setattr(script, "get_ontong_api_key", fail_if_called)
    monkeypatch.setattr(script, "collect_ontong_policy_pages", fail_if_called)

    with pytest.raises(SystemExit) as exc_info:
        script.main(["--help"])

    assert exc_info.value.code == 0
    assert not db_path.exists()
    output = capsys.readouterr().out
    assert "--db" in output
    assert "--output-dir" in output
    assert "--start-page" in output
    assert "--page-size" in output
    assert "--max-pages" in output
    assert "--timeout" in output
