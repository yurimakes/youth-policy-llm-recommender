# 지원장바구니: 청년정책 AI 에이전트

**정책을 찾아보지 않던 청년이 적은 카드 선택으로 시작하고, 필요한 지원과 준비·상담 행동을 이어가는 서비스**

목표가 뚜렷하지 않아도 일상적인 상황·관심 카드로 시작합니다. 관심 정책을 고르면 사용자가 선택한 상세 질문에서 필요한 조건과 선호를 보완하고, 정책 후보와 다음 행동을 갱신하는 흐름을 개발합니다.

현재 저장소는 **기존 MVP에서 새 서비스로 고도화하는 단계**입니다. 새 React 웹서비스가 구현·배포 완료된 상태가 아닙니다. 최종 신청 자격은 공식 공고와 담당 기관에서 확인합니다.

## 원본 MVP와 현재 개발 기준

- 원본 버전: [`v0.1-mvp`](https://github.com/yurimakes/youth-policy-llm-recommender/tree/v0.1-mvp), 커밋 `23f33e7`
- 1차 고도화: [PR #2](https://github.com/yurimakes/youth-policy-llm-recommender/pull/2) main 병합 완료
- 현재 API·데모 UI 브랜치: `feature/intake-api`
- 최신 기획: [2026-10-07 팀 공유본](docs/planning/service-redesign-2026-10.md)
- 개발 계약: [PROJECT_SPEC.md](PROJECT_SPEC.md)
- 구현·검증 상태: [PROJECT_STATUS.md](PROJECT_STATUS.md)
- 과거 구현 기록: [MVP 개요](docs/mvp/overview.md)

## 고도화 방향

| 구간 | 원본 MVP | 지원장바구니 방향 |
|---|---|---|
| 시작 | 나이·지역·취업 상태와 관심사 입력 | 상황 또는 목표 카드, 모름·건너뛰기 |
| 조건 확인 | MATCH / UNKNOWN / NO_MATCH | 정책 불확실성과 사용자 정보 부족 구분 |
| 진행 | 입력 후 결과 표시 | 선택적 상세 질문, 답변 이어받기·수정·중단·복귀 |
| 결과 | 검색·추천 설명 | 정책·다음 행동 갱신, 준비·상담 지원 |
| 화면·서버 | Streamlit·SQLite | FastAPI·로컬 서버/DB 확인, 같은 서버의 3개 데모 화면 추가, PostgreSQL 후속 |
| 검색·AI | OpenAI 임베딩·FAISS·설명 | 하이브리드 검색·RAG·상태 기반 도구 연결 검증 예정 |

‘쉬고 있어요’만으로 미취업·소득·경제난을 추정하지 않습니다. 서울·19~34세는 초기 대상 범위이며 실제 입력값을 대신하지 않습니다. 상세 정보 제공을 원치 않아도 남은 확인사항과 공식 경로를 안내합니다.

## 이번 브랜치의 첫 코드 구현

- 상황/목표 카드 진입, 모름·건너뛰기, 직접 확인한 사실과 선호 분리
- 사용자 선택에 따른 상세 확인, 중단·복귀·답변 수정
- 후보에 필요한 기초/상세 질문 선택과 중복 질문 방지
- 조건별 네 가지 표시 상태, 신청 기간의 요청 날짜 재평가
- 명확한 불일치 제외, 공식 링크·확인 시각과 다음 확인 행동 유지

1차 병합의 결과는 **Python 핵심 로직과 개발용 CLI**입니다. 이번 후속 브랜치에는 FastAPI와 시작·질문·결과의 **3개 데모 화면**을 추가했습니다. 선택적 상세 확인은 질문 화면을 재사용합니다. 상황/관심 카드에 따른 정책 순위와 선호 반영, AI 질문·설명·문서 생성, 실제 정책 목록 검증은 후속 작업입니다.

UI 추가 전 API 커밋 `1862bbe`는 사용자의 Windows Python 3.10 환경에서 **224 passed, 67 subtests passed, 경고 1개**를 확인했습니다. 실제 서버 점검은 상세 중단·복귀를 포함해 **6개 모두 통과, 실패·스킵·점검 경고 0개**입니다. UI 커밋 `f22e949`의 Windows 실행은 226 passed, 실패 하위 사례 2개, 경고 1개, 73 subtests passed였습니다. 실패는 두 JavaScript 모듈의 MIME 타입이 text/plain인 문제로, 서버가 타입을 직접 지정하도록 수정했습니다. 보완 후 개발 환경의 Python 관련 테스트는 성공 91개·HTTP 스킵 14개입니다. JavaScript 상태 관리 테스트 7개는 UI 구현 단계에서 통과했습니다. MIME 수정 후 Windows 전체 회귀·브라우저 배치는 확인 전입니다. 단계별 검증 기록은 PROJECT_STATUS에 있습니다.

## 제출용 데모 UI와 백엔드 API

팀원의 화면 작업이 시작 전인 상황에서 사용자가 담당 범위를 변경해, 이 브랜치에 제출용 UI를 추가했습니다. HTML/CSS/JavaScript 화면과 API를 같은 FastAPI 서버에서 제공하며 npm 설치나 별도 빌드가 필요하지 않습니다. 정적 파일은 필요한 세 파일만 허용하며 CSS와 JavaScript MIME 타입을 직접 지정해 OS별 차이를 피합니다. React/TypeScript는 이후 프론트엔드 방향으로 유지합니다. 사용자 진행 상태는 POST 본문으로 이어받고 서버에 영구 저장하지 않습니다.

- [UI 연결 규격과 실행 방법](docs/api/intake-v1.md)
- [시작 요청 JSON Schema](docs/api/schemas/start-request.json)
- [전환 요청 JSON Schema](docs/api/schemas/transition-request.json)
- [응답 JSON Schema](docs/api/schemas/intake-response.json)

API 계약·스키마와 실제 FastAPI TestClient 테스트가 Windows 전체 회귀에서 통과했습니다. **Uvicorn 서버와 로컬 DB 20건 조회, 기본 후보 5건, 상세 거절·중단·복귀를 확인했습니다.** 새 데모의 브라우저 연결·배치와 공식 공고의 최신성은 확인 전입니다. 기존 데이터 DB가 없으면 정책 후보 조회에는 별도 데이터 준비가 필요합니다.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-api.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

서버 실행 후 [http://127.0.0.1:8000/demo](http://127.0.0.1:8000/demo)를 엽니다. 이미 실행 중인 서버는 Ctrl+C로 종료하고 다시 실행해야 새 화면 경로가 반영됩니다. 데모는 같은 origin의 API에 연결하므로 CORS 추가 설정이 필요하지 않습니다. 별도 프론트엔드 개발 서버를 사용할 때는 origin을 명시합니다. 새 UI·AI·문서·저장 기능 전체가 완성된 것으로 표시하지 않습니다.

서버를 실행한 상태에서 **다른 PowerShell 창**으로 질문·결과·상세 전환을 점검합니다. 이 명령은 실제 사용자 답변 대신 합성 입력을 사용하며, 로컬 서버에만 연결하고 상태·원문 응답을 파일에 저장하지 않습니다.

```powershell
.\.venv\Scripts\python.exe scripts/check_intake_api.py
```

`PASS` / `FAIL` / `SKIP` / `WARN`과 집계를 출력합니다. 상세 중단·복귀는 별도의 새 합성 진행에서 모든 후보를 차례로 확인해 유용한 질문이 있는 정책으로 점검합니다. 기본 경로의 건너뛰기 이력은 수정하지 않습니다. 데이터가 없으면 실패하며, 후보 또는 유용한 상세 질문이 없으면 해당 검증은 스킵됩니다. 상세 검증까지 필수로 확인하려면 `--require-detail`을 사용합니다. 공식 공고의 최신성·브라우저 화면 동작은 별도로 확인합니다.

### 화면 확인 순서

1. 상황 또는 목표를 선택하고, 카드의 선택 표시를 확인한 뒤 ‘다음’을 누릅니다.
2. 필요한 질문에 답하거나 모름·건너뛰기를 선택해 결과로 이동합니다.
3. 결과에서 답변을 수정하고 정책을 선택합니다. 남은 유용한 질문이 있으면 상세 확인을 선택·거절·중단·복귀할 수 있습니다.
4. 개별 조건과 공식 링크, 다음 확인할 항목을 확인합니다. 마지막 항목 안내는 준비 문서 생성 기능이 아닙니다.

진행은 메모리에만 유지되며 새로고침하면 초기화됩니다. API 요청 실패 시 이전 답변을 유지하고 중복 요청을 막습니다. 새 데모는 외부 AI를 호출하지 않습니다.

JavaScript 상태 관리 테스트는 Node가 있는 개발 환경에서 `node --test tests/test_demo_client.mjs`로 실행합니다. Node는 화면 실행에 필요하지 않습니다.

## 기존 구현에서 재사용하는 기능

온통청년 API 페이지 수집·raw snapshot 보존·정규화·SQLite upsert, 삼중 규칙 평가, OpenAI 임베딩·FAISS Top-5 검색, 검색된 공식 정보 기반 설명과 AI 실패 폴백을 보존합니다. 원본 Streamlit 진입점은 `app.py`입니다.

과거 2026-07-02 기록에는 자동 테스트 122개와 실제 API 20건 검증이 있습니다. 이는 해당 시점의 기록입니다. 새 에이전트 품질이나 최신 정책 전체에 대한 검증 결과가 아닙니다.

## 코드와 문서

| 경로 | 역할 |
|---|---|
| `app.py` | 기존 Streamlit MVP |
| `demo/` | 시작·질문·결과의 제출용 HTML/CSS/JavaScript 화면 |
| `api.py` | 데모와 API를 함께 제공하는 FastAPI 진입점 |
| `src/youth_policy/` | 기존 데이터·규칙·검색·설명 모듈, 후속 진행 로직 |
| `scripts/` | 기존 온통청년 수집·적재 CLI, 신규 `preview_intake.py` 흐름 점검 |
| `tests/` | 기존 회귀 테스트와 신규 기능 테스트 |
| `docs/planning/` | 최신 팀 공유 기획 |
| `docs/decisions/` | 기획 전환과 구현 결정 |
| `docs/mvp/` | 과거 MVP 명세·보존 설명 |
| `assets/brand/logo-preview.html` | 서비스 로고 미리보기; 데모 헤더에도 같은 심볼 사용 |

## 기존 MVP 로컬 실행

아래 안내는 Windows PowerShell에서 저장소 루트를 기준으로 합니다. 원본 정책 데이터와 DB는 저장소에 포함되지 않으므로 앱 실행 전에 데이터를 준비해야 합니다.

### 1. 저장소와 가상환경 준비

```powershell
git clone https://github.com/yurimakes/youth-policy-llm-recommender.git
cd youth-policy-llm-recommender
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Python 버전·운영체제에 따라 고정된 의존성의 설치 가능 여부를 확인해야 합니다.

### 2. API 설정

온통청년 API 인증키와 OpenAI API 키를 준비합니다. 저장소 루트에 `.streamlit/secrets.toml`을 만들고 아래 항목을 설정합니다.

```toml
ONTONG_API_KEY = ""
OPENAI_API_KEY = ""
OPENAI_CHAT_MODEL = ""
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
```

키와 채팅 모델명은 사용 가능한 값으로 입력합니다. 빈 채팅 모델 설정은 앱의 기본값을 사용합니다. 환경 변수도 지원하며, 수집 CLI와 앱 모두 환경 변수를 먼저 읽고, 값이 없으면 Streamlit secrets를 읽습니다. `.env` 파일을 자동으로 불러오는 기능은 없습니다.

### 3. 정책 수집과 SQLite 적재

수집 CLI는 페이지별 원본을 보존하고 정규화된 정책을 DB에 함께 적재합니다.

```powershell
.\.venv\Scripts\python.exe scripts/collect_ontong_pages.py `
  --db data/processed/policies.sqlite3 `
  --page-size 10 `
  --max-pages 2
```

이 설정은 최대 2페이지를 수집합니다. 과거 실제 API 검증에서는 20건이 적재되었으며, 현재 반환 건수와 내용은 API 응답에 따라 달라질 수 있습니다. CLI 출력의 `fetched_policies`와 `stored_policies`로 수집·저장 건수를 확인합니다.

이미 보존한 snapshot이 있다면 `scripts/load_ontong_snapshot.py`의 `--input`, `--db` 옵션으로 재적재할 수 있습니다.

### 4. 웹서비스 실행

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

나이, 시·도와 시·군·구, 취업 상태를 입력하고 필요하면 관심사를 작성한 뒤 `맞춤 정책 추천받기`를 누릅니다. 예: `자격증 시험 비용과 월세 지원이 필요해요.` 지역 선택지는 현재 적재된 정책의 지역 정보에서 구성됩니다.


## 새 진행 로직 로컬 점검

기존 정책 DB가 있으면 다음 명령으로 간편→선택적 상세→조건 갱신 흐름을 터미널에서 확인할 수 있습니다. DB를 읽기 전용으로 열고 사용자 답변을 저장하거나 외부 AI를 호출하지 않습니다. 웹서비스 실행 명령과는 별개입니다.

```powershell
.\.venv\Scripts\python.exe scripts/preview_intake.py --db data/processed/policies.sqlite3
.\.venv\Scripts\python.exe scripts/preview_intake.py --start goal --db data/processed/policies.sqlite3
```

UI 없이 실행할 신규 테스트:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_intake*.py" -v
```

CLI는 개발용이므로 지역을 5자리 코드로 입력하고, 카드에 따른 관심도 순위 없이 조건 후보를 표시합니다. 정책 DB가 없거나 안내할 후보가 없으면 이를 알립니다. 입력 수정과 선호 저장은 핵심 모듈에서 제공하며 CLI 화면에는 연결하지 않았습니다. PostgreSQL 또는 영구 진행 상태 저장은 이 단계에 포함하지 않습니다.

## 검증과 다음 개발

기존 전체 검증 명령은 `.\.venv\Scripts\python.exe -m pytest -q` 및 `.\.venv\Scripts\python.exe -m compileall app.py src scripts`입니다. 현재 브랜치의 실제 실행 결과와 제한은 PROJECT_STATUS에 기록합니다.

초기 정책 20~30개 목록, 지원 플랫폼 API·모델, 개인정보 전달·저장·삭제, 호스팅은 확정 전입니다. 평가 사례 100건 이상과 근거 일치율 95% 이상은 목표이며 달성 성과가 아닙니다. 청년 20명 테스트는 최신 기획에서 보류로 표시돼 있습니다.

## 데이터와 이용 조건

주요 출처는 [온통청년](https://www.youthcenter.go.kr/) 청년정책 API입니다. 정책 ID·공식 URL·확인 시각을 보존합니다. `last_verified_at`은 적재·처리 시각이며 담당 기관이 모든 조건을 재확인했다는 뜻이 아닙니다. 공식 데이터의 이용·재배포 조건과 코드 라이선스는 별도로 확인해야 하며 현재 코드 라이선스는 지정되지 않았습니다.

API 키·raw 데이터·로컬 DB는 Git에서 제외합니다. 기존 MVP의 AI 검색·설명 이용 시 사용자 관심사·조건이 OpenAI API에 전달되고 비용이 발생합니다. 신규 사용자 진행 상태의 외부 AI 전달과 영구 저장 설계는 후속 결정사항입니다. 자동 신청·자동 연락은 구현 범위에 포함하지 않습니다.
