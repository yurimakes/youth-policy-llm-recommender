# Intake API v1

## 개요

FastAPI가 `/demo`의 HTML/CSS/JavaScript 화면과 진행 API를 함께 제공한다. API 코드는 `api.py`, `src/youth_policy/api_*.py`에 있다.

API의 진행과 조건 판정은 외부 AI 호출 없이 규칙 기반으로 동작한다. 서버가 읽은 정책의 조건 평가 결과를 반환한다. 명확한 조건 불일치를 먼저 제외한 뒤, 사용자가 직접 선택한 관심·목표와 정책명·분야·요약의 키워드 관련성으로 후보를 정렬하고 `recommendation_reasons`로 이유를 제공한다. 개인별 최적 추천 순위나 최종 자격을 확정하지 않는다. 공개 정적 데모는 별도의 가상 데이터를 사용한다. 문서 초안은 클라이언트에서 입력·확인사항을 조합한다.

### 관심 기반 표시 순서와 이유

`recommendation_reasons`는 후보별 문자열 배열이다. 실제 API 화면에서는 “보여드린 이유”로 표시한다. 분야·정책명·요약에 관련 키워드가 있는 경우 각각 3·2·1의 내부 가중치를 더한다. 같은 점수는 데이터 제공 순서를 유지한다. 점수는 확률·자격 점수·AI 성능 지표가 아니다.

생활비는 생활비·주거·월세·전세·장학·학자금·생계, 상담은 상담, 부담 적은 활동은 참여·활동·문화 표현을 비교한다. 목표의 취업은 취업·구직·일자리, 주거는 주거·월세·전세·주택, 학습은 교육·훈련·학습·직무를 비교한다. 부분 문자열 비교 기준선이며 문맥·부정 표현을 이해하는 의미 검색은 아니다. 관련 표현이 없으면 일반 탐색 안내를 제공한다.

상황 카드와 모름·건너뛰기는 관련성 점수에 사용하지 않는다. 관심은 조건 평가 결과를 바꾸거나 후보를 추가·제외하지 않는다. 활동 관련 표현만으로 실제 부담이 적거나 참여 가능하다고 확정하지 않는다. 데이터 최신성·원문 근거 검증은 별도 절차다. 공개 가상 데모의 기존 표시 순서는 유지되며 실제 API의 이유를 가상 정책 근거로 사용하지 않는다.

### 기록된 신청 준비 정보

후보에는 `application_start`, `application_end`(ISO 날짜 또는 null), `required_documents`, `application_method`, `contact`(원문 문자열 또는 null)가 포함된다. 로컬 실제 API의 준비 화면과 문서 초안은 이 값을 “정책에 기록된 준비 정보”로 표시한다. 문서는 화면의 문자열을 그대로 포함하므로 복사·인쇄에도 같은 정보와 처리일이 남는다.

누락된 값은 “공고에서 확인 필요”로 표시하고, 날짜 한쪽만 있으면 남은 날짜를 미확인으로 표시한다. 서류·발급기관·발급 URL을 추정하거나 자동 생성하지 않는다. 수집 기록은 원문 공고의 최신성 검증이나 접수 가능 확정이 아니며 공식 링크에서 다시 확인해야 한다. 사용자 완료 체크는 기관 확인·접수 완료로 취급하지 않는다. 공개 가상 데모에는 이 실제 정책 정보 블록을 표시하지 않는다.

### 후보에 따른 질문 순서

실제 API의 `next_question`은 명확한 불일치가 제외된 현재 후보만 사용한다. 기초 단계는 나이·지역, 동의한 상세 단계는 선택한 정책의 나이·지역·취업 상태 중에서 **비교 가능한 정책 조건이 있고 사용자 입력이 부족한 항목**만 질문한다. 이미 답했거나 건너뛴 항목은 다시 묻지 않는다. 정책 자체의 조건이 없거나 복잡한 항목은 사용자에게 답을 요구하지 않고 확인 필요로 남긴다.

기록된 조건 그룹의 종류가 많은 항목을 먼저 묻고, 동률이면 입력이 필요한 후보 수가 많은 항목을 우선한다. 다시 동률이면 기존 순서(나이·지역·취업 상태)를 유지한다. 지역 코드 목록의 순서와 중복은 그룹 수에 영향을 주지 않는다. 질문 목적에는 현재 후보 중 해당 입력이 필요한 수 또는 선택한 지원을 표시한다. 답변·수정 뒤 후보와 질문을 다시 계산하며 추가 질문이 없으면 UI는 결과로 이동한다.

예를 들어 같은 연령 범위의 두 지역 정책과 조건 정보가 없는 정책이 남아 있으면 지역을 먼저 확인한다. 사용자가 두 지역 밖에 거주한다면 지역 정책은 제외되고, 남은 정책의 연령 조건 자체가 없으므로 나이를 더 묻지 않는다. 남은 정책은 **자격 확인됨이 아니라 확인 필요**다. 이 합성 회귀 사례는 기존 나이→지역 경로의 2개 질문을 1개로 줄이며 최종 조건 상태를 유지한다. 일반적인 질문 수 감소율·사용성 개선·G3 통과를 입증한 성과는 아니다.

이는 외부 모델 없이 구현한 결정론적 질문 선택 기준선이다. 사용자 답변을 예측하지 않고 카드·선호로 사실을 채우지 않는다. LLM 기반 질문 개인화와 실제 정책 평가·최신성 검증은 별도 작업이다. 공개 가상 데모의 질문 흐름은 유지되며 진행 표시만 응답·건너뛰기 이력을 기준으로 계산한다.

## 실행

### 출처를 연결한 설명

`POST /api/v1/intake/explanation`은 `state`, `policy_id`, `focus`(`overview` / `preparation` / `conditions`), `use_ai`(기본 false)를 받는다. 결과·준비 단계에서 현재 후보를 다시 평가하고, 명확한 조건 불일치나 목록 밖 정책은 409로 거부한다. 입력 스키마 밖 정책 텍스트·프롬프트를 받지 않는다. 요청·응답 계약은 `schemas/explanation-request.json`, `schemas/explanation-response.json`에 있다.

기본 경로는 서버가 읽은 요약·지원 내용·신청기간·추가 조건·서류·신청방법 중 목적에 맞는 기록을 최대 3개 보여준다. 각 발췌는 정책 ID와 필드의 `evidence_id`, 필드명, 원문 문자열, 출처명·URL·데이터 처리일과 연결된다. 필드당 최대 600자로 제한하고 생략은 `truncated`와 “일부 발췌”로 표시한다. 누락된 필드는 생성하지 않으며 날짜 한쪽만 있으면 미확인을 유지한다. 공식 원문 페이지를 새로 가져오거나 최신성을 재검증하는 기능은 아니다.

AI 선택은 **기본 비활성**이다. `api.py` 서버에 아래 환경 변수를 설정한 경우에만 제공한다. `.env.example`은 안내용이며 API가 `.env`나 기존 Streamlit secrets를 자동으로 읽지는 않는다. 키는 코드·명령 기록·PR에 포함하지 않는다.

- `POLICY_EXPLANATION_AI_ENABLED=1`
- `OPENAI_API_KEY`: 실행 환경의 비밀 설정
- `POLICY_EXPLANATION_MODEL`: 구조화 출력을 지원하는 사용자의 모델 설정

UI의 “근거로 설명 보기”는 `use_ai=false`로 실행한다. AI가 사용 가능한 경우 전달 범위 안내와 “AI로 핵심 근거 골라보기”를 표시한다. 이 버튼을 누른 요청만 `use_ai=true`다. 모델에는 선택한 정책의 발췌·ID·질문 목적, 명시적 관심·목표, 조건별 상태만 전달하며 사용자 나이·지역 값·취업 상태 값·상황 카드·원문 답변은 전달하지 않는다.

모델 출력은 자유 설명이 아니라 `evidence_ids` 배열만 허용한다. 요청당 호출 1회, 출력 상한 256토큰, SDK timeout 5초, 자동 재시도 0회다. 서버는 ID가 자신이 읽은 해당 정책의 항목인지, 1~3개이며 중복이 없는지 검사한다. 외부 모델이 기록 문자열이나 조건 판정을 작성·덮어쓰지 않는다. `mode=ai_selected`면 AI가 고른 ID의 원래 발췌를 출력하고, 미설정·근거 부족·출처 URL 부재·호출 오류·잘못된 ID·추가 조언이 섞인 응답은 `mode=source_only`로 기록된 근거를 반환한다. 오류 상세·모델 원문은 반환하지 않는다.

화면은 출처 링크와 남은 확인 조건을 표시한다. 최근에 요청한 발췌는 같은 화면의 문서 초안·복사·인쇄에 포함된다. 진행 전환·답변 수정·이전 단계 복귀·설명 요청 실패 시 이전 설명을 지운다. 입력·장바구니 상태는 설명 요청으로 바뀌지 않는다. 공개 가상 데모에서는 이 설명 경로를 실행하지 않는다.

현재 검증은 합성 자료·주입한 선택기·SDK 호출 계약·실제 HTTP와 브라우저 흐름에 대한 회귀 검사다. 실제 OpenAI 호출 품질, 공식 공고 문단 검색, 검색 기준선 비교와 G4 근거 일치율 목표는 별도 검증이며 완료로 표시하지 않는다. 서버 설정만으로 운영 인증·요청별 사용자 비용 예산·정책 최신성이 확보되는 것은 아니며 G5 운영 검증에 포함한다.

저장소 루트의 Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-api.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

API 의존성은 `requirements-api.txt`에 있다. 가상환경 준비는 [개발자 실행 안내](../getting-started/README.md#로컬-환경-준비)를 참고한다.

정책 데이터가 없으면 기존 수집 CLI로 준비한다. API가 DB·샘플 정책을 자동 생성하지 않는다.

```powershell
.\.venv\Scripts\python.exe scripts/collect_ontong_pages.py --db data/processed/policies.sqlite3 --page-size 10 --max-pages 2
```

수집 건수·내용은 실제 공식 API 응답에 따라 달라진다.

- 기본 주소: `http://127.0.0.1:8000`
- 데모 화면: `/demo` 또는 `/demo/` (별도 빌드 없음)
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
| `GET /demo`, `GET /demo/` | 없음 | 데모 HTML 화면 |
| `GET /demo/assets/*` | 없음 | CSS·모듈·공식 참고 JSON·Pretendard 글꼴·라이선스만 허용, MIME 타입 명시 |
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

SQLite는 읽기 전용으로 열고 사용자 답변을 저장하지 않는다. 인증·로그인·자동 제출·자동 연락은 없다. 외부 모델 호출은 별도 설정과 사용자 요청이 있는 설명 endpoint에서만 가능하다. CORS 설정은 브라우저 origin 허용이며 사용자 인증을 대신하지 않는다. 사용자 인증이나 공개 운영에 필요한 개인정보 처리 기능을 제공하지 않는다.

## 내장 데모 확인

시작 화면에서 상황/목표 카드를 선택하고 ‘다음’을 누른다. 질문에 답하거나 건너뛰어 결과를 열고, 답변 수정·정책 선택·선택적 상세 확인을 점검한다. 선택한 정책에 유용한 미확인 질문이 없으면 추가 질문을 제안하지 않는다. 조건별 확인사항·공식 공고와 데이터 처리 기준일, 다음 확인할 항목을 표시한다. UI의 준비 화면에서는 메모리 체크와 입력·확인사항을 모은 문서 초안을 제공한다. PDF 저장은 브라우저 인쇄 기능이다.

요청은 순서대로 실행하며 실패하면 기존 상태를 유지한다. POST와 JSON 읽기는 10초로 제한하고, timeout 이후 늦은 응답은 반영하지 않는다. 사용자가 다시 시도해야 재요청하며 AI를 자동 반복하지 않는다. 동적 정책 문구는 `textContent`로 넣고 공식 링크는 http/https만 허용한다. CSS·JavaScript MIME 타입은 서버가 직접 지정한다. [실제 API 실행·배포 준비](deployment.md)

Node가 있는 개발 환경에서는 `node --test tests/test_demo_client.mjs tests/test_mock_demo.mjs`로 클라이언트를 검증할 수 있다. Node는 데모 실행에 필요하지 않다.

## 검증과 계약 재생성

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_intake*.py" -v
.\.venv\Scripts\python.exe -m pytest tests/test_intake_http.py tests/test_intake_schema.py -q
.\.venv\Scripts\python.exe scripts/export_intake_schemas.py
```

API 패키지가 없으면 HTTP 테스트는 명시적으로 skip된다. 스킵을 통과로 해석하지 않고 의존성 설치 후 실제 실행을 확인한다. JSON Schema는 Pydantic 모델에서 생성한 계약 파일이며 실행한 FastAPI의 OpenAPI를 대체했다고 주장하지 않는다.

공식 참고: [FastAPI 테스트](https://fastapi.tiangolo.com/tutorial/testing/), [CORS](https://fastapi.tiangolo.com/tutorial/cors/), [FastAPI 배포 패키지](https://pypi.org/project/fastapi/).


## 공개 가상 체험과 실제 API의 경계

공개 데모 주소와 사용 방법은 [데모 안내](../demo/README.md)에서 확인할 수 있다. 정적 공개 화면은 `data-runtime="mock"`, 로컬 `/demo`는 `data-runtime="api"`다. 공개 가구·참여 시간 질문을 실제 API action으로 보내지 않는다. 양쪽 UI는 입력·장바구니를 영구 저장하지 않는다. 공식 참고 목록은 공식 페이지를 모은 목록이며 가상 후보의 근거나 현재 신청 가능 증명이 아니다.

정적 파일은 `style.css`, `app.mjs`, `client.mjs`, `mock.mjs`, `preparation.mjs`, `official-policies.json`, Pretendard WOFF2 글꼴 3개와 `Pretendard-OFL.txt`만 허용한다. JavaScript MIME은 OS와 무관하게 text/javascript를 명시하고 JSON은 application/json으로 제공한다.
