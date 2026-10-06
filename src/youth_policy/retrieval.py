"""retrieval.py

FAISS 기반 정책 검색과 임베딩 입력 구성을 담당합니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class RetrievalError(RuntimeError):
    """검색 인덱스 생성 또는 임베딩 호출 실패를 나타냅니다."""


@dataclass(frozen=True)
class RankedPolicy:
    """FAISS 검색 결과와 벡터 위치 매핑을 보관합니다."""

    policy: dict[str, Any]
    policy_id: str
    vector_position: int
    score: float


def _first_value(source: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = source.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def build_embedding_text(policy: dict[str, Any]) -> str:
    """공식 정책 필드만 사용해 임베딩 텍스트를 구성합니다."""
    embedding_text = _first_value(policy, "embedding_text")
    if embedding_text:
        return embedding_text

    fields = (
        _first_value(policy, "policy_name", "name", "title"),
        _first_value(policy, "category"),
        _first_value(policy, "summary", "description", "support_content"),
        _first_value(policy, "eligibility_text", "eligibility", "condition_text"),
        _first_value(policy, "benefit_text", "benefit", "support_detail"),
        _first_value(policy, "application_method", "apply_method"),
    )
    return "\n".join(field for field in fields if field)


def create_embeddings(client: Any, model: str, texts: list[str]) -> list[list[float]]:
    """OpenAI 임베딩 API 호출 결과를 벡터 리스트로 반환합니다."""
    if not texts:
        return []
    response = client.embeddings.create(model=model, input=texts)
    return [list(item.embedding) for item in response.data]


def rank_policies(
    *,
    candidates: list[dict[str, Any]],
    query: str,
    client: Any,
    embedding_model: str,
    top_k: int = 5,
) -> list[RankedPolicy]:
    """후보 정책을 FAISS 유사도 기준으로 검색합니다."""
    if not query.strip() or not candidates:
        return []

    try:
        import faiss
        import numpy as np
    except ImportError as exc:
        raise RetrievalError("FAISS 검색 의존성을 불러올 수 없습니다.") from exc

    texts = [build_embedding_text(policy) for policy in candidates]
    usable_items = [
        (index, policy, text)
        for index, (policy, text) in enumerate(zip(candidates, texts))
        if text.strip()
    ]
    if not usable_items:
        return []

    try:
        embeddings = create_embeddings(
            client,
            embedding_model,
            [text for _, _, text in usable_items],
        )
        query_embedding = create_embeddings(client, embedding_model, [query])[0]
    except Exception as exc:
        raise RetrievalError("OpenAI 임베딩 생성에 실패했습니다.") from exc

    vectors = np.array(embeddings, dtype="float32")
    query_vector = np.array([query_embedding], dtype="float32")
    faiss.normalize_L2(vectors)
    faiss.normalize_L2(query_vector)

    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    scores, positions = index.search(query_vector, min(top_k, len(usable_items)))

    ranked: list[RankedPolicy] = []
    for score, vector_position in zip(scores[0], positions[0]):
        if vector_position < 0:
            continue
        _, policy, _ = usable_items[int(vector_position)]
        ranked.append(
            RankedPolicy(
                policy=policy,
                policy_id=_first_value(policy, "policy_id"),
                vector_position=int(vector_position),
                score=float(score),
            )
        )
    return ranked
