"""test_matching.py

정책 1차 조건 판정 규칙을 테스트합니다.
"""

from datetime import date, datetime
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from career_catch.matching import MatchStatus, UserProfile, evaluate_policy
from career_catch.models import ApplicationStatus, PolicyRecord


APPLICATION_START = date(2026, 6, 1)
APPLICATION_END = date(2026, 6, 30)
VERIFIED_AT = datetime(2026, 6, 29, 0, 0, 0)


def make_policy(
    *,
    policy_id: str = "policy-1",
    age_min: int | None = 19,
    age_max: int | None = 39,
    application_status: ApplicationStatus = ApplicationStatus.OPEN,
) -> PolicyRecord:
    return PolicyRecord(
        policy_id=policy_id,
        policy_name="Test Policy",
        category=None,
        summary=None,
        region_code=None,
        region_name=None,
        age_min=age_min,
        age_max=age_max,
        income_condition=None,
        employment_status=None,
        education_status=None,
        application_start=APPLICATION_START,
        application_end=APPLICATION_END,
        application_status=application_status,
        eligibility_text=None,
        benefit_text=None,
        application_method=None,
        required_documents=None,
        contact=None,
        source_name="Test Source",
        source_url=None,
        last_verified_at=VERIFIED_AT,
        embedding_text="Test Policy",
    )


def test_open_policy_with_age_in_range_matches_with_no_reasons():
    result = evaluate_policy(make_policy(policy_id="policy-match"), UserProfile(age=25))

    assert result.policy_id == "policy-match"
    assert result.status is MatchStatus.MATCH
    assert result.reasons == ()


def test_closed_policy_immediately_returns_no_match_regardless_of_age():
    result = evaluate_policy(
        make_policy(application_status=ApplicationStatus.CLOSED),
        UserProfile(age=25),
    )

    assert result.status is MatchStatus.NO_MATCH
    assert result.reasons == ("신청이 마감된 정책입니다.",)


@pytest.mark.parametrize(
    ("application_status", "expected_reason"),
    [
        (
            ApplicationStatus.UPCOMING,
            "아직 신청 기간이 시작되지 않았습니다.",
        ),
        (
            ApplicationStatus.UNKNOWN,
            "신청 가능 상태를 확인할 수 없습니다.",
        ),
    ],
)
def test_non_open_application_status_is_unknown_when_age_matches(
    application_status,
    expected_reason,
):
    result = evaluate_policy(
        make_policy(application_status=application_status),
        UserProfile(age=25),
    )

    assert result.status is MatchStatus.UNKNOWN
    assert result.reasons == (expected_reason,)


@pytest.mark.parametrize(
    ("policy", "profile", "expected_reason"),
    [
        (
            make_policy(),
            UserProfile(age=None),
            "사용자 나이가 입력되지 않았습니다.",
        ),
        (
            make_policy(age_min=None, age_max=None),
            UserProfile(age=25),
            "정책의 연령 조건을 확인할 수 없습니다.",
        ),
    ],
)
def test_unknown_age_conditions(policy, profile, expected_reason):
    result = evaluate_policy(policy, profile)

    assert result.status is MatchStatus.UNKNOWN
    assert result.reasons == (expected_reason,)


@pytest.mark.parametrize("age", [18, 40])
def test_age_outside_two_sided_range_is_no_match(age):
    result = evaluate_policy(make_policy(age_min=19, age_max=39), UserProfile(age=age))

    assert result.status is MatchStatus.NO_MATCH
    assert result.reasons == ("지원 연령 19~39세에 해당하지 않습니다.",)


def test_age_below_minimum_only_policy_is_no_match_with_exact_reason():
    result = evaluate_policy(
        make_policy(age_min=19, age_max=None),
        UserProfile(age=18),
    )

    assert result.status is MatchStatus.NO_MATCH
    assert result.reasons == ("지원 연령 19세 이상에 해당하지 않습니다.",)


def test_age_above_maximum_only_policy_is_no_match_with_exact_reason():
    result = evaluate_policy(
        make_policy(age_min=None, age_max=39),
        UserProfile(age=40),
    )

    assert result.status is MatchStatus.NO_MATCH
    assert result.reasons == ("지원 연령 39세 이하에 해당하지 않습니다.",)


def test_upcoming_policy_with_age_mismatch_returns_no_match_and_ordered_reasons():
    result = evaluate_policy(
        make_policy(
            age_min=19,
            age_max=39,
            application_status=ApplicationStatus.UPCOMING,
        ),
        UserProfile(age=18),
    )

    assert result.status is MatchStatus.NO_MATCH
    assert result.reasons == (
        "아직 신청 기간이 시작되지 않았습니다.",
        "지원 연령 19~39세에 해당하지 않습니다.",
    )
