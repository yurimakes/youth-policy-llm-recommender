# 원본 MVP 보존 기록

`v0.1-mvp`는 `23f33e7bc8e51d3e26812faeb479aae7f83ee596`를 가리킨다. 태그 설명은 `Preserve original MVP before service redesign`이다. 이후 고도화는 이 커밋에서 이어지는 별도 브랜치의 일반 커밋으로 진행한다.

원본은 Streamlit·SQLite 기반으로 나이·지역·취업 상태 입력, 삼중 조건 평가, OpenAI 임베딩·FAISS 검색, 공식 정보 기반 설명과 AI 실패 폴백을 구현했다. 2026-07-02 기록에는 자동 테스트 122개와 실제 API 20건 검증이 있다. 이번 새 기능의 검증 결과나 최신 공고의 유효성을 뜻하지 않는다.

- [과거 상세 명세](implementation-spec.md)
- [원본 README와 코드](https://github.com/yurimakes/youth-policy-llm-recommender/tree/v0.1-mvp)
- 기존 실행: `.\.venv\Scripts\python.exe -m streamlit run app.py`

`app.py`, 기존 데이터 파이프라인과 테스트는 유지한다. 최신 개발 방향은 루트 `PROJECT_SPEC.md`를 기준으로 한다.
