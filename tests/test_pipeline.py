"""test_pipeline.py

저장된 온통청년 snapshot의 SQLite 적재 파이프라인을 테스트합니다.
"""

from __future__ import annotations

from datetime import date, datetime
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from youth_policy.matching import UserProfile, evaluate_policies
from youth_policy.pipeline import (
    SnapshotPipelineError,
    load_ontong_snapshot_to_sqlite,
)
from scripts.load_ontong_snapshot import main as load_snapshot_main


VERIFIED_AT = datetime(2026, 7, 1, 0, 0, 0)
REFERENCE_DATE = date(2026, 7, 1)


def make_policy_item(policy_id: str = "policy-1", **overrides: object) -> dict[str, object]:
    item: dict[str, object] = {
        "plcyNo": policy_id,
        "plcyNm": f"Policy {policy_id}",
        "plcyExplnCn": "Snapshot policy summary",
        "zipCd": "29140",
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


def make_payload(items: list[dict[str, object]] | None = None) -> dict[str, object]:
    if items is None:
        items = [make_policy_item(f"policy-{index}") for index in range(10)]

    return {
        "resultCode": 200,
        "resultMessage": "ok",
        "result": {
            "pagging": {
                "totCount": len(items),
                "pageNum": 1,
                "pageSize": 10,
            },
            "youthPolicyList": items,
        },
    }


def write_snapshot(path: Path, payload: dict[str, object]) -> Path:
    path.write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def load_fixture_snapshot(tmp_path: Path, payload: dict[str, object] | None = None):
    snapshot_path = write_snapshot(
        tmp_path / "snapshot.json",
        payload or make_payload(),
    )
    return load_ontong_snapshot_to_sqlite(
        snapshot_path,
        tmp_path / "policies.sqlite3",
        verified_at=VERIFIED_AT,
        reference_date=REFERENCE_DATE,
    )


def test_load_latest_response_wrapper_to_sqlite(tmp_path: Path):
    result = load_fixture_snapshot(tmp_path)

    assert result.parsed_count == 10
    assert result.stored_count == 10
    assert len(result.stored_policies) == 10


def test_policy_record_round_trip_preserves_core_fields(tmp_path: Path):
    result = load_fixture_snapshot(tmp_path)

    original = result.parsed_policies[0]
    reloaded = result.stored_policies[0]

    assert reloaded.policy_id == original.policy_id
    assert reloaded.policy_name == original.policy_name
    assert reloaded.summary == original.summary
    assert reloaded.region_code == original.region_code
    assert reloaded.age_min == original.age_min
    assert reloaded.age_max == original.age_max
    assert reloaded.employment_status == original.employment_status
    assert reloaded.income_condition == original.income_condition
    assert reloaded.last_verified_at == original.last_verified_at


def test_loading_same_snapshot_twice_does_not_duplicate_rows(tmp_path: Path):
    snapshot_path = write_snapshot(tmp_path / "snapshot.json", make_payload())
    db_path = tmp_path / "policies.sqlite3"

    first = load_ontong_snapshot_to_sqlite(
        snapshot_path,
        db_path,
        verified_at=VERIFIED_AT,
        reference_date=REFERENCE_DATE,
    )
    second = load_ontong_snapshot_to_sqlite(
        snapshot_path,
        db_path,
        verified_at=VERIFIED_AT,
        reference_date=REFERENCE_DATE,
    )

    assert first.parsed_count == 10
    assert second.parsed_count == 10
    assert second.stored_count == 10


def test_reloaded_sqlite_policies_can_be_evaluated(tmp_path: Path):
    result = load_fixture_snapshot(tmp_path)

    batch = evaluate_policies(
        result.stored_policies,
        UserProfile(age=25, region_code="29140", employment_status="미취업자"),
    )
    evaluated_count = len(batch.matched) + len(batch.unknown) + len(batch.no_match)

    assert evaluated_count == result.stored_count


def test_missing_snapshot_raises_clear_error(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="Snapshot file not found"):
        load_ontong_snapshot_to_sqlite(
            tmp_path / "missing.json",
            tmp_path / "policies.sqlite3",
            verified_at=VERIFIED_AT,
            reference_date=REFERENCE_DATE,
        )


def test_invalid_json_raises_clear_error(tmp_path: Path):
    snapshot_path = tmp_path / "invalid.json"
    snapshot_path.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(SnapshotPipelineError, match="valid JSON"):
        load_ontong_snapshot_to_sqlite(
            snapshot_path,
            tmp_path / "policies.sqlite3",
            verified_at=VERIFIED_AT,
            reference_date=REFERENCE_DATE,
        )


def test_empty_policy_list_raises_clear_error(tmp_path: Path):
    snapshot_path = write_snapshot(
        tmp_path / "empty.json",
        make_payload([]),
    )

    with pytest.raises(SnapshotPipelineError, match="no policies"):
        load_ontong_snapshot_to_sqlite(
            snapshot_path,
            tmp_path / "policies.sqlite3",
            verified_at=VERIFIED_AT,
            reference_date=REFERENCE_DATE,
        )


def test_cli_help_does_not_create_database(tmp_path: Path):
    db_path = tmp_path / "policies.sqlite3"

    with pytest.raises(SystemExit) as exc_info:
        load_snapshot_main(["--help"])

    assert exc_info.value.code == 0
    assert not db_path.exists()
