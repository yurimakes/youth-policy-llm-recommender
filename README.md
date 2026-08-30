# 청년 맞춤 정책 추천

청년의 기본 조건과 자연어 관심사를 바탕으로 공식 청년정책 데이터를 필터링하고, 관련 정책을 검색해 추천 이유와 확인사항을 제공하는 Streamlit 웹서비스입니다.

이 서비스는 정책 탐색을 돕는 보조 도구입니다. 최종 신청 자격과 세부 조건은 반드시 공식 공고문에서 확인해야 합니다.

## 주요 기능

- 온통청년 청년정책 API 실제 데이터 수집
- 정책 데이터를 `PolicyRecord` 공통 구조로 변환
- SQLite 저장 및 정책 ID 기준 중복 방지
- 나이, 시·도, 시·군·구, 취업 상태 입력
- `MATCH`, `UNKNOWN`, `NO_MATCH` 규칙 기반 평가
- 자연어 관심사 입력
- OpenAI 임베딩 + FAISS Top-5 검색
- 검색된 공식 정책 정보만 사용한 OpenAI 추천 설명
- 공식 출처와 최종 확인 안내 표시
- AI 설명 실패 시 규칙 기반 결과 유지

## 현재 검증 상태

- 실제 API 2페이지, 총 20건 수집
- SQLite 정책 20건 저장 및 재조회
- 동일 정책 재적재 시 중복 증가 없음
- 전체 자동 테스트: `122 passed`
- `compileall app.py src`: 성공
- Streamlit 로컬 실행: 성공
- 실제 FAISS Top-5 검색 및 OpenAI 설명 생성: 성공
- GitHub `main` 브랜치 반영 완료

## 처리 흐름

```text
온통청년 공식 API
        ↓
raw snapshot 저장
        ↓
PolicyRecord 변환
        ↓
SQLite 적재 및 조회
        ↓
사용자 조건 규칙 평가
        ↓
MATCH + UNKNOWN 후보
        ↓
OpenAI 임베딩
        ↓
FAISS Top-5 검색
        ↓
공식 정책 기반 OpenAI 설명
        ↓
Streamlit 결과 화면
```

## 기술 스택

| 영역 | 기술 |
|---|---|
| 언어 | Python 3.10 |
| 웹 UI | Streamlit |
| 데이터 수집 | Requests |
| 데이터 처리 | Pandas |
| 구조화 저장소 | SQLite |
| 벡터 검색 | FAISS |
| 임베딩 및 설명 | OpenAI API |
| 테스트 | pytest |
| 버전 관리 | Git, GitHub |

## 주요 파일

```text
app.py
src/career_catch/
├── codebook.py
├── config.py
├── llm_service.py
├── matching.py
├── models.py
├── ontong_client.py
├── ontong_parser.py
├── pipeline.py
├── retrieval.py
├── sqlite_store.py
└── ui_service.py

tests/
├── test_llm_service.py
├── test_retrieval.py
├── test_ui_service.py
└── ...
```

## 로컬 설정

저장소 루트에 `.streamlit/secrets.toml`을 만들고 실제 키를 입력합니다.

```toml
ONTONG_API_KEY = ""
OPENAI_API_KEY = ""
OPENAI_CHAT_MODEL = ""
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
```

주의:

- 실제 키를 Git에 커밋하지 않습니다.
- `.streamlit/secrets.toml`은 `.gitignore` 대상입니다.
- raw 데이터와 SQLite 파일도 Git에 포함하지 않습니다.

## 실행

현재 로컬 실행은 정책 SQLite 데이터가 준비되어 있다는 전제에서 검증했습니다.

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

브라우저에서 나이, 지역, 취업 상태, 관심 정책을 입력한 뒤 `맞춤 정책 추천받기` 버튼을 누릅니다.

## 테스트

전체 테스트:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

현재 검증 결과:

```text
122 passed
```

구문 검증:

```powershell
.\.venv\Scripts\python.exe -m compileall app.py src
```

## 추천 안전 원칙

- 명확한 불일치만 `NO_MATCH`로 제외합니다.
- 정보가 부족하면 `UNKNOWN`으로 유지합니다.
- LLM은 FAISS로 검색된 공식 정책만 설명합니다.
- 정책 데이터에 없는 금액, 날짜, 자격, 서류를 생성하지 않습니다.
- 최종 신청 자격을 확정하지 않습니다.
- 공식 출처 확인을 안내합니다.

## 데이터 및 비밀정보 관리

다음 파일은 Git에 포함하지 않습니다.

- 실제 API 키가 있는 설정 파일
- `data/raw` 원본 snapshot
- `data/processed` 생성 데이터
- 로컬 SQLite 데이터베이스
- FAISS 생성 산출물

새 환경에서는 공식 API를 이용해 데이터 수집·적재 파이프라인을 다시 실행해야 합니다.

## 현재 한계

- 현재 실제 데이터 검증 범위는 20건입니다.
- 소득 조건의 단위와 개인·가구 기준은 완전 구조화되지 않았습니다.
- 복잡한 자유 텍스트 자격 조건은 자동으로 확정하지 않습니다.
- OpenAI API 사용 시 비용이 발생합니다.
- Streamlit Community Cloud 배포는 아직 완료되지 않았습니다.

## 남은 작업

- 최종 실행 화면 캡처 정리
- 결과보고서 작성
- 필요 시 Streamlit Community Cloud 배포

## 저장소

```text
https://github.com/yurimakes/youth-policy-llm-recommender
```
