# 구조와 데이터 흐름

## 화면과 실행 모드

동일한 HTML/CSS/JavaScript 화면을 두 가지 방식으로 실행한다.

| 실행 모드 | 데이터 | 처리 |
|---|---|---|
| 공개 정적 데모 | `demo/mock.mjs`의 가상 정책·조건 | 브라우저에서 가상 응답 구성 |
| 로컬 FastAPI `/demo` | 로컬 SQLite의 정책 레코드 | 서버에서 상태 전환·정책 조건 재평가 |

`scripts/build_demo.py`는 `demo/index.html`의 실행 모드를 `mock`으로 바꿔 정적 파일을 생성한다. 로컬 API는 원본 HTML의 `api` 모드를 사용한다. `demo/client.mjs`는 모드에 따라 가상 응답 또는 HTTP API를 호출하고, `demo/app.mjs`는 질문·결과·장바구니·준비·상담 화면을 표시한다.

공식 제도 참고자료는 `demo/official-policies.json`에 별도로 보관한다. 이 자료는 가상 후보의 조건 근거가 아니다.

## Intake API

1. 시작 요청은 초기 진행 상태와 질문을 반환한다.
2. 화면은 응답의 `state`와 한 개의 `action`을 전환 요청에 전달한다.
3. 서버는 입력 형식·상태 이력·허용된 전환을 검증하고 필요한 정책 데이터를 읽는다.
4. 서버 DB와 한국 날짜(UTC+9)를 기준으로 조건을 평가해 상태·질문·후보·확인사항을 반환한다.

| 모듈 | 역할 |
|---|---|
| `api_app.py`, `api_config.py` | HTTP 경로, 설정, 정적 파일 제공 |
| `api_schemas.py`, `intake_contract.py` | 요청·응답 스키마와 상태·행동 검증 |
| `intake.py`, `intake_service.py` | 진행 단계와 정책 재평가 |
| `conditions.py`, `matching.py` | 정책 조건 비교 |
| `policy_repository.py`, `sqlite_store.py` | 정책 데이터 읽기와 SQLite 저장 |

위 모듈은 `src/youth_policy/`에 있다. 사용자 사실과 선호를 구분하며 상황 카드에서 취업 상태·소득 등을 추정하지 않는다. 후보의 상태는 조건 비교 결과이며 최종 신청 자격이나 개인별 최적 추천 순위를 뜻하지 않는다. 자세한 필드와 오류는 [API 규격](api/intake-v1.md)에서 확인한다.

## 상태와 문서

API는 사용자 진행 상태를 서버에 저장하지 않는다. 화면은 상태·장바구니·준비 체크를 메모리에서 유지하며 새로고침하면 초기화된다. 요청은 순서대로 실행하고 오류 시 기존 상태를 유지한다. 문서 초안은 입력과 확인사항을 조합한다. PDF 저장은 브라우저 인쇄 기능을 사용한다.

Intake API와 데모는 외부 LLM 호출, 영구 답변 저장, 자동 신청·연락을 수행하지 않는다. CORS는 브라우저 origin 허용 설정이며 사용자 인증 기능이 아니다.

## 기존 Streamlit 경로

`app.py`는 정책 수집·정규화·SQLite 적재 모듈과 조건 평가를 사용한다. `retrieval.py`의 OpenAI 임베딩·FAISS 검색과 `llm_service.py`의 설명 생성은 외부 API를 호출한다. 이 경로는 정적 데모 및 Intake API와 별개다. [원본 MVP 안내](mvp/overview.md), [실행 방법](getting-started/README.md#기존-streamlit-mvp-실행)을 참고한다.
