# 개발자 실행 안내

[서비스 소개로 돌아가기](../../README.md) · [데모 사용 안내](../demo/README.md) · [API 규격](../api/intake-v1.md)

모든 명령어는 Windows PowerShell에서 저장소 루트를 기준으로 실행합니다.

| 실행 방식 | 필요한 준비 |
|---|---|
| 가상 데모 | Python 환경. DB·API 키 불필요 |
| 실제 정책 데모·API | Python 의존성과 정책 SQLite. API 자체는 OpenAI를 호출하지 않음 |
| 기존 Streamlit MVP | Python 의존성·정책 SQLite·온통청년 수집 키·OpenAI 키 |

## 로컬 환경 준비

Windows PowerShell에서 저장소를 내려받고 가상환경을 만듭니다.

```powershell
git clone https://github.com/yurimakes/youth-policy-llm-recommender.git
cd youth-policy-llm-recommender
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-api.txt
```

Python 버전과 운영체제에 따라 고정 의존성의 설치 가능 여부를 확인합니다.

## 가상 데모 실행

공개 데모와 같은 가상 데이터 모드는 DB나 API 키 없이 실행할 수 있습니다.

```powershell
.\.venv\Scripts\python.exe scripts/build_demo.py --output demo-build
.\.venv\Scripts\python.exe scripts/serve_demo.py --directory demo-build --port 8080
```

[로컬 가상 데모](http://127.0.0.1:8080)를 엽니다. Node는 화면 실행에 필요하지 않습니다.

## 실제 정책 데이터 준비

실제 API나 기존 MVP를 실행할 때 준비합니다. 기존 SQLite가 있으면 수집을 생략할 수 있습니다. 새 데이터를 수집하려면 온통청년 인증키가 필요하며, OpenAI 키는 기존 MVP의 AI 검색·설명에 사용합니다.

### API 설정

저장소 루트에 `.streamlit/secrets.toml`을 만들고 온통청년 API 인증키와 OpenAI API 키를 설정합니다.

```toml
ONTONG_API_KEY = ""
OPENAI_API_KEY = ""
OPENAI_CHAT_MODEL = ""
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
```

키와 모델명에 사용 가능한 값을 입력합니다. 빈 채팅 모델 설정은 앱의 기본값을 사용합니다. 환경 변수를 먼저 읽고 값이 없으면 Streamlit secrets를 읽습니다. `.env` 파일을 자동으로 불러오지는 않습니다.

### 정책 수집과 SQLite 적재

원본 정책 데이터와 DB는 저장소에 포함되지 않습니다. 수집 CLI는 페이지별 원본을 보존하고 정규화한 정책을 적재합니다.

```powershell
.\.venv\Scripts\python.exe scripts/collect_ontong_pages.py --db data/processed/policies.sqlite3 --page-size 10 --max-pages 2
```

위 설정은 최대 2페이지를 수집합니다. 수집 건수와 내용은 공식 API 응답에 따라 달라지며 CLI의 `fetched_policies`와 `stored_policies`에서 확인합니다. 보존한 snapshot은 `scripts/load_ontong_snapshot.py`의 `--input`, `--db` 옵션으로 재적재할 수 있습니다.

## 로컬 데모와 API

실제 정책 데이터가 준비된 저장소 루트에서 실행합니다.

```powershell
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

[로컬 데모](http://127.0.0.1:8000/demo)를 엽니다. SQLite 데이터가 없으면 후보 요청에서 데이터 오류를 안내합니다. API는 후보·판정·기준일을 클라이언트에서 받지 않고 서버 DB와 한국 날짜로 조건을 평가합니다. 나이·지역·취업 상태와 선호를 받으며, 가상 체험 전용 가구 질문은 실제 API 계약에 포함되지 않습니다.

서버를 실행한 채 별도 PowerShell 창에서 점검합니다.

```powershell
.\.venv\Scripts\python.exe scripts/check_intake_api.py --require-detail
```

실행 중인 서버는 Ctrl+C로 종료할 수 있습니다. 코드를 갱신한 뒤 다시 실행합니다. [API 규격](../api/intake-v1.md)과 [JSON Schema](../api/schemas/intake-response.json)에서 요청·응답과 오류를 확인할 수 있습니다.

## 기존 Streamlit MVP 실행

기존 MVP는 온통청년 API 수집·정규화·SQLite 적재, 조건 평가, OpenAI 임베딩·FAISS 검색, 공식 정보 기반 설명과 AI 실패 폴백을 제공합니다. 진입점은 `app.py`이며 원본 코드는 [`v0.1-mvp`](https://github.com/yurimakes/youth-policy-llm-recommender/tree/v0.1-mvp)에서 확인할 수 있습니다. [원본 MVP 안내](../mvp/overview.md)

### 앱 실행

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

나이·지역·취업 상태와 선택적인 관심사를 입력한 뒤 ‘맞춤 정책 추천받기’를 누릅니다. 지역 선택지는 적재된 정책 데이터에서 구성됩니다. 기존 MVP의 AI 검색·설명은 OpenAI API를 호출하며 사용자 관심사·조건이 전달되고 비용이 발생합니다.

## 테스트

[데이터·API 구현 검증](../validation/README.md)에서 API 키 없이 예제 정책을 SQLite·실제 API에 연결하고, 실제 로컬 DB의 품질과 원본 추적을 점검할 수 있습니다.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q api.py app.py src scripts tests
node --test tests/test_demo_client.mjs tests/test_mock_demo.mjs
```

[GitHub Actions의 Demo checks](https://github.com/yurimakes/youth-policy-llm-recommender/actions/workflows/demo-checks.yml)는 Windows Python 회귀, JavaScript 시나리오, 정적 빌드와 Chromium 브라우저 흐름을 검사합니다. 실행별 결과와 화면 PNG·상담 PDF는 해당 실행에서 확인합니다. 브라우저 검증은 합성 정책과 합성 입력을 사용하며 실제 공고의 최신성이나 최종 자격을 보증하지 않습니다. [브라우저 검증 방법](../demo/README.md#자동-브라우저-검증과-캡처)

