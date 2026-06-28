"""matching.py

사용자 조건과 정책 데이터의 최소 1차 판정 규칙을 정의합니다.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum

from career_catch.models import ApplicationStatus, PolicyRecord


class MatchStatus(str, Enum):
    MATCH = "match"
    NO_MATCH = "no_match"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class UserProfile:
    age: int | None = None
    region_code: str | None = None
    employment_status: str | None = None


@dataclass(frozen=True)
class MatchResult:
    policy_id: str
    status: MatchStatus
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class EvaluatedPolicy:
    policy: PolicyRecord
    result: MatchResult


@dataclass(frozen=True)
class PolicyEvaluationBatch:
    matched: tuple[EvaluatedPolicy, ...]
    unknown: tuple[EvaluatedPolicy, ...]
    no_match: tuple[EvaluatedPolicy, ...]


def evaluate_policy(
    policy: PolicyRecord,
    profile: UserProfile,
) -> MatchResult:
    reasons: list[str] = []
    statuses: list[MatchStatus] = []

    if policy.application_status is ApplicationStatus.CLOSED:
        return MatchResult(
            policy_id=policy.policy_id,
            status=MatchStatus.NO_MATCH,
            reasons=("신청이 마감된 정책입니다.",),
        )
    if policy.application_status is ApplicationStatus.UPCOMING:
        statuses.append(MatchStatus.UNKNOWN)
        reasons.append("아직 신청 기간이 시작되지 않았습니다.")
    elif policy.application_status is ApplicationStatus.UNKNOWN:
        statuses.append(MatchStatus.UNKNOWN)
        reasons.append("신청 가능 상태를 확인할 수 없습니다.")
    else:
        statuses.append(MatchStatus.MATCH)

    age_status, age_reason = _evaluate_age(policy, profile)
    statuses.append(age_status)
    if age_reason is not None:
        reasons.append(age_reason)

    region_status, region_reason = _evaluate_region(policy, profile)
    statuses.append(region_status)
    if region_reason is not None:
        reasons.append(region_reason)

    employment_status, employment_reason = _evaluate_employment_status(policy, profile)
    statuses.append(employment_status)
    if employment_reason is not None:
        reasons.append(employment_reason)

    income_status, income_reason = _evaluate_income_condition(policy)
    statuses.append(income_status)
    if income_reason is not None:
        reasons.append(income_reason)

    if MatchStatus.NO_MATCH in statuses:
        status = MatchStatus.NO_MATCH
    elif MatchStatus.UNKNOWN in statuses:
        status = MatchStatus.UNKNOWN
    else:
        status = MatchStatus.MATCH

    return MatchResult(
        policy_id=policy.policy_id,
        status=status,
        reasons=tuple(reasons),
    )


def evaluate_policies(
    policies: Iterable[PolicyRecord],
    profile: UserProfile,
) -> PolicyEvaluationBatch:
    matched: list[EvaluatedPolicy] = []
    unknown: list[EvaluatedPolicy] = []
    no_match: list[EvaluatedPolicy] = []

    for policy in policies:
        result = evaluate_policy(policy, profile)
        evaluated_policy = EvaluatedPolicy(policy=policy, result=result)
        if result.status is MatchStatus.MATCH:
            matched.append(evaluated_policy)
        elif result.status is MatchStatus.UNKNOWN:
            unknown.append(evaluated_policy)
        else:
            no_match.append(evaluated_policy)

    return PolicyEvaluationBatch(
        matched=tuple(matched),
        unknown=tuple(unknown),
        no_match=tuple(no_match),
    )


def _evaluate_age(
    policy: PolicyRecord,
    profile: UserProfile,
) -> tuple[MatchStatus, str | None]:
    if profile.age is None:
        return MatchStatus.UNKNOWN, "사용자 나이가 입력되지 않았습니다."
    if policy.age_min is None and policy.age_max is None:
        return MatchStatus.UNKNOWN, "정책의 연령 조건을 확인할 수 없습니다."
    if policy.age_min is not None and profile.age < policy.age_min:
        return MatchStatus.NO_MATCH, _age_mismatch_reason(policy)
    if policy.age_max is not None and profile.age > policy.age_max:
        return MatchStatus.NO_MATCH, _age_mismatch_reason(policy)

    return MatchStatus.MATCH, None


def _age_mismatch_reason(policy: PolicyRecord) -> str:
    if policy.age_min is not None and policy.age_max is not None:
        age_range = f"{policy.age_min}~{policy.age_max}세"
    elif policy.age_min is not None:
        age_range = f"{policy.age_min}세 이상"
    else:
        age_range = f"{policy.age_max}세 이하"

    return f"지원 연령 {age_range}에 해당하지 않습니다."


def _evaluate_region(
    policy: PolicyRecord,
    profile: UserProfile,
) -> tuple[MatchStatus, str | None]:
    if profile.region_code is None or not profile.region_code.strip():
        return MatchStatus.UNKNOWN, "사용자 지역이 입력되지 않았습니다."

    policy_region_codes = _parse_region_codes(policy.region_code)
    if not policy_region_codes:
        return MatchStatus.UNKNOWN, "정책의 지역 조건을 확인할 수 없습니다."

    if profile.region_code.strip() in policy_region_codes:
        return MatchStatus.MATCH, None

    return MatchStatus.NO_MATCH, "지원 지역에 해당하지 않습니다."


def _parse_region_codes(region_code: str | None) -> set[str]:
    if region_code is None:
        return set()

    return {code.strip() for code in region_code.split(",") if code.strip()}


def _evaluate_employment_status(
    policy: PolicyRecord,
    profile: UserProfile,
) -> tuple[MatchStatus, str | None]:
    if profile.employment_status is None or not profile.employment_status.strip():
        return MatchStatus.UNKNOWN, "사용자 취업 상태가 입력되지 않았습니다."
    if policy.employment_status is None or not policy.employment_status.strip():
        return MatchStatus.UNKNOWN, "정책의 취업 상태 조건을 확인할 수 없습니다."

    user_employment_status = profile.employment_status.strip()
    policy_employment_status = policy.employment_status.strip()
    if policy_employment_status == "제한없음":
        return MatchStatus.MATCH, None
    if user_employment_status == policy_employment_status:
        return MatchStatus.MATCH, None

    return MatchStatus.NO_MATCH, "취업 상태 조건에 해당하지 않습니다."


def _evaluate_income_condition(policy: PolicyRecord) -> tuple[MatchStatus, str | None]:
    if policy.income_condition is None or not policy.income_condition.strip():
        return MatchStatus.UNKNOWN, "정책의 소득 조건을 확인할 수 없습니다."
    if policy.income_condition.strip() == "무관":
        return MatchStatus.MATCH, None

    return MatchStatus.UNKNOWN, "소득 조건은 세부 확인이 필요합니다."
