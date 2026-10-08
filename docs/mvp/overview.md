# 원본 Streamlit MVP

원본 코드는 [`v0.1-mvp`](https://github.com/yurimakes/youth-policy-llm-recommender/tree/v0.1-mvp) 태그에서 확인할 수 있다. 태그가 가리키는 커밋은 `23f33e7bc8e51d3e26812faeb479aae7f83ee596`이다.

Streamlit·SQLite 기반으로 나이·지역·취업 상태 입력, 조건 평가, OpenAI 임베딩·FAISS 검색, 공식 정보 기반 설명과 AI 실패 폴백을 제공한다. 현재 저장소에서도 진입점은 `app.py`다.

```powershell
.\\.venv\\Scripts\\python.exe -m streamlit run app.py
```

실행 전 정책 데이터와 API 키를 준비한다. [설정·실행 안내](../getting-started/README.md#기존-streamlit-mvp-실행)에서 확인할 수 있다. 기존 MVP의 검색·설명은 OpenAI API를 호출하며, 공개 정적 데모와 Intake API의 동작은 [구조와 데이터 흐름](../architecture.md)에서 구분한다.
