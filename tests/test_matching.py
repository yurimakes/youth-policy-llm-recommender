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
    region_code: str | None = "29140",
    age_min: int | None = 19,
    age_max: int | None = 39,
    application_status: ApplicationStatus = ApplicationStatus.OPEN,
) -> PolicyRecord:
    return PolicyRecord(
        policy_id=policy_id,
        policy_name="Test Policy",
        category=None,
        summary=None,
        region_code=region_code,
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
    result = evaluate_policy(
        make_policy(policy_id="policy-match"),
        UserProfile(age=25, region_code="29140"),
    )

    assert result.policy_id == "policy-match"
    assert result.status is MatchStatus.MATCH
    assert result.reasons == ()


def test_closed_policy_immediately_returns_no_match_regardless_of_age():
    result = evaluate_policy(
        make_policy(application_status=ApplicationStatus.CLOSED),
        UserProfile(age=25, region_code="99999"),
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
        UserProfile(age=25, region_code="29140"),
    )

    assert result.status is MatchStatus.UNKNOWN
    assert result.reasons == (expected_reason,)


@pytest.mark.parametrize(
    ("policy", "profile", "expected_reason"),
    [
        (
            make_policy(),
            UserProfile(age=None, region_code="29140"),
            "사용자 나이가 입력되지 않았습니다.",
        ),
        (
            make_policy(age_min=None, age_max=None),
            UserProfile(age=25, region_code="29140"),
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
    result = evaluate_policy(
        make_policy(age_min=19, age_max=39),
        UserProfile(age=age, region_code="29140"),
    )

    assert result.status is MatchStatus.NO_MATCH
    assert result.reasons == ("지원 연령 19~39세에 해당하지 않습니다.",)


def test_age_below_minimum_only_policy_is_no_match_with_exact_reason():
    result = evaluate_policy(
        make_policy(age_min=19, age_max=None),
        UserProfile(age=18, region_code="29140"),
    )

    assert result.status is MatchStatus.NO_MATCH
    assert result.reasons == ("지원 연령 19세 이상에 해당하지 않습니다.",)


def test_age_above_maximum_only_policy_is_no_match_with_exact_reason():
    result = evaluate_policy(
        make_policy(age_min=None, age_max=39),
        UserProfile(age=40, region_code="29140"),
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
        UserProfile(age=18, region_code="29140"),
    )

    assert result.status is MatchStatus.NO_MATCH
    assert result.reasons == (
        "아직 신청 기간이 시작되지 않았습니다.",
        "지원 연령 19~39세에 해당하지 않습니다.",
    )


@pytest.mark.parametrize("region_code", [None, "   "])
def test_missing_user_region_is_unknown(region_code):
    result = evaluate_policy(
        make_policy(),
        UserProfile(age=25, region_code=region_code),
    )

    assert result.status is MatchStatus.UNKNOWN
    assert result.reasons == ("사용자 지역이 입력되지 않았습니다.",)


@pytest.mark.parametrize("region_code", [None, "   "])
def test_missing_policy_region_is_unknown(region_code):
    result = evaluate_policy(
        make_policy(region_code=region_code),
        UserProfile(age=25, region_code="29140"),
    )

    assert result.status is MatchStatus.UNKNOWN
    assert result.reasons == ("정책의 지역 조건을 확인할 수 없습니다.",)


@pytest.mark.parametrize(
    "policy_region_code",
    [
        "29140",
        "29110,29140,29155,29170,29200",
        "29110, 29140, 29155",
    ],
)
def test_user_region_matches_single_or_multiple_policy_regions(policy_region_code):
    result = evaluate_policy(
        make_policy(region_code=policy_region_code),
        UserProfile(age=25, region_code="29140"),
    )

    assert result.status is MatchStatus.MATCH
    assert result.reasons == ()


def test_region_mismatch_is_no_match_with_exact_reason():
    result = evaluate_policy(
        make_policy(region_code="29110,29155"),
        UserProfile(age=25, region_code="29140"),
    )

    assert result.status is MatchStatus.NO_MATCH
    assert result.reasons == ("지원 지역에 해당하지 않습니다.",)


def test_many_policy_region_codes_match_when_user_code_is_included():
    nationwide_like_codes = ",".join(str(code) for code in range(29000, 29255))
    result = evaluate_policy(
        make_policy(region_code=nationwide_like_codes),
        UserProfile(age=25, region_code="29140"),
    )

    assert result.status is MatchStatus.MATCH
    assert result.reasons == ()


def test_upcoming_policy_with_region_mismatch_returns_no_match_and_ordered_reasons():
    result = evaluate_policy(
        make_policy(
            application_status=ApplicationStatus.UPCOMING,
            region_code="29110",
        ),
        UserProfile(age=25, region_code="29140"),
    )

    assert result.status is MatchStatus.NO_MATCH
    assert result.reasons == (
        "아직 신청 기간이 시작되지 않았습니다.",
        "지원 지역에 해당하지 않습니다.",
    )


def test_age_and_region_mismatch_reasons_are_ordered_after_status():
    result = evaluate_policy(
        make_policy(age_min=19, age_max=39, region_code="29110"),
        UserProfile(age=18, region_code="29140"),
    )

    assert result.status is MatchStatus.NO_MATCH
    assert result.reasons == (
        "지원 연령 19~39세에 해당하지 않습니다.",
        "지원 지역에 해당하지 않습니다.",
    )


def test_closed_policy_returns_only_closed_reason_regardless_of_region():
    result = evaluate_policy(
        make_policy(
            application_status=ApplicationStatus.CLOSED,
            region_code="29110",
        ),
        UserProfile(age=18, region_code=None),
    )

    assert result.status is MatchStatus.NO_MATCH
    assert result.reasons == ("신청이 마감된 정책입니다.",)
