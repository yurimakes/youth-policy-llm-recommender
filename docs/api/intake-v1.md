# UI 데모 연결용 Intake API v1

## 담당과 구현 상태

팀원은 데모 UI를 담당하고, 이 브랜치는 백엔드와 데이터·AI 연결을 준비한다. 프론트엔드 화면·React·CSS는 이번 변경에 포함하지 않는다.

API 코드는 `api.py`, `src/youth_policy/api_*.py`에 있다. 진행 계약·정책 재평가·Pydantic 스키마는 검증했다. FastAPI/HTTPX 설치가 개발 환경에서 차단되어 **실제 HTTP 실행 테스트 11개는 아직 실행하지 못했다.** 로컬 설치 후 테스트와 서버 실행을 확인해야 한다.

이 API는 외부 AI 호출 없이 규칙 기반으로 동작한다. 카드·선호에 따른 정책 순위, PostgreSQL, LangGraph, RAG, 준비 문서와 공개 배포는 후속 작업이다. 현재 후보는 적재한 정책의 조건 평가 결과이며 개인별 최적 추천 순위가 아니다.

## 실행

저장소 루트의 Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-api.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

위 명령은 제공하는 Windows 실행 방법이며 이 변경에 대한 Windows 실행은 아직 확인 전이다. API 의존성은 기존 requirements.txt와 분리해 추가했다.

정책 데이터가 없으면 기존 수집 CLI로 준비한다. API가 DB·샘플 정책을 자동 생성하지 않는다.

```powershell
.\.venv\Scripts\python.exe scripts/collect_ontong_pages.py --db data/processed/policies.sqlite3 --page-size 10 --max-pages 2
```

수집 건수·내용은 실제 공식 API 응답에 따라 달라진다. 이 수집은 서울·전국 주거·취업 20~30개 정책 목록이 확정됐다는 뜻이 아니다.

- 기본 주소: `http://127.0.0.1:8000`
- 실행 후 자동 문서: `/docs`
- 실행 후 OpenAPI: `/openapi.json`
- 정책 DB 기본 경로: 저장소 루트 기준 `data/processed/policies.sqlite3`
- 선택 설정: `POLICY_DB_PATH`, `API_CORS_ORIGINS`
- 기본 CORS 허용: `http://localhost:5173`, `http://localhost:3000`

UI 개발 서버 origin이 다르면 해당 origin만 명시한다. 별도의 프록시로 같은 origin에서 연결해도 된다.

```powershell
$env:API_CORS_ORIGINS = "http://localhost:8080"
```

## 요청과 응답

| 메서드·경로 | 입력 | 출력 |
|---|---|---|
| `GET /health` | 없음 | 프로세스 상태, `api_version` |
| `GET /ready` | 없음 | DB 준비 여부·정책 건수, 미준비/비어 있음은 503 |
| `POST /api/v1/intake/start` | `{"start_mode":"situation"}` 또는 `{}` | 초기 상태·상황 카드 질문 |
| `POST /api/v1/intake/start` | `{"start_mode":"goal"}` | 초기 상태·목표 카드 질문 |
| `POST /api/v1/intake/transition` | 응답의 `state`와 한 개의 `action` | 갱신된 상태·질문·후보·전환 가능 여부 |

서버는 사용자 진행 상태를 저장하지 않는다. UI는 응답의 `state`를 메모리에서 유지하고 다음 POST의 본문에 그대로 전달한다. UI에서 현재 응답만 버리면 해당 진행을 서버에서 복구할 수 없다. 브라우저 영구 저장·새로고침 복구 여부는 별도 결정사항이다.

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
| `prepare` | 없음 | 현재 결과에서 준비 단계로 이동. 문서 생성은 아직 미구현 |

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

위 코드는 요청 형식 예시이며 프론트엔드 구현 파일이 아니다. 요청을 순서대로 실행하고 성공한 최신 응답으로 state를 교체한다. stateless API이므로 동시 요청의 순서 충돌은 UI에서 관리해야 한다. 오류 응답이면 기존 state를 유지한다. `revision`은 상태 변경 번호이며 서버가 저장하는 잠금·세션 번호가 아니다.

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

## 검증과 계약 재생성

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_intake*.py" -v
.\.venv\Scripts\python.exe -m pytest tests/test_intake_http.py tests/test_intake_schema.py -q
.\.venv\Scripts\python.exe scripts/export_intake_schemas.py
```

API 패키지가 없으면 HTTP 테스트는 명시적으로 skip된다. 스킵을 통과로 해석하지 않고 의존성 설치 후 실제 실행을 확인한다. JSON Schema는 Pydantic 모델에서 생성한 계약 파일이며 실행한 FastAPI의 OpenAPI를 대체했다고 주장하지 않는다.

공식 참고: [FastAPI 테스트](https://fastapi.tiangolo.com/tutorial/testing/), [CORS](https://fastapi.tiangolo.com/tutorial/cors/), [FastAPI 배포 패키지](https://pypi.org/project/fastapi/).
