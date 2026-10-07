"""intake_service.py

진행 상태와 기존 정책 모델을 연결해 필요한 질문과 다음 행동을 구성합니다.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime
from urllib.parse import urlparse

from youth_policy.conditions import ConditionAssessment, ConditionStatus, assess_conditions
from youth_policy.intake import IntakeState, Stage
from youth_policy.models import PolicyRecord


@dataclass(frozen=True)
class Question:
    key: str
    prompt: str
    purpose: str


@dataclass(frozen=True)
class PolicyGuidance:
    policy_id: str
    policy_name: str
    assessment: ConditionAssessment
    next_actions: tuple[str, ...]
    source_url: str | None
    last_verified_at: datetime


QUESTIONS = {
    "age": Question("age", "만 나이를 알려주세요.", "정책의 연령 범위와 비교하기 위해 필요해요. 모르면 건너뛸 수 있어요."),
    "region_code": Question("region_code", "실제로 거주하는 지역은 어디인가요?", "기록된 지원 지역과 비교해요. 서울 거주로 자동 가정하지 않아요."),
    "employment_status": Question("employment_status", "현재 취업 상태를 확인해 주세요.", "상황 카드와 별개로 선택한 정책의 취업 조건을 확인해요."),
}


def build_guidance(
    policies: tuple[PolicyRecord, ...], state: IntakeState, *, reference_date: date
) -> tuple[PolicyGuidance, ...]:
    """명확한 불일치를 제외하고 공식 정보와 남은 확인 행동을 반환합니다."""
    results = []
    ids = [p.policy_id for p in policies]
    if len(ids) != len(set(ids)):
        raise ValueError("policy IDs must be unique")
    for policy in policies:
        assessment = assess_conditions(policy, state.profile, reference_date=reference_date)
        if assessment.status is ConditionStatus.NOT_MET:
            continue
        missing = [check.field for check in assessment.checks if check.status is ConditionStatus.INPUT_MISSING]
        actions = []
        if missing:
            actions.append("모르는 정보는 건너뛸 수 있습니다. 확인 가능한 조건부터 확인하세요.")
        if any(check.status is ConditionStatus.CHECK_REQUIRED for check in assessment.checks):
            actions.append("확인 필요 항목은 공식 공고 또는 담당 기관에서 확인하세요.")
        source_url = _source_url(policy.source_url)
        actions.append("공식 공고에서 최종 자격과 준비 절차를 확인하세요." if source_url
                       else "공식 공고 URL이 없어 제공기관에서 공고를 찾아 확인해야 합니다.")
        results.append(PolicyGuidance(policy.policy_id, policy.policy_name, assessment,
                                      tuple(actions), source_url, policy.last_verified_at))
    return tuple(results)


def next_question(
    state: IntakeState, policies: tuple[PolicyRecord, ...], *, reference_date: date
) -> Question | None:
    if state.stage not in {Stage.BASIC, Stage.DETAIL}:
        return None
    candidates = build_guidance(policies, state, reference_date=reference_date)
    if state.stage is Stage.DETAIL:
        candidates = tuple(p for p in candidates if p.policy_id == state.interested_policy_id)
    missing = {check.field for p in candidates for check in p.assessment.checks
               if check.status is ConditionStatus.INPUT_MISSING}
    allowed = ("age", "region_code") if state.stage is Stage.BASIC else tuple(QUESTIONS)
    for key in allowed:
        if key in missing and key not in state.answered and key not in state.skipped:
            return QUESTIONS[key]
    return None


def detail_is_useful(
    state: IntakeState, policies: tuple[PolicyRecord, ...], *, reference_date: date
) -> bool:
    """명시적 관심 뒤에 후보를 구분할 입력이 더 필요한지 확인합니다."""
    if state.interested_policy_id is None:
        return False
    detail_state = replace(state, stage=Stage.DETAIL)
    return next_question(detail_state, policies, reference_date=reference_date) is not None


def _source_url(value: str | None) -> str | None:
    if value is None:
        return None
    parsed = urlparse(value)
    return value if parsed.scheme in {"http", "https"} and parsed.netloc else None
