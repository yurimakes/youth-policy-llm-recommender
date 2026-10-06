"""test_ui_service.py

Streamlit UI 서비스의 정책 로딩과 평가 연결을 테스트합니다.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from youth_policy.models import ApplicationStatus, PolicyRecord
from youth_policy.sqlite_store import (
    connect_database,
    initialize_database,
    upsert_policies,
)
from youth_policy.ui_service import (
    PolicyServiceError,
    evaluate_sqlite_policies,
    load_policies_from_sqlite,
)


VERIFIED_AT = datetime(2026, 7, 1, 0, 0, 0)


def make_policy(
    policy_id: str,
    *,
    region_code: str = "11680",
    employment_status: str | None = "미취업자",
    application_status: ApplicationStatus = ApplicationStatus.OPEN,
) -> PolicyRecord:
    return PolicyRecord(
        policy_id=policy_id,
        policy_name=f"Policy {policy_id}",
        category="일자리",
        summary="정책 요약",
        region_code=region_code,
        region_name=None,
        age_min=19,
        age_max=39,
        income_condition="무관",
        employment_status=employment_status,
        education_status=None,
        application_start=date(2026, 1, 1),
        application_end=date(2026, 12, 31),
        application_status=application_status,
        eligibility_text=None,
        benefit_text="지원 내용",
        application_method="온라인",
        required_documents=None,
        contact=None,
        source_name="온통청년",
        source_url="https://example.test/policy",
        last_verified_at=VERIFIED_AT,
        embedding_text="Policy text",
    )


def write_policies(db_path: Path, policies: list[PolicyRecord]) -> None:
    connection = connect_database(db_path)
    try:
        initialize_database(connection)
        upsert_policies(connection, policies)
    finally:
        connection.close()


def test_load_policies_from_sqlite_returns_policy_records(tmp_path: Path):
    db_path = tmp_path / "policies.sqlite3"
    write_policies(db_path, [make_policy("policy-1"), make_policy("policy-2")])

    policies = load_policies_from_sqlite(db_path)

    assert len(policies) == 2
    assert [policy.policy_id for policy in policies] == ["policy-1", "policy-2"]


def test_evaluate_sqlite_policies_uses_existing_matching_engine(tmp_path: Path):
    db_path = tmp_path / "policies.sqlite3"
    write_policies(
        db_path,
        [
            make_policy("match-policy"),
            make_policy("unknown-policy", employment_status=None),
            make_policy("no-match-policy", region_code="29140"),
        ],
    )

    summary = evaluate_sqlite_policies(
        db_path=db_path,
        age=24,
        region_code=" 11680 ",
        employment_status=" 미취업자 ",
    )

    assert summary.total_count == 3
    assert [item.policy.policy_id for item in summary.batch.matched] == [
        "match-policy"
    ]
    assert [item.policy.policy_id for item in summary.batch.unknown] == [
        "unknown-policy"
    ]
    assert [item.policy.policy_id for item in summary.batch.no_match] == [
        "no-match-policy"
    ]


def test_load_policies_from_sqlite_raises_for_missing_database(tmp_path: Path):
    with pytest.raises(PolicyServiceError, match="SQLite database not found"):
        load_policies_from_sqlite(tmp_path / "missing.sqlite3")
