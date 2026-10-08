# 지원장바구니: 청년정책 AI 에이전트

**상황 카드에서 필요한 질문, 지원 후보와 조건 확인, 준비·상담 행동까지 이어가는 서비스**

[제출용 공개 데모](https://youth-support-demo-20261008.cyr3918.chatgpt.site) · [시연·실행 안내](docs/submission/2026-10-08-demo.md) · [10월 8일 계획표](docs/planning/submission-mvp-2026-10-08.md)

공개 데모는 로그인 없이 열리는 **가상 정책·조건 체험**입니다. 실제 정책 DB를 읽는 FastAPI는 로컬 `/demo`에서 같은 화면을 사용합니다. 공개 주소에 Python API나 실제 자격 판정 서비스를 배포한 것은 아닙니다. 최종 자격과 현재 모집 여부는 공식 공고·기관에서 확인합니다.

## 현재 구현

사용자가 확정한 화면 보드에 맞춰 상황·관심·기초 질문·지원 방향·상세 제안·상세 질문·갱신 결과·장바구니 준비·상담 요약을 연결했습니다. 흰 바탕, 파란 강조색, 회색 보조 정보와 세로 선택 카드를 사용합니다. HTML/CSS/JavaScript 구현이며 React/TypeScript는 후속 방향입니다.

- 모름·건너뛰기, 답변 수정, 상세 거절·중단·복귀, 오류 후 재시도
- 조건별 확인됨 / 미충족 / 확인 필요 / 입력 부족과 명확한 미충족 후보 제외
- 메모리 장바구니, 준비 체크 3개, 상담 요약·체크리스트·발급 안내·문의 초안
- 문서 복사와 브라우저 인쇄를 통한 PDF 저장. 외부 AI·자동 제출·예약·연락 없음
- 실제 제도 6개의 별도 공식 참고자료: ID·URL·확인일·모집 종료 또는 기관 확인 필요 표시

‘쉬고 있어요’에서 미취업·소득·경제난을 추정하지 않습니다. 선호는 자격에 사용하지 않습니다. 공개 가상 정책의 조건과 공식 참고자료를 연결하지 않으며, 실제 정책 목록 전체의 조건 정규화는 후속 작업입니다. 입력·장바구니·완료 체크는 새로고침하면 초기화됩니다.

## 개발 기준과 검증

- 원본: [`v0.1-mvp`](https://github.com/yurimakes/youth-policy-llm-recommender/tree/v0.1-mvp), `23f33e7` 보존
- 1차 고도화: [PR #2](https://github.com/yurimakes/youth-policy-llm-recommender/pull/2) main 병합 완료
- API·공개 데모 작업세트: [PR #3](https://github.com/yurimakes/youth-policy-llm-recommender/pull/3) main 병합 완료 (`2e120f3`)
- 검증·제출 코드 기준: `97cd09a`, 공개 체험 버전 3
- 기획: [팀 공유본](docs/planning/service-redesign-2026-10.md), [확정 UI·배포 결정](docs/decisions/2026-10-approved-ui-and-public-demo.md)
- 계약·진행: [PROJECT_SPEC](PROJECT_SPEC.md), [PROJECT_STATUS](PROJECT_STATUS.md), [TASKS](TASKS.md)

검증한 `97cd09a`는 Windows Python 3.10의 전체 pytest **230 passed, 82 subtests passed, 기존 경고 1개**입니다. JavaScript 15개, Chromium 브라우저 시연 6개, compileall과 정적 빌드도 통과했습니다. 실제 FastAPI와 격리된 합성 정책을 이용한 UI 연결, 모름·건너뛰기·상세·수정·오류 복구, 상담 복사·PDF 출력과 모바일 가로 넘침을 확인했습니다.

[검증 실행](https://github.com/yurimakes/youth-policy-llm-recommender/actions/runs/37707391655) · [화면 PNG 6개·상담 PDF](https://github.com/yurimakes/youth-policy-llm-recommender/actions/runs/37707391655/artifacts/11520561167) (캡처 보관: 2026-10-15까지)

기존 사용자 DB 20건의 실제 서버 확인은 `1862bbe`의 이전 실행 기록이며 현재 브라우저의 합성 정책 검증과 구분합니다. 공개 체험은 배포 성공과 검증 코드 일치를 확인했으며 운영 데이터 전체의 최신성·실사용 효과 검증은 후속입니다. 자세한 단계별 기록은 PROJECT_STATUS에 있습니다.

## 로컬 데모와 API

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-api.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

서버를 재시작한 후 http://127.0.0.1:8000/demo 를 엽니다. 실제 정책 SQLite가 없으면 후보 요청에서 데이터 오류를 안내합니다. 별도 PowerShell 창에서 다음 명령으로 실제 서버·DB와 상세 흐름을 확인합니다.

```powershell
.\.venv\Scripts\python.exe scripts/check_intake_api.py --require-detail
```

공개 체험과 같은 목데이터 모드는 설치 없이 배포 링크에서 열거나 다음처럼 로컬에서 실행합니다.

```powershell
.\.venv\Scripts\python.exe scripts/build_submission_demo.py --output submission-demo
.\.venv\Scripts\python.exe scripts/serve_submission_demo.py --directory submission-demo --port 8080
```

http://127.0.0.1:8080 을 엽니다. Node는 화면 실행에는 필요하지 않으며 개발 테스트에는 `node --test tests/test_demo_client.mjs tests/test_submission_demo.mjs`를 사용합니다.

[API v1 규격](docs/api/intake-v1.md)과 [JSON Schema](docs/api/schemas/intake-response.json)를 유지합니다. 서버는 후보·조건·날짜를 클라이언트에서 받지 않고 SQLite와 한국 날짜로 평가합니다. 새로운 가구·참여 시간 질문은 가상 체험에만 있으며 실제 API 계약은 변경하지 않았습니다.

## 기존 구현에서 재사용하는 기능

온통청년 API 페이지 수집·raw snapshot 보존·정규화·SQLite upsert, 삼중 규칙 평가, OpenAI 임베딩·FAISS Top-5 검색, 검색된 공식 정보 기반 설명과 AI 실패 폴백을 보존합니다. 원본 Streamlit 진입점은 `app.py`입니다.

과거 2026-07-02 기록에는 자동 테스트 122개와 실제 API 20건 검증이 있습니다. 이는 해당 시점의 기록입니다. 새 에이전트 품질이나 최신 정책 전체에 대한 검증 결과가 아닙니다.

## 코드와 문서

| 경로 | 역할 |
|---|---|
| `app.py` | 기존 Streamlit MVP |
| `demo/` | 확정 UI, 로컬 실제 API 모드와 공개 가상 체험 모드 |
| `api.py` | 데모와 API를 함께 제공하는 FastAPI 진입점 |
| `src/youth_policy/` | 기존 데이터·규칙·검색·설명 모듈, 후속 진행 로직 |
| `scripts/` | 기존 온통청년 수집·적재 CLI, 신규 `preview_intake.py` 흐름 점검 |
| `tests/` | 기존 회귀 테스트와 신규 기능 테스트 |
| `docs/planning/` | 최신 팀 공유 기획 |
| `docs/decisions/` | 기획 전환과 구현 결정 |
| `docs/mvp/` | 과거 MVP 명세·보존 설명 |
| `assets/brand/logo-preview.html` | 서비스 로고 미리보기 |

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
