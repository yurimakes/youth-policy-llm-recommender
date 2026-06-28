"""matching.py

사용자 조건과 정책 데이터의 최소 1차 판정 규칙을 정의합니다.
"""

from __future__ import annotations

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


@dataclass(frozen=True)
class MatchResult:
    policy_id: str
    status: MatchStatus
    reasons: tuple[str, ...]


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
