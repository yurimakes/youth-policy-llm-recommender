"""test_matching.py

정책 1차 조건 판정 규칙을 테스트합니다.
"""

from datetime import date, datetime
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from career_catch.matching import (
    MatchStatus,
    UserProfile,
    evaluate_policies,
    evaluate_policy,
)
from career_catch.models import ApplicationStatus, PolicyRecord
from career_catch.sqlite_store import (
    connect_database,
    initialize_database,
    list_policies,
    upsert_policies,
)


APPLICATION_START = date(2026, 6, 1)
APPLICATION_END = date(2026, 6, 30)
VERIFIED_AT = datetime(2026, 6, 29, 0, 0, 0)


def make_policy(
    *,
    policy_id: str = "policy-1",
    region_code: str | None = "29140",
    employment_status: str | None = "미취업자",
    income_condition: str | None = "무관",
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
        income_condition=income_condition,
        employment_status=employment_status,
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


def make_profile(
    *,
    age: int | None = 25,
    region_code: str | None = "29140",
    employment_status: str | None = "미취업자",
) -> UserProfile:
    return UserProfile(
        age=age,
        region_code=region_code,
        employment_status=employment_status,
    )


def test_open_policy_with_age_in_range_matches_with_no_reasons():
    result = evaluate_policy(
        make_policy(policy_id="policy-match"),
        make_profile(age=25),
    )

    assert result.policy_id == "policy-match"
    assert result.status is MatchStatus.MATCH
    assert result.reasons == ()


def test_closed_policy_immediately_returns_no_match_regardless_of_age():
    result = evaluate_policy(
        make_policy(application_status=ApplicationStatus.CLOSED),
        make_profile(age=25, region_code="99999", employment_status="재직자"),
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
        make_profile(age=25),
    )

    assert result.status is MatchStatus.UNKNOWN
    assert result.reasons == (expected_reason,)


@pytest.mark.parametrize(
    ("policy", "profile", "expected_reason"),
    [
        (
            make_policy(),
            make_profile(age=None),
            "사용자 나이가 입력되지 않았습니다.",
        ),
        (
            make_policy(age_min=None, age_max=None),
            make_profile(age=25),
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
        make_profile(age=age),
    )

    assert result.status is MatchStatus.NO_MATCH
    assert result.reasons == ("지원 연령 19~39세에 해당하지 않습니다.",)


def test_age_below_minimum_only_policy_is_no_match_with_exact_reason():
    result = evaluate_policy(
        make_policy(age_min=19, age_max=None),
        make_profile(age=18),
    )

    assert result.status is MatchStatus.NO_MATCH
    assert result.reasons == ("지원 연령 19세 이상에 해당하지 않습니다.",)


def test_age_above_maximum_only_policy_is_no_match_with_exact_reason():
    result = evaluate_policy(
        make_policy(age_min=None, age_max=39),
        make_profile(age=40),
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
        make_profile(age=18),
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
        make_profile(age=25, region_code=region_code),
    )

    assert result.status is MatchStatus.UNKNOWN
    assert result.reasons == ("사용자 지역이 입력되지 않았습니다.",)


@pytest.mark.parametrize("region_code", [None, "   "])
def test_missing_policy_region_is_unknown(region_code):
    result = evaluate_policy(
        make_policy(region_code=region_code),
        make_profile(age=25),
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
        make_profile(age=25),
    )

    assert result.status is MatchStatus.MATCH
    assert result.reasons == ()


def test_region_mismatch_is_no_match_with_exact_reason():
    result = evaluate_policy(
        make_policy(region_code="29110,29155"),
        make_profile(age=25),
    )

    assert result.status is MatchStatus.NO_MATCH
    assert result.reasons == ("지원 지역에 해당하지 않습니다.",)


def test_many_policy_region_codes_match_when_user_code_is_included():
    nationwide_like_codes = ",".join(str(code) for code in range(29000, 29255))
    result = evaluate_policy(
        make_policy(region_code=nationwide_like_codes),
        make_profile(age=25),
    )

    assert result.status is MatchStatus.MATCH
    assert result.reasons == ()


def test_upcoming_policy_with_region_mismatch_returns_no_match_and_ordered_reasons():
    result = evaluate_policy(
        make_policy(
            application_status=ApplicationStatus.UPCOMING,
            region_code="29110",
        ),
        make_profile(age=25),
    )

    assert result.status is MatchStatus.NO_MATCH
    assert result.reasons == (
        "아직 신청 기간이 시작되지 않았습니다.",
        "지원 지역에 해당하지 않습니다.",
    )


def test_age_and_region_mismatch_reasons_are_ordered_after_status():
    result = evaluate_policy(
        make_policy(age_min=19, age_max=39, region_code="29110"),
        make_profile(age=18),
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
        make_profile(age=18, region_code=None, employment_status=None),
    )

    assert result.status is MatchStatus.NO_MATCH
    assert result.reasons == ("신청이 마감된 정책입니다.",)


@pytest.mark.parametrize("employment_status", [None, "   "])
def test_missing_user_employment_status_is_unknown(employment_status):
    result = evaluate_policy(
        make_policy(),
        make_profile(employment_status=employment_status),
    )

    assert result.status is MatchStatus.UNKNOWN
    assert result.reasons == ("사용자 취업 상태가 입력되지 않았습니다.",)


@pytest.mark.parametrize("employment_status", [None, "   "])
def test_missing_policy_employment_status_is_unknown(employment_status):
    result = evaluate_policy(
        make_policy(employment_status=employment_status),
        make_profile(),
    )

    assert result.status is MatchStatus.UNKNOWN
    assert result.reasons == ("정책의 취업 상태 조건을 확인할 수 없습니다.",)


@pytest.mark.parametrize(
    ("policy_employment_status", "profile_employment_status"),
    [
        ("미취업자", "미취업자"),
        (" 미취업자 ", "미취업자"),
        ("미취업자", " 미취업자 "),
    ],
)
def test_employment_status_matches_exact_label_after_strip(
    policy_employment_status,
    profile_employment_status,
):
    result = evaluate_policy(
        make_policy(employment_status=policy_employment_status),
        make_profile(employment_status=profile_employment_status),
    )

    assert result.status is MatchStatus.MATCH
    assert result.reasons == ()


def test_unrestricted_policy_employment_status_matches_any_user_status():
    result = evaluate_policy(
        make_policy(employment_status="제한없음"),
        make_profile(employment_status="재직자"),
    )

    assert result.status is MatchStatus.MATCH
    assert result.reasons == ()


def test_employment_status_mismatch_is_no_match_with_exact_reason():
    result = evaluate_policy(
        make_policy(employment_status="미취업자"),
        make_profile(employment_status="재직자"),
    )

    assert result.status is MatchStatus.NO_MATCH
    assert result.reasons == ("취업 상태 조건에 해당하지 않습니다.",)


def test_upcoming_policy_with_employment_mismatch_returns_no_match_and_ordered_reasons():
    result = evaluate_policy(
        make_policy(
            application_status=ApplicationStatus.UPCOMING,
            employment_status="미취업자",
        ),
        make_profile(employment_status="재직자"),
    )

    assert result.status is MatchStatus.NO_MATCH
    assert result.reasons == (
        "아직 신청 기간이 시작되지 않았습니다.",
        "취업 상태 조건에 해당하지 않습니다.",
    )


def test_age_region_and_employment_mismatch_reasons_are_ordered():
    result = evaluate_policy(
        make_policy(
            age_min=19,
            age_max=39,
            region_code="29110",
            employment_status="미취업자",
        ),
        make_profile(age=18, region_code="29140", employment_status="재직자"),
    )

    assert result.status is MatchStatus.NO_MATCH
    assert result.reasons == (
        "지원 연령 19~39세에 해당하지 않습니다.",
        "지원 지역에 해당하지 않습니다.",
        "취업 상태 조건에 해당하지 않습니다.",
    )


def test_closed_policy_returns_only_closed_reason_regardless_of_employment_status():
    result = evaluate_policy(
        make_policy(
            application_status=ApplicationStatus.CLOSED,
            employment_status="미취업자",
        ),
        make_profile(employment_status="재직자"),
    )

    assert result.status is MatchStatus.NO_MATCH
    assert result.reasons == ("신청이 마감된 정책입니다.",)


@pytest.mark.parametrize("income_condition", [None, "   "])
def test_missing_policy_income_condition_is_unknown(income_condition):
    result = evaluate_policy(
        make_policy(income_condition=income_condition),
        make_profile(),
    )

    assert result.status is MatchStatus.UNKNOWN
    assert result.reasons == ("정책의 소득 조건을 확인할 수 없습니다.",)


def test_unrestricted_income_condition_matches_after_strip():
    result = evaluate_policy(
        make_policy(income_condition=" 무관 "),
        make_profile(),
    )

    assert result.status is MatchStatus.MATCH
    assert result.reasons == ()


@pytest.mark.parametrize(
    "income_condition",
    [
        "연소득 / 최대 5000",
        "기타 / 중위소득 150% 이하",
        "중위소득 100% 이하",
        "가구소득 기준",
    ],
)
def test_complex_income_condition_is_unknown_with_exact_reason(income_condition):
    result = evaluate_policy(
        make_policy(income_condition=income_condition),
        make_profile(),
    )

    assert result.status is MatchStatus.UNKNOWN
    assert result.reasons == ("소득 조건은 세부 확인이 필요합니다.",)


def test_region_mismatch_with_complex_income_is_no_match_with_ordered_reasons():
    result = evaluate_policy(
        make_policy(
            region_code="29110",
            income_condition="연소득 / 최대 5000",
        ),
        make_profile(region_code="29140"),
    )

    assert result.status is MatchStatus.NO_MATCH
    assert result.reasons == (
        "지원 지역에 해당하지 않습니다.",
        "소득 조건은 세부 확인이 필요합니다.",
    )


def test_employment_mismatch_with_complex_income_is_no_match_with_ordered_reasons():
    result = evaluate_policy(
        make_policy(
            employment_status="미취업자",
            income_condition="기타 / 중위소득 150% 이하",
        ),
        make_profile(employment_status="재직자"),
    )

    assert result.status is MatchStatus.NO_MATCH
    assert result.reasons == (
        "취업 상태 조건에 해당하지 않습니다.",
        "소득 조건은 세부 확인이 필요합니다.",
    )


def test_upcoming_policy_with_complex_income_is_unknown_with_ordered_reasons():
    result = evaluate_policy(
        make_policy(
            application_status=ApplicationStatus.UPCOMING,
            income_condition="연소득 / 최대 5000",
        ),
        make_profile(),
    )

    assert result.status is MatchStatus.UNKNOWN
    assert result.reasons == (
        "아직 신청 기간이 시작되지 않았습니다.",
        "소득 조건은 세부 확인이 필요합니다.",
    )


def test_closed_policy_returns_only_closed_reason_regardless_of_income_condition():
    result = evaluate_policy(
        make_policy(
            application_status=ApplicationStatus.CLOSED,
            income_condition="연소득 / 최대 5000",
        ),
        make_profile(),
    )

    assert result.status is MatchStatus.NO_MATCH
    assert result.reasons == ("신청이 마감된 정책입니다.",)


def test_evaluate_policies_returns_empty_batch_for_empty_input():
    batch = evaluate_policies([], make_profile())

    assert batch.matched == ()
    assert batch.unknown == ()
    assert batch.no_match == ()


def test_evaluate_policies_groups_statuses_and_preserves_group_order():
    match_a = make_policy(policy_id="policy-1")
    unknown_a = make_policy(policy_id="policy-2", income_condition="연소득 / 최대 5000")
    no_match_a = make_policy(policy_id="policy-3", region_code="11110")
    match_b = make_policy(policy_id="policy-4")
    unknown_b = make_policy(policy_id="policy-5", income_condition=None)
    no_match_b = make_policy(policy_id="policy-6", employment_status="재직자")
    policies = [match_a, unknown_a, no_match_a, match_b, unknown_b, no_match_b]

    batch = evaluate_policies(policies, make_profile())

    assert [item.policy.policy_id for item in batch.matched] == [
        "policy-1",
        "policy-4",
    ]
    assert [item.policy.policy_id for item in batch.unknown] == [
        "policy-2",
        "policy-5",
    ]
    assert [item.policy.policy_id for item in batch.no_match] == [
        "policy-3",
        "policy-6",
    ]
    assert all(item.result.status is MatchStatus.MATCH for item in batch.matched)
    assert all(item.result.status is MatchStatus.UNKNOWN for item in batch.unknown)
    assert all(item.result.status is MatchStatus.NO_MATCH for item in batch.no_match)


def test_evaluate_policies_preserves_policy_and_single_result_details():
    policy = make_policy(policy_id="policy-preserved", income_condition="연소득 / 최대 5000")
    profile = make_profile()
    single_result = evaluate_policy(policy, profile)

    batch = evaluate_policies([policy], profile)
    evaluated = batch.unknown[0]

    assert evaluated.policy is policy
    assert evaluated.result.policy_id == policy.policy_id
    assert evaluated.result == single_result
    assert evaluated.result.reasons == single_result.reasons


def test_evaluate_policies_accepts_generator_input():
    policies = (
        policy
        for policy in [
            make_policy(policy_id="policy-match"),
            make_policy(policy_id="policy-unknown", income_condition="연소득 / 최대 5000"),
            make_policy(policy_id="policy-no-match", region_code="11110"),
        ]
    )

    batch = evaluate_policies(policies, make_profile())

    assert [item.policy.policy_id for item in batch.matched] == ["policy-match"]
    assert [item.policy.policy_id for item in batch.unknown] == ["policy-unknown"]
    assert [item.policy.policy_id for item in batch.no_match] == ["policy-no-match"]


def test_evaluate_policies_accepts_sqlite_list_policies_results(tmp_path):
    db_path = tmp_path / "policies.sqlite3"
    policies = [
        make_policy(policy_id="policy-a-match"),
        make_policy(policy_id="policy-b-unknown", income_condition="연소득 / 최대 5000"),
        make_policy(policy_id="policy-c-no-match", region_code="11110"),
    ]
    connection = connect_database(db_path)
    try:
        initialize_database(connection)
        assert upsert_policies(connection, policies) == 3

        stored_policies = list_policies(connection)
        batch = evaluate_policies(stored_policies, make_profile())

        assert [item.policy.policy_id for item in batch.matched] == [
            "policy-a-match"
        ]
        assert [item.policy.policy_id for item in batch.unknown] == [
            "policy-b-unknown"
        ]
        assert [item.policy.policy_id for item in batch.no_match] == [
            "policy-c-no-match"
        ]
        assert [policy.policy_id for policy in stored_policies] == [
            "policy-a-match",
            "policy-b-unknown",
            "policy-c-no-match",
        ]
    finally:
        connection.close()
