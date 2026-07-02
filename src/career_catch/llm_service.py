"""llm_service.py

검색된 공식 정책 데이터 기반 AI 설명 생성을 담당합니다.
"""

from __future__ import annotations

from typing import Any


class ExplanationError(RuntimeError):
    """AI 설명 생성 실패를 나타냅니다."""


def _policy_context(policy: dict[str, Any]) -> dict[str, str]:
    return {
        "policy_id": str(policy.get("policy_id") or "확인 필요"),
        "policy_name": str(policy.get("policy_name") or "확인 필요"),
        "category": str(policy.get("category") or "확인 필요"),
        "summary": str(policy.get("summary") or "확인 필요"),
        "eligibility_text": str(policy.get("eligibility_text") or "확인 필요"),
        "benefit_text": str(policy.get("benefit_text") or "확인 필요"),
        "application_start": str(policy.get("application_start") or "확인 필요"),
        "application_end": str(policy.get("application_end") or "확인 필요"),
        "application_method": str(policy.get("application_method") or "확인 필요"),
        "source_url": str(policy.get("source_url") or "확인 필요"),
        "last_verified_at": str(policy.get("last_verified_at") or "확인 필요"),
        "status": str(policy.get("status") or "UNKNOWN"),
        "reasons": "\n".join(str(reason) for reason in policy.get("reasons") or ["확인 필요"]),
    }


def build_explanation_messages(
    *,
    user_interest: str,
    user_profile: dict[str, Any],
    policies: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """검색된 Top-5 정책만 포함한 grounded prompt를 구성합니다."""
    policy_blocks = []
    for index, policy in enumerate(policies, start=1):
        context = _policy_context(policy)
        policy_blocks.append(
            "\n".join(
                [
                    f"[정책 {index}]",
                    f"정책 ID: {context['policy_id']}",
                    f"정책명: {context['policy_name']}",
                    f"분류: {context['category']}",
                    f"요약: {context['summary']}",
                    f"자격 조건: {context['eligibility_text']}",
                    f"지원 내용: {context['benefit_text']}",
                    f"신청 기간: {context['application_start']} ~ {context['application_end']}",
                    f"신청 방법: {context['application_method']}",
                    f"공식 출처: {context['source_url']}",
                    f"검증일: {context['last_verified_at']}",
                    f"규칙 평가: {context['status']}",
                    f"규칙 평가 이유: {context['reasons']}",
                ]
            )
        )

    return [
        {
            "role": "system",
            "content": (
                "공식 정책 데이터만 근거로 청년 정책 추천 설명을 작성한다. "
                "최종 신청 자격이 확정되었다고 말하지 않는다. "
                "정책 데이터에 없는 내용은 추측하지 말고 '확인 필요'라고 표시한다."
            ),
        },
        {
            "role": "user",
            "content": "\n\n".join(
                [
                    f"사용자 관심사: {user_interest}",
                    f"사용자 조건: {user_profile}",
                    "아래 검색된 Top-5 정책만 사용해 설명하세요.",
                    *policy_blocks,
                    (
                        "각 정책별로 추천 이유, 사용자 조건과 일치하는 점, 확인이 필요한 조건, "
                        "신청 기간과 공식 출처 안내를 한국어로 간결하게 작성하세요."
                    ),
                ]
            ),
        },
    ]


def generate_explanation(
    *,
    client: Any,
    chat_model: str,
    user_interest: str,
    user_profile: dict[str, Any],
    policies: list[dict[str, Any]],
) -> str:
    """OpenAI Chat API로 추천 설명을 생성합니다."""
    if not policies:
        return "AI 설명을 생성할 검색 결과가 없습니다."

    messages = build_explanation_messages(
        user_interest=user_interest,
        user_profile=user_profile,
        policies=policies,
    )
    try:
        response = client.chat.completions.create(
            model=chat_model,
            messages=messages,
            temperature=0.2,
        )
        content = response.choices[0].message.content
    except Exception as exc:
        raise ExplanationError("AI 설명 생성에 실패했습니다.") from exc

    if not content:
        raise ExplanationError("AI 설명 응답이 비어 있습니다.")
    return str(content)
