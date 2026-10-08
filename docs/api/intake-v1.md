# UI 데모 연결용 Intake API v1

## 담당과 구현 상태

사용자가 확정한 화면 보드에 따라 질문·결과·장바구니 준비·상담 문서 초안까지 제출용 UI를 연결했다. 기존 FastAPI가 `/demo`에서 HTML/CSS/JavaScript와 API를 함께 제공한다. React/TypeScript는 후속 방향이다.

API 코드는 `api.py`, `src/youth_policy/api_*.py`에 있다. 진행 계약·정책 재평가·Pydantic 스키마를 검증했고, `1862bbe`의 Windows 전체 pytest에서 **224 passed, 67 subtests passed, 경고 1개**를 확인했다. FastAPI TestClient 테스트 11개도 포함된다. 실제 Uvicorn 서버·정책 DB 20건·기본 후보 5건에서 상세 중단·복귀를 포함한 점검 **6개 모두 통과(실패·스킵·점검 경고 0개)**를 확인했다. 이 검증은 UI 추가 전 API 결과다. 최신 97cd09a의 Windows 전체 pytest 230 passed·82 subtests passed와 Chromium 시연 6개를 확인했다. 현재 브라우저 테스트는 실제 FastAPI에 합성 정책을 연결한 결과이며, 실제 데이터 전체의 최신성 검증과 구분한다.

이 API는 외부 AI 호출 없이 규칙 기반으로 동작한다. 실제 API의 관련도 순위, PostgreSQL, LangGraph와 RAG는 후속이다. 공개 정적 목데이터 체험은 실제 API와 별개이며 문서 초안은 클라이언트에서 입력·확인사항을 조합한다. 현재 후보는 적재한 정책의 조건 평가 결과이며 개인별 최적 추천 순위가 아니다.

## 실행

저장소 루트의 Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-api.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

API 의존성 설치, `1862bbe`의 Windows 전체 테스트, 위 Uvicorn 서버 기동과 `--require-detail` 점검을 확인했다. API 의존성은 기존 requirements.txt와 분리해 추가했다.

정책 데이터가 없으면 기존 수집 CLI로 준비한다. API가 DB·샘플 정책을 자동 생성하지 않는다.

```powershell
.\.venv\Scripts\python.exe scripts/collect_ontong_pages.py --db data/processed/policies.sqlite3 --page-size 10 --max-pages 2
```

수집 건수·내용은 실제 공식 API 응답에 따라 달라진다. 이 수집은 서울·전국 주거·취업 20~30개 정책 목록이 확정됐다는 뜻이 아니다.

- 기본 주소: `http://127.0.0.1:8000`
- 제출용 화면: `/demo` 또는 `/demo/` (별도 빌드 없음)
- 실행 후 자동 문서: `/docs`
- 실행 후 OpenAPI: `/openapi.json`
- 정책 DB 기본 경로: 저장소 루트 기준 `data/processed/policies.sqlite3`
- 선택 설정: `POLICY_DB_PATH`, `API_CORS_ORIGINS`
- 기본 CORS 허용: `http://localhost:5173`, `http://localhost:3000`

내장 데모는 같은 origin으로 연결하므로 CORS 추가 설정이 없다. 코드 갱신 후 기존 서버를 Ctrl+C로 종료하고 다시 실행한다. 별도 UI 개발 서버 origin이 다르면 해당 origin만 명시한다. 별도의 프록시로 같은 origin에서 연결해도 된다.

```powershell
$env:API_CORS_ORIGINS = "http://localhost:8080"
```

### 실행 중인 서버 점검

서버를 실행한 채 다른 PowerShell 창에서:

```powershell
.\.venv\Scripts\python.exe scripts/check_intake_api.py
# 다른 로컬 포트를 쓸 때
.\.venv\Scripts\python.exe scripts/check_intake_api.py --base-url http://127.0.0.1:8001
# 상세 중단·복귀까지 확인이 필수인 경우
.\.venv\Scripts\python.exe scripts/check_intake_api.py --require-detail
```

실제 사용자 정보 대신 카드 선택·합성 나이 24·모름 답변을 사용한다. 응답 상태 전체를 다음 POST에 전달하고 `/health`, `/ready`, 실행 중인 `/openapi.json`, 기본/목표 경로·건너뛰기·답변 수정·상세 거절·중단/복귀·준비 단계 전환을 확인한다. loopback HTTP만 허용하며 상태·응답 원문을 저장하지 않는다.

상세 중단·복귀는 기본 경로에서 건너뛴 답변을 수정하지 않고 별도의 새 합성 진행에서 점검한다. 첫 정책에 유용한 질문이 없으면 다음 후보도 확인한다. 모든 후보에 질문이 없으면 SKIP이 정상이며, 테스트를 위해 실제 데이터나 제품 질문 규칙을 바꾸지 않는다.

| 결과 | 의미 |
|---|---|
| PASS | 해당 흐름 확인 성공 |
| FAIL | 서버·DB·응답 계약·흐름 오류. 종료 코드 1 |
| SKIP | 현재 후보 또는 필요한 상세 질문이 없어 해당 확인을 실행하지 못함 |
| WARN | 후보의 공식 공고 URL 보완 필요 |

정상 완료의 종료 코드는 0이다. `--require-detail`에서 상세 확인이 스킵되면 2를 반환한다. 요약의 `skipped`·`warnings`도 확인한다. `/ready`의 503은 기존 공식 데이터 수집·적재 상태를 확인해야 하며 fixture를 실제 정책으로 적재해 해결하지 않는다. 정책 날짜 때문에 후보가 없다면 최신 공고 목록을 확인한다.

점검 성공은 공고의 최신성·최종 신청 가능·브라우저 CORS·UI 통합을 인증하지 않는다. 이 명령은 준비 단계 이동만 확인하며 문서를 생성하지 않는다.

## 요청과 응답

| 메서드·경로 | 입력 | 출력 |
|---|---|---|
| `GET /demo`, `GET /demo/` | 없음 | 제출용 HTML 화면 |
| `GET /demo/assets/*` | 없음 | style.css·app.mjs·client.mjs만 허용, MIME 타입 명시 |
| `GET /health` | 없음 | 프로세스 상태, `api_version` |
| `GET /ready` | 없음 | DB 준비 여부·정책 건수, 미준비/비어 있음은 503 |
| `POST /api/v1/intake/start` | `{"start_mode":"situation"}` 또는 `{}` | 초기 상태·상황 카드 질문 |
| `POST /api/v1/intake/start` | `{"start_mode":"goal"}` | 초기 상태·목표 카드 질문 |
| `POST /api/v1/intake/transition` | 응답의 `state`와 한 개의 `action` | 갱신된 상태·질문·후보·전환 가능 여부 |

서버는 사용자 진행 상태를 저장하지 않는다. UI는 응답의 `state`를 메모리에서 유지하고 다음 POST의 본문에 그대로 전달한다. UI에서 현재 응답만 버리면 해당 진행을 서버에서 복구할 수 없다. 내장 데모는 브라우저 영구 저장 없이 메모리만 사용하며 새로고침하면 초기화된다.

상태의 사실은 사용자 본인이 확인·입력한 값이다. 서버는 형식과 단계·답변 이력의 일관성을 검증하지만 신원을 인증하거나 답변 사실성을 증명하지 않는다. 정책 후보·판정·기준일을 클라이언트가 주입하는 필드는 없다. 서버 정책 DB와 한국 날짜(UTC+9)로 조건을 다시 평가한다.

이 문서의 필드명 예시는 계약 설명이며 실제 정책 데이터·신청 가능 결과가 아니다. 전체 스키마:

- [시작 요청](schemas/start-request.json)
- [전환 요청](schemas/transition-request.json)
- [진행 응답](schemas/intake-response.json)

## action 종류

| type | 추가 필드 | 의미 |
|---|---|---|
| `choose_card` | `key`, `value` | 상황/관심/목표 선택. `null`은 건너뛰기 |
| `answer_fact` | `key`, `value` | 직접 확인한 만 나이·지역 코드·취업 상태. `null`은 모름·건너뛰기 |
| `answer_preference` | `key`, `value` | 상세 단계의 선호. `null`은 건너뛰기 |
| `show_results` | 없음 | 현재 정보로 결과 확인, 상세 질문 종료 |
| `select_policy` | `policy_id` | 서버 응답의 후보 중 관심 정책 선택 |
| `choose_detail` | `accept` (boolean) | 상세 확인 동의/거절. 필요한 추가 입력 여부는 서버가 판단 |
| `pause_detail` | 없음 | 상세 확인 중단, 답변 보존 |
| `resume_detail` | 없음 | 동의한 상세 확인을 이어감. 선택 정책이 제외됐으면 거절 |
| `prepare` | 없음 | 현재 결과에서 준비 단계로 이동. 서버는 문서를 생성하지 않으며 UI에서 정해진 초안을 구성 |

첫 API 응답을 `result`에 보관했다고 할 때 전환 본문 형태는 다음과 같다. JSON의 `state` 위치에는 **result.state 전체 객체**를 넣는다.

```javascript
const response = await fetch("http://127.0.0.1:8000/api/v1/intake/transition", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    state: result.state,
    action: { type: "choose_card", key: "situation", value: "resting" }
  })
});
const updated = await response.json();
```

위 코드는 요청 형식 예시다. 내장 데모의 실제 구현은 `demo/client.mjs`와 `demo/app.mjs`에 있다. 요청을 순서대로 실행하고 성공한 최신 응답으로 state를 교체한다. stateless API이므로 동시 요청의 순서 충돌은 UI에서 관리해야 한다. 오류 응답이면 기존 state를 유지한다. `revision`은 상태 변경 번호이며 서버가 저장하는 잠금·세션 번호가 아니다.

## 선택값과 표시 기준

| 필드 | 값 |
|---|---|
| `situation` | `school`, `working`, `resting`, `unknown` |
| `interest` | `living_cost`, `low_burden`, `counseling`, `unknown` |
| `goal` | `employment`, `housing`, `learning`, `unknown` |
| `age` | 만 나이 정수 0~120. 문자열·boolean·소수는 유효한 나이 입력이 아님 |
| `region_code` | 실제 거주 지역 5자리 문자열. 명칭과 코드를 동일 값으로 취급하지 않음 |
| `employment_status` | 응답 질문 options의 지원 값. 상황 카드에서 추정하지 않음 |
| `participation_format` | `online`, `offline`, `either` |
| `contact_format` | `phone`, `online`, `in_person`, `either` |

0~120은 입력 형식 검증 범위이며 서비스의 모집 대상 연령을 뜻하지 않는다. 상세 단계의 선호는 저장 상태에 구분해 보관하며 아직 후보 순위·다음 행동에는 반영하지 않는다.

- `next_question`: 질문 하나 또는 `null`. `input_type`, `options`, `purpose`, `allow_skip`를 제공한다.
- `can_show_results`: 현재 정보로 결과를 확인할 수 있는 단계인지 표시한다. 자격 충족을 뜻하지 않는다.
- `detail_offer_available`: 결과 단계에서 관심 정책 선택 후 필요한 미확인 항목이 있는 경우다. 전환을 자동 실행하지 않는다.
- `selected_policy_excluded`: 추가 답변·데이터 변경으로 관심 정책이 현재 후보에서 제외되면 true다.
- `candidates`: 정책 ID·이름·공식 요약·혜택, 네 가지 상태와 개별 확인사항, 다음 행동, 출처와 확인 시각을 제공한다.
- `data_status`: `not_loaded` (시작 단계), `ready` (정책 데이터 읽음), `empty` (DB에 정책 없음). `ready`는 모든 공고의 최신성을 인증하지 않는다.
- 질문이 없으면 UI가 `show_results`를 요청해 결과 단계로 이동한다. 정보가 부족해도 확인되지 않은 조건을 명시하는 현재 안내 경로는 유지한다.

`confirmed`/`not_met`/`check_required`/`input_missing`을 UI에서 임의의 ‘신청 가능’으로 치환하지 않는다. `notice`를 유지하고 개별 확인사항과 공식 링크를 표시한다.

## 오류와 데이터 경계

| HTTP | code | 대응 |
|---|---|---|
| 422 | `invalid_payload` / `invalid_state_or_answer` | 필드·값·상태 이력 확인, 현재 UI 상태 유지 |
| 409 | `transition_conflict` | 현재 단계·정책 후보에서 허용되는 행동인지 확인 |
| 503 | `policy_data_unavailable` | 데이터 준비·적재 확인. 사용자 입력 재요구로 해결하지 않음 |
| 503 | `policy_data_empty` | `/ready`의 비어 있는 DB 상태. 정책 목록 준비 필요 |

오류 응답은 `{"error":{"code":"...","message":"..."}}` 형식이다. 제출한 원문 값·내부 파일 경로를 오류에 돌려주지 않는다. POST 본문에 임의 필드, 계좌·주민등록번호·자유 입력 필드를 추가하면 거절한다. 모든 API 응답은 `Cache-Control: no-store`다.

SQLite는 읽기 전용으로 열고 사용자 답변을 저장하지 않는다. 인증·로그인·외부 모델 호출·자동 제출·자동 연락은 없다. CORS 설정은 브라우저 origin 허용이며 사용자 인증을 대신하지 않는다. 로컬 데모 연결 이후 공개 운영·개인정보 처리 설계는 별도 결정한다.

## 내장 데모 확인

시작 화면에서 상황/목표 카드를 선택하고 ‘다음’을 누른다. 질문에 답하거나 건너뛰어 결과를 열고, 답변 수정·정책 선택·선택적 상세 확인을 점검한다. 선택한 정책에 유용한 미확인 질문이 없으면 추가 질문을 제안하지 않는다. 조건별 확인사항·공식 공고와 데이터 처리 기준일, 다음 확인할 항목을 표시한다. UI의 준비 화면에서는 메모리 체크와 입력·확인사항을 모은 문서 초안을 제공한다. PDF 저장은 브라우저 인쇄 기능이다.

요청은 순서대로 실행하며 실패하면 기존 상태를 유지한다. 동적 정책 문구는 `textContent`로 넣고 공식 링크는 http/https만 허용한다. Windows에서 모듈이 text/plain으로 제공된 오류를 확인해 CSS·JavaScript MIME 타입을 서버가 직접 지정하도록 수정했다. 수정 후 Windows 전체 회귀·시각적 배치는 PROJECT_STATUS의 확인 대기 항목이다.

Node가 있는 개발 환경에서는 `node --test tests/test_demo_client.mjs tests/test_submission_demo.mjs`로 클라이언트를 검증할 수 있다. Node는 데모 실행에 필요하지 않다.

## 검증과 계약 재생성

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_intake*.py" -v
.\.venv\Scripts\python.exe -m pytest tests/test_intake_http.py tests/test_intake_schema.py -q
.\.venv\Scripts\python.exe scripts/export_intake_schemas.py
```

API 패키지가 없으면 HTTP 테스트는 명시적으로 skip된다. 스킵을 통과로 해석하지 않고 의존성 설치 후 실제 실행을 확인한다. JSON Schema는 Pydantic 모델에서 생성한 계약 파일이며 실행한 FastAPI의 OpenAPI를 대체했다고 주장하지 않는다.

공식 참고: [FastAPI 테스트](https://fastapi.tiangolo.com/tutorial/testing/), [CORS](https://fastapi.tiangolo.com/tutorial/cors/), [FastAPI 배포 패키지](https://pypi.org/project/fastapi/).


## 공개 가상 체험과 실제 API의 경계

공개 제출 주소와 시연 방법은 `docs/submission/2026-10-08-demo.md`에서 관리한다. 정적 공개 화면은 `data-runtime="mock"`, 로컬 `/demo`는 `data-runtime="api"`다. 공개 가구·참여 시간 질문을 실제 API action으로 보내지 않는다. 양쪽 UI는 입력·장바구니를 영구 저장하지 않는다. 공식 참고 목록은 별도 검토한 페이지이며 가상 후보의 근거나 현재 신청 가능 증명이 아니다.

정적 파일은 style.css, app.mjs, client.mjs, mock.mjs, official-policies.json의 다섯 파일만 허용한다. JavaScript MIME은 OS와 무관하게 text/javascript를 명시하고 JSON은 application/json으로 제공한다.


2026-10-08 최종 코드 97cd09a는 Windows 전체 pytest 230 passed·82 subtests passed·경고 1개와 Chromium 자동 시연 6개를 통과했다. 실제 FastAPI에 격리된 합성 정책을 연결해 브라우저의 모듈 제공·지역 코드 입력/수정·공식 링크·준비/상담 흐름을 확인했다. 사용자 DB 20건의 과거 서버 검증과 구분하며 실제 데이터 전체의 최신성을 확인한 결과는 아니다. PR #3은 main에 병합됐다.
