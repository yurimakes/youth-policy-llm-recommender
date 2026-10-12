"""Explain card relevance using policy text without changing eligibility checks."""

from __future__ import annotations

from dataclasses import dataclass

from youth_policy.intake import CARD_OPTIONS, IntakeState
from youth_policy.models import PolicyRecord


TERMS: dict[str, tuple[str, ...]] = {
    "living_cost": ("생활비", "주거", "월세", "전세", "장학", "학자금", "생계"),
    "low_burden": ("참여", "활동", "문화"),
    "counseling": ("상담",),
    "employment": ("취업", "구직", "일자리"),
    "housing": ("주거", "월세", "전세", "주택"),
    "learning": ("교육", "훈련", "학습", "직무"),
}


@dataclass(frozen=True)
class Relevance:
    score: int
    reasons: tuple[str, ...]


def assess_relevance(policy: PolicyRecord, state: IntakeState) -> Relevance:
    """Use only explicit goal/interest selections and recorded descriptive text.

    This is a transparent keyword baseline, not an AI prediction or eligibility
    decision. Participation keywords do not establish low effort or availability.
    """
    cards = dict(state.cards)
    score = 0
    reasons: list[str] = []
    for key in ("interest", "goal"):
        value = cards.get(key)
        terms = TERMS.get(value or "", ())
        if not terms:
            continue
        label = dict(CARD_OPTIONS[key])[value]
        for field, text, weight in (
            ("분야", policy.category, 3),
            ("정책명", policy.policy_name, 2),
            ("요약", policy.summary, 1),
        ):
            matches = tuple(term for term in terms if term in (text or ""))
            if matches:
                score += weight
                reasons.append(f"선택한 ‘{label}’와 관련된 ‘{' · '.join(matches)}’ 표현이 {field}에 있어요.")
        if value == "low_burden" and any(term in (policy.category or "") + policy.policy_name + (policy.summary or "") for term in terms):
            reasons.append("활동의 실제 부담·시간·참여 방식은 공고에서 별도로 확인해야 해요.")
    if not reasons:
        reasons.append("선택한 관심과 직접 연결되는 표현이 확인되지 않아, 조건과 공식 공고를 살펴볼 후보로 보여드려요.")
    return Relevance(score, tuple(reasons))
