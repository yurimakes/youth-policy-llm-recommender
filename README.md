# 지원장바구니: 청년정책 AI 에이전트

**정책을 찾아보지 않던 청년이 적은 카드 선택으로 시작하고, 필요한 지원과 준비·상담 행동을 이어가는 서비스**

목표가 뚜렷하지 않아도 일상적인 상황·관심 카드로 시작합니다. 관심 정책을 고르면 사용자가 선택한 상세 질문에서 필요한 조건과 선호를 보완하고, 정책 후보와 다음 행동을 갱신하는 흐름을 개발합니다.

현재 저장소는 **기존 MVP에서 새 서비스로 고도화하는 단계**입니다. 새 React 웹서비스가 구현·배포 완료된 상태가 아닙니다. 최종 신청 자격은 공식 공고와 담당 기관에서 확인합니다.

## 원본 MVP와 현재 개발 기준

- 원본 버전: [`v0.1-mvp`](https://github.com/yurimakes/youth-policy-llm-recommender/tree/v0.1-mvp), 커밋 `23f33e7`
- 고도화 브랜치: `docs/service-redesign`
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
| 화면·서버 | Streamlit·SQLite | React·TypeScript·FastAPI·PostgreSQL 개발 예정 |
| 검색·AI | OpenAI 임베딩·FAISS·설명 | 하이브리드 검색·RAG·상태 기반 도구 연결 검증 예정 |

‘쉬고 있어요’만으로 미취업·소득·경제난을 추정하지 않습니다. 서울·19~34세는 초기 대상 범위이며 실제 입력값을 대신하지 않습니다. 상세 정보 제공을 원치 않아도 남은 확인사항과 공식 경로를 안내합니다.

## 이번 브랜치의 첫 코드 구현

- 상황/목표 카드 진입, 모름·건너뛰기, 직접 확인한 사실과 선호 분리
- 사용자 선택에 따른 상세 확인, 중단·복귀·답변 수정
- 후보에 필요한 기초/상세 질문 선택과 중복 질문 방지
- 조건별 네 가지 표시 상태, 신청 기간의 요청 날짜 재평가
- 명확한 불일치 제외, 공식 링크·확인 시각과 다음 확인 행동 유지

이 단계는 **웹/API에 연결하기 위한 Python 핵심 로직과 개발용 CLI**입니다. 카드 화면이 구현된 상태는 아닙니다. 상황/관심 카드에 따른 정책 순위와 선호 반영, AI 질문·설명·문서 생성, 실제 정책 목록 검증은 후속 작업입니다.

신규 로직 테스트 49개와 구문 검증이 통과했고, 2026-10-07 사용자의 Windows Python 3.10 환경에서 전체 pytest **171 passed, 23 subtests passed**를 확인했습니다. 상세 검증 기록은 PROJECT_STATUS에 있습니다.

## 기존 구현에서 재사용하는 기능

온통청년 API 페이지 수집·raw snapshot 보존·정규화·SQLite upsert, 삼중 규칙 평가, OpenAI 임베딩·FAISS Top-5 검색, 검색된 공식 정보 기반 설명과 AI 실패 폴백을 보존합니다. 원본 Streamlit 진입점은 `app.py`입니다.

과거 2026-07-02 기록에는 자동 테스트 122개와 실제 API 20건 검증이 있습니다. 이는 해당 시점의 기록입니다. 새 에이전트 품질이나 최신 정책 전체에 대한 검증 결과가 아닙니다.

## 코드와 문서

| 경로 | 역할 |
|---|---|
| `app.py` | 기존 Streamlit MVP |
| `src/youth_policy/` | 기존 데이터·규칙·검색·설명 모듈, 후속 진행 로직 |
| `scripts/` | 기존 온통청년 수집·적재 CLI, 신규 `preview_intake.py` 흐름 점검 |
| `tests/` | 기존 회귀 테스트와 신규 기능 테스트 |
| `docs/planning/` | 최신 팀 공유 기획 |
| `docs/decisions/` | 기획 전환과 구현 결정 |
| `docs/mvp/` | 과거 MVP 명세·보존 설명 |
| `assets/brand/logo-preview.html` | 첨부 로고 미리보기, 앱 연동 전 |

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
