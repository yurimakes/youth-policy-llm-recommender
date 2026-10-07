"""conditions.py

개별 조건의 근거 부족과 사용자 입력 부족을 분리해 평가합니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
import re

from youth_policy.codebook import CODEBOOKS
from youth_policy.matching import MatchStatus, UserProfile
from youth_policy.models import ApplicationStatus, PolicyRecord


class ConditionStatus(str, Enum):
    CONFIRMED = "confirmed"
    NOT_MET = "not_met"
    CHECK_REQUIRED = "check_required"
    INPUT_MISSING = "input_missing"


STATUS_LABELS = {
    ConditionStatus.CONFIRMED: "확인됨",
    ConditionStatus.NOT_MET: "조건에 맞지 않음",
    ConditionStatus.CHECK_REQUIRED: "확인 필요",
    ConditionStatus.INPUT_MISSING: "사용자 입력 부족",
}
EMPLOYMENT_VALUES = frozenset(CODEBOOKS["jobCd"].values()) - {"제한없음", "기타"}


@dataclass(frozen=True)
class ConditionCheck:
    field: str
    status: ConditionStatus
    reason: str


@dataclass(frozen=True)
class ConditionAssessment:
    policy_id: str
    checks: tuple[ConditionCheck, ...]

    @property
    def status(self) -> ConditionStatus:
        for status in (
            ConditionStatus.NOT_MET,
            ConditionStatus.CHECK_REQUIRED,
            ConditionStatus.INPUT_MISSING,
        ):
            if any(check.status is status for check in self.checks):
                return status
        return ConditionStatus.CONFIRMED

    @property
    def legacy_status(self) -> MatchStatus:
        if self.status is ConditionStatus.NOT_MET:
            return MatchStatus.NO_MATCH
        if self.status is ConditionStatus.CONFIRMED:
            return MatchStatus.MATCH
        return MatchStatus.UNKNOWN


def validate_profile(profile: UserProfile) -> None:
    if profile.age is not None and (type(profile.age) is not int or not 0 <= profile.age <= 120):
        raise ValueError("age must be an integer between 0 and 120")
    if profile.region_code is not None and (
        not isinstance(profile.region_code, str)
        or re.fullmatch(r"[0-9]{5}", profile.region_code) is None
    ):
        raise ValueError("region_code must be a five-digit code")
    if profile.employment_status is not None and profile.employment_status not in EMPLOYMENT_VALUES:
        raise ValueError("employment_status must be a supported explicit answer")


def assess_conditions(
    policy: PolicyRecord, profile: UserProfile, *, reference_date: date
) -> ConditionAssessment:
    """정책의 개별 조건을 평가하며 전체 신청 자격을 확정하지 않습니다."""
    validate_profile(profile)
    checks = [_period(policy, reference_date), _age(policy, profile), _region(policy, profile)]
    checks.append(_employment(policy, profile))
    checks.append(ConditionCheck(
        "income", ConditionStatus.CONFIRMED if policy.income_condition == "무관"
        else ConditionStatus.CHECK_REQUIRED,
        "공식 데이터의 소득 무관 조건을 확인했습니다." if policy.income_condition == "무관"
        else "소득·가구 기준과 단위는 공식 공고 또는 기관에서 확인해야 합니다.",
    ))
    checks.append(ConditionCheck(
        "education", ConditionStatus.CONFIRMED if policy.education_status == "제한없음"
        else ConditionStatus.CHECK_REQUIRED,
        "학력 제한이 없는 것으로 기록돼 있습니다." if policy.education_status == "제한없음"
        else "학력 조건은 공식 공고에서 확인해야 합니다.",
    ))
    # This model cannot distinguish absent additional conditions from a complete notice.
    checks.append(ConditionCheck(
        "eligibility", ConditionStatus.CHECK_REQUIRED,
        "추가·예외 조건은 기관 확인이 필요합니다." if policy.eligibility_text
        else "추가·예외 조건의 유무는 공식 공고에서 확인해야 합니다.",
    ))
    return ConditionAssessment(policy.policy_id, tuple(checks))


def _period(policy: PolicyRecord, today: date) -> ConditionCheck:
    if policy.application_status is ApplicationStatus.CLOSED or (
        policy.application_end is not None and today > policy.application_end
    ):
        return ConditionCheck("application", ConditionStatus.NOT_MET, "신청 기간이 마감됐습니다.")
    if policy.application_start is not None and today < policy.application_start:
        return ConditionCheck("application", ConditionStatus.CHECK_REQUIRED, "신청 시작 전입니다. 공식 일정 확인이 필요합니다.")
    if policy.application_start is not None and policy.application_end is not None:
        return ConditionCheck("application", ConditionStatus.CONFIRMED, "입력된 신청 기간에 해당합니다.")
    # An OPEN snapshot alone does not prove that a policy is still open today.
    return ConditionCheck("application", ConditionStatus.CHECK_REQUIRED, "최신 신청 기간·상시 접수 여부를 공식 공고에서 확인해야 합니다.")


def _age(policy: PolicyRecord, profile: UserProfile) -> ConditionCheck:
    if policy.age_min is None and policy.age_max is None:
        return ConditionCheck("age", ConditionStatus.CHECK_REQUIRED, "정책의 연령 기준이 없습니다.")
    if profile.age is None:
        return ConditionCheck("age", ConditionStatus.INPUT_MISSING, "만 나이를 확인하지 않았습니다.")
    if (policy.age_min is not None and profile.age < policy.age_min) or (
        policy.age_max is not None and profile.age > policy.age_max
    ):
        return ConditionCheck("age", ConditionStatus.NOT_MET, "입력한 만 나이가 지원 연령 범위를 벗어납니다.")
    return ConditionCheck("age", ConditionStatus.CONFIRMED, "입력한 만 나이가 기록된 연령 범위에 해당합니다.")


def _region(policy: PolicyRecord, profile: UserProfile) -> ConditionCheck:
    codes = tuple(part.strip() for part in (policy.region_code or "").split(","))
    if not codes or any(re.fullmatch(r"[0-9]{5}", code) is None or code.endswith("000") for code in codes):
        return ConditionCheck("region_code", ConditionStatus.CHECK_REQUIRED, "지역 범위가 없거나 광역·전국 기준을 추가 확인해야 합니다.")
    if profile.region_code is None:
        return ConditionCheck("region_code", ConditionStatus.INPUT_MISSING, "실제 거주 지역을 확인하지 않았습니다.")
    if profile.region_code not in codes:
        return ConditionCheck("region_code", ConditionStatus.NOT_MET, "입력한 지역이 기록된 지원 지역에 해당하지 않습니다.")
    return ConditionCheck("region_code", ConditionStatus.CONFIRMED, "입력한 지역이 기록된 지원 지역에 해당합니다.")


def _employment(policy: PolicyRecord, profile: UserProfile) -> ConditionCheck:
    if policy.employment_status == "제한없음":
        return ConditionCheck("employment_status", ConditionStatus.CONFIRMED, "취업 상태 제한이 없습니다.")
    if policy.employment_status not in EMPLOYMENT_VALUES:
        return ConditionCheck("employment_status", ConditionStatus.CHECK_REQUIRED, "정책의 취업 상태 조건이 없거나 복잡해 기관 확인이 필요합니다.")
    if profile.employment_status is None:
        return ConditionCheck("employment_status", ConditionStatus.INPUT_MISSING, "실제 취업 상태를 확인하지 않았습니다.")
    if profile.employment_status != policy.employment_status:
        return ConditionCheck("employment_status", ConditionStatus.NOT_MET, "직접 확인한 취업 상태가 기록된 조건과 다릅니다.")
    return ConditionCheck("employment_status", ConditionStatus.CONFIRMED, "직접 확인한 취업 상태가 기록된 조건과 같습니다.")
