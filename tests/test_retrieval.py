"""test_retrieval.py

정책 검색 입력 구성과 OpenAI 임베딩 호출 격리를 검증합니다.
"""

from __future__ import annotations

from types import SimpleNamespace

from youth_policy import retrieval


def test_build_embedding_text_prefers_existing_embedding_text() -> None:
    policy = {
        "embedding_text": "이미 구성된 임베딩 텍스트",
        "policy_name": "무시되는 정책명",
    }

    assert retrieval.build_embedding_text(policy) == "이미 구성된 임베딩 텍스트"


def test_build_embedding_text_uses_official_fields_only() -> None:
    policy = {
        "policy_name": "청년 월세 지원",
        "category": "주거",
        "summary": "월세 일부를 지원합니다.",
        "eligibility_text": "만 19세 이상 청년",
        "benefit_text": "월세 지원",
        "application_method": "온라인 신청",
    }

    text = retrieval.build_embedding_text(policy)

    assert "청년 월세 지원" in text
    assert "주거" in text
    assert "월세 일부를 지원합니다." in text
    assert "온라인 신청" in text


def test_create_embeddings_uses_mock_client() -> None:
    class MockEmbeddings:
        def create(self, model: str, input: list[str]) -> SimpleNamespace:
            assert model == "text-embedding-3-small"
            assert input == ["query"]
            return SimpleNamespace(data=[SimpleNamespace(embedding=[0.1, 0.2])])

    client = SimpleNamespace(embeddings=MockEmbeddings())

    assert retrieval.create_embeddings(client, "text-embedding-3-small", ["query"]) == [[0.1, 0.2]]
