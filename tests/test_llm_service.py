"""test_llm_service.py

AI 설명 프롬프트와 OpenAI 호출 격리를 검증합니다.
"""

from __future__ import annotations

from types import SimpleNamespace

from career_catch import llm_service


def test_build_explanation_messages_contains_only_given_policies() -> None:
    messages = llm_service.build_explanation_messages(
        user_interest="월세 지원이 필요해요.",
        user_profile={"age": 24, "region_code": "11680", "employment_status": "미취업자"},
        policies=[
            {
                "policy_id": "P1",
                "policy_name": "청년 월세 지원",
                "summary": "월세를 지원합니다.",
                "source_url": "https://example.test/p1",
            }
        ],
    )

    prompt = messages[1]["content"]

    assert "검색된 Top-5 정책만 사용" in prompt
    assert "청년 월세 지원" in prompt
    assert "https://example.test/p1" in prompt


def test_generate_explanation_uses_mock_client() -> None:
    class MockCompletions:
        def create(self, **kwargs: object) -> SimpleNamespace:
            assert kwargs["model"] == "test-chat-model"
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content="추천 이유와 확인 필요 조건입니다.")
                    )
                ]
            )

    client = SimpleNamespace(
        chat=SimpleNamespace(completions=MockCompletions())
    )

    explanation = llm_service.generate_explanation(
        client=client,
        chat_model="test-chat-model",
        user_interest="자격증 비용 지원",
        user_profile={"age": 24},
        policies=[{"policy_id": "P1", "policy_name": "정책 A"}],
    )

    assert explanation == "추천 이유와 확인 필요 조건입니다."
