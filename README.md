# 지원장바구니: 청년정책 AI 에이전트

**상황 카드에서 필요한 질문, 지원 후보와 조건 확인, 준비·상담 행동까지 이어가는 서비스**

[공개 데모](https://jiwon-basket.vercel.app/) · [데모 실행 안내](docs/demo/README.md) · [구조와 데이터 흐름](docs/architecture.md) · [API 규격](docs/api/intake-v1.md) · [개발·검증 계획](docs/development-plan.md)

공개 데모는 로그인 없이 열리는 **가상 정책·조건 체험**입니다. 로컬 FastAPI는 실제 정책 SQLite를 읽어 같은 화면에 응답합니다. 공개 정적 데모에서는 Python API와 실제 정책 DB를 사용하지 않습니다. 최종 자격과 현재 모집 여부는 공식 공고·기관에서 확인합니다.

## 서비스 화면

[지원장바구니 데모 열기](https://jiwon-basket.vercel.app/)

<table>
  <tr>
    <th>1. 상황 카드로 시작</th>
    <th>2. 필요한 지원 살펴보기</th>
  </tr>
  <tr>
    <td valign="top"><img src="assets/screens/01-situation.png" width="260" alt="요즘 상황을 선택해 지원 탐색을 시작하는 화면"></td>
    <td valign="top"><img src="assets/screens/04-directions.png" width="260" alt="기초 답변을 바탕으로 가상 지원 후보를 살펴보고 담는 화면"></td>
  </tr>
  <tr>
    <th>3. 담은 지원의 신청 준비</th>
    <th>4. 상담 요약과 문서 저장</th>
  </tr>
  <tr>
    <td valign="top"><img src="assets/screens/08-preparation.png" width="260" alt="담은 지원의 기간과 서류, 남은 조건을 확인하는 준비 체크 화면"></td>
    <td valign="top"><img src="assets/screens/09-consultation.png" width="260" alt="입력 정보와 기관 문의사항을 정리하고 복사하거나 PDF로 저장하는 상담 요약 화면"></td>
  </tr>
</table>

실제 브라우저 캡처이며 정책·조건과 입력값은 **가상 체험 예시**입니다. [캡처 출처](assets/screens/README.md)

## 주요 기능

상황·관심 카드, 기초 질문, 지원 후보, 선택적 상세 확인, 장바구니 준비와 상담 요약을 연결합니다. 화면은 HTML/CSS/JavaScript로 구현했으며 Pretendard 글꼴을 함께 제공합니다. [글꼴 출처·라이선스](docs/demo/fonts.md)

- 모름·건너뛰기, 답변 수정, 상세 거절·중단·복귀, 오류 후 재시도
- 조건별 확인됨 / 미충족 / 확인 필요 / 입력 부족 표시와 명확한 미충족 후보 제외
- 메모리 장바구니, 준비 체크, 상담 요약·체크리스트·발급 안내·문의 초안
- 문서 복사와 브라우저 인쇄를 통한 PDF 저장
- 실제 제도 6개의 별도 공식 참고자료: ID·URL·확인일·기간 주의사항 표시

상황 카드에서 미취업·소득·경제난을 추정하지 않고, 선호를 자격 조건으로 사용하지 않습니다. 가상 정책의 조건과 공식 참고자료는 별개입니다. 입력·장바구니·완료 체크는 새로고침하면 초기화됩니다. 문서 초안은 입력과 확인사항을 조합하며 외부 AI 호출·자동 제출·예약·연락을 수행하지 않습니다.

## 사업기간 개발·검증 계획

현재는 **Foundation: 데모·규칙·로컬 API 기반 구현 단계**이며 G1~G5는 아직 통과하지 않았습니다. 아래는 2026년 10월~12월 11일의 **구현·검증 목표**입니다.

| 시기 | 데이터·서비스 범위 | 구현·검증 목표 |
|---|---|---|
| 10월 | 서울·경기 지역 정책과 전국 공통 정책 | 초기 정책 20~30개 적재·근거 추적, 기본 추천·상세 조건 확인, 규칙·진행 기준선 검증 |
| 11월 | 이용허락이 확보된 전국 지역 정책 순차 확대 | 지역별 조건 판정, 최소 질문 개인화, 근거 검색·준비·상담 문서 생성 검증 |
| 12월 1~11일 | 전국 거주 청년 대상 웹/PWA | 실제 정책 API 배포, 모바일·오류 복구·응답시간·비용·사용성 검증과 재평가 |

| Gate | 통과 기준 요약 |
|---|---|
| **G1 Data** | 정책 범위·필드 coverage 측정, 공식 출처·원본 추적 |
| **G2 Core QA** | 정답 사례 100건 이상, 명확한 제외 누락·미확인 조건 충족 단정 0건 |
| **G3 Question** | 같은 필수조건 확인 수준에서 질문 수 감소, 중복·추정·무동의 상세 진입 차단 |
| **G4 Evidence** | 키워드 기준선보다 검색 개선, 핵심 안내 근거 일치율 95% 이상, 근거 없는 금액·기간·서류 생성 0건 |
| **G5 Release** | 공개 API·timeout·fallback·웹/PWA·사용성 검증 통과, 비용·응답시간 예산과 릴리스 버전 고정 |

앞 Gate의 통과 증빙을 갖춰야 다음 Gate의 구현·검증을 시작합니다. 수치와 전국 확대는 목표이며 달성 실적이나 전국 모든 정책 확보를 뜻하지 않습니다. [상세 개발 범위·Gate·평가 방법·릴리스 기준](docs/development-plan.md)

## 로컬 환경 준비

Windows PowerShell에서 저장소를 내려받고 가상환경을 만듭니다.

```powershell
git clone https://github.com/yurimakes/youth-policy-llm-recommender.git
cd youth-policy-llm-recommender
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-api.txt
```

Python 버전과 운영체제에 따라 고정 의존성의 설치 가능 여부를 확인합니다.

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

실행 중인 서버는 Ctrl+C로 종료할 수 있습니다. 코드를 갱신한 뒤 다시 실행합니다. [API 규격](docs/api/intake-v1.md)과 [JSON Schema](docs/api/schemas/intake-response.json)에서 요청·응답과 오류를 확인할 수 있습니다.

공개 데모와 같은 가상 데이터 모드는 DB나 API 키 없이 실행할 수 있습니다.

```powershell
.\.venv\Scripts\python.exe scripts/build_demo.py --output demo-build
.\.venv\Scripts\python.exe scripts/serve_demo.py --directory demo-build --port 8080
```

[로컬 가상 데모](http://127.0.0.1:8080)를 엽니다. Node는 화면 실행에 필요하지 않습니다.

## 기존 Streamlit MVP 실행

기존 MVP는 온통청년 API 수집·정규화·SQLite 적재, 조건 평가, OpenAI 임베딩·FAISS 검색, 공식 정보 기반 설명과 AI 실패 폴백을 제공합니다. 진입점은 `app.py`이며 원본 코드는 [`v0.1-mvp`](https://github.com/yurimakes/youth-policy-llm-recommender/tree/v0.1-mvp)에서 확인할 수 있습니다. [원본 MVP 안내](docs/mvp/overview.md)

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

### 앱 실행

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

나이·지역·취업 상태와 선택적인 관심사를 입력한 뒤 ‘맞춤 정책 추천받기’를 누릅니다. 지역 선택지는 적재된 정책 데이터에서 구성됩니다. 기존 MVP의 AI 검색·설명은 OpenAI API를 호출하며 사용자 관심사·조건이 전달되고 비용이 발생합니다.

## 테스트

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q api.py app.py src scripts tests
node --test tests/test_demo_client.mjs tests/test_mock_demo.mjs
```

[GitHub Actions의 Demo checks](https://github.com/yurimakes/youth-policy-llm-recommender/actions/workflows/demo-checks.yml)는 Windows Python 회귀, JavaScript 시나리오, 정적 빌드와 Chromium 브라우저 흐름을 검사합니다. 실행별 결과와 화면 PNG·상담 PDF는 해당 실행에서 확인합니다. 브라우저 검증은 합성 정책과 합성 입력을 사용하며 실제 공고의 최신성이나 최종 자격을 보증하지 않습니다. [브라우저 검증 방법](docs/demo/README.md#자동-브라우저-검증과-캡처)

## 코드와 문서

| 경로 | 역할 |
|---|---|
| `app.py` | Streamlit MVP |
| `api.py` | 데모와 API를 제공하는 FastAPI 진입점 |
| `demo/` | 로컬 API 모드와 공개 가상 체험 모드 |
| `src/youth_policy/` | 데이터·조건 평가·검색·설명·진행 상태 모듈 |
| `scripts/` | 정책 수집·적재, API 점검, 정적 빌드, 스키마 생성 |
| `tests/` | 회귀 테스트와 브라우저 시나리오 |
| `docs/api/` | API 규격과 JSON Schema |
| `docs/demo/` | 데모 실행 안내와 글꼴 라이선스 |
| `assets/screens/` | 서비스 화면 캡처 |

## 데이터와 이용 조건

주요 출처는 [온통청년](https://www.youthcenter.go.kr/) 청년정책 API입니다. 정책 ID·공식 URL·확인 시각을 보존합니다. `last_verified_at`은 적재·처리 시각이며 담당 기관이 모든 조건을 재확인했다는 뜻이 아닙니다. 최종 자격과 현재 모집 여부는 공식 공고와 담당 기관에서 확인합니다.

API 키·raw 데이터·로컬 DB·사용자 답변은 공개 저장소에 포함하지 않습니다. 공식 데이터의 이용·재배포 조건과 코드 라이선스는 별도로 확인해야 하며 현재 코드 라이선스는 지정되지 않았습니다.
