# 지원장바구니 개발 현황

- 기준일: 2026-10-07
- 브랜치: `feature/intake-api`
- 이전 작업: PR #2 main 병합 완료 (`d0d86f2`)
- 원본 MVP: `v0.1-mvp` → `23f33e7`
- 단계: 제출용 UI의 Windows MIME 오류 수정; 보완 후 전체 회귀·브라우저 검증 대기

## 이번에 구현한 내용

| 파일 | 변경 내용 |
|---|---|
| `src/youth_policy/intake.py` | 상황/목표 카드, 모름·건너뛰기, 사실·선호 분리, 상세 선택·거절·중단·복귀와 답변 수정 |
| `src/youth_policy/conditions.py` | 조건별 네 가지 상태와 원인, 요청 날짜의 신청 기간 재평가, 명확한 제외와 불확실성 유지 |
| `src/youth_policy/intake_service.py` | 필요한 기초/상세 질문, 현재 후보의 조건 갱신, 공식 근거와 다음 확인 행동 |
| `scripts/preview_intake.py` | 기존 SQLite를 읽기 전용으로 연결하는 개발용 터미널 흐름 |
| `tests/test_intake*.py` | 신규 단위·통합 테스트 49개 |

기존 `app.py`, 데이터 수집·저장·검색·LLM 모듈과 과거 테스트는 수정하지 않았다. 1차 고도화는 PR #2로 main에 병합됐고 원본 태그는 유지했다. 후속 작업은 main에서 분기한 feature/intake-api에 기록한다. 최신 공유본 원문과 과거 명세, 첨부 로고 미리보기를 함께 기록했다.

## 실제 실행한 검증

환경: Linux, 저장소 `.venv/bin/python` 사용.

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_intake*.py' -v
# Ran 49 tests ... OK
.venv/bin/python -m compileall -q app.py src scripts tests
# 성공
.venv/bin/python scripts/preview_intake.py --help
# 성공
```

기존 공식 예시 fixture → 기존 파서 → 임시 SQLite → 신규 안내 흐름 통합을 실행했다. 로컬 CLI의 상세 거절·추가 답변에 따른 후보 제외도 입력을 모의해 실행했다. 실제 사용자 답변 저장과 외부 API 호출은 하지 않았다. Windows CLI의 직접 수동 실행은 미검증이다.

`python -m pytest`는 pytest 패키지가 없어 실행되지 않았다. Git 직접 clone과 npm/pip 패키지 설치가 차단돼 있어 고정 커밋의 파일을 GitHub 연결로 가져와 검증했다. 이 개발 환경의 신규 49개 결과와 아래 사용자의 Windows 전체 회귀 결과를 구분해 기록한다.

### Windows 회귀 실행과 인코딩 수정

사용자가 `ad7b911`을 Windows Python 3.10에서 실행한 결과는 `5 failed, 166 passed, 23 subtests passed`였다. 실패 5개는 신규 통합 테스트의 공통 준비 단계에서 UTF-8 fixture를 시스템 기본 CP949로 읽으면서 발생한 동일한 `UnicodeDecodeError`였다.

`tests/test_intake_integration.py`의 `read_text`에 `encoding="utf-8"`을 명시했다. CP949로 직접 읽을 때 기존 오류가 발생하는 것을 재현하고, 기본 파일 읽기 인코딩을 CP949로 모의한 환경에서 신규 49개 테스트가 모두 통과하는 것을 확인했다. 수정 파일의 compileall도 성공했다. 수정 후 사용자가 `1d67ade`를 Windows Python 3.10에서 다시 실행한 결과는 다음과 같다.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
# 171 passed, 23 subtests passed in 1.53s
```

2026-10-07 사용자가 제공한 터미널 출력으로 기존 122개와 신규 49개를 포함한 전체 회귀 통과를 확인했다. 23개 하위 테스트는 별도 집계이며 171개에 더해 전체 테스트 개수를 표기하지 않는다. 이후 변경은 검증 기록을 갱신하는 문서 변경뿐이다. 실제 사용자 효과·최신 정책 품질·신규 웹 배포 검증과는 구분한다.

## 구현 한계와 다음 단계

- 사용자 지시 변경으로 제출용 3개 데모 화면을 추가했다. 기존 API의 Windows·실제 서버 확인은 완료했고, UI 추가 후 Windows 전체 회귀와 실제 브라우저 확인은 대기 중이다.
- 카드·선호에 따른 정책 관련도 순위는 미구현이다. 선호는 사실과 분리해 저장만 하며 자격에 사용하지 않는다.
- 광역·전국 지역 기준, 복합 소득·학력·예외 조건은 기관 확인으로 남긴다.
- 추가 조건이 기록되지 않은 것을 제한 없음으로 해석하지 않아 전체 정책 요약은 보수적으로 확인 필요를 유지한다.
- 저장한 신청 기간은 요청 날짜로 재평가하지만 최신 공고를 다시 조회하는 기능은 아직 없다.
- PostgreSQL·LangGraph·pgvector/BM25·신규 RAG·준비 문서·배포·실사용 검증은 후속 단계다.
- 초기 정책 20~30개 목록, 모델/API, 개인정보 전달·저장·삭제, 호스팅은 미정이다.
- 최신 공유본의 청년 20명 실사용 테스트는 보류다. 평가 100건 이상·근거 일치율 95% 이상은 향후 목표다.

과거 자동 테스트 122개·실제 API 20건은 2026-07 기록이며 이번 검증과 구분한다.

## 2차: UI 분담과 API 연결

이 단계에서는 팀원 UI 담당이라는 당시 지시에 따라 프론트엔드를 추가하지 않았다. 이후 변경은 아래 4차 항목에 기록한다.

- `api.py`, `api_app.py`: 시작·상태 전환·health/readiness FastAPI 코드
- `api_schemas.py`, `intake_contract.py`: 구조화 입력·응답, 상태·이력 일관성, 서버 후보·날짜 재평가
- `api_config.py`, `policy_repository.py`: 명시적 CORS, 한국 날짜, SQLite 읽기 전용 조회
- `docs/api/intake-v1.md`, `docs/api/schemas/`: UI 연결 규격과 실제 Pydantic 모델에서 생성한 JSON Schema
- `requirements-api.txt`: 기존 Streamlit과 분리한 API 추가 의존성 목록

서버는 사용자 진행 상태를 저장하지 않고 POST 본문의 상태를 검증·갱신한다. 로그인·인증·브라우저 영구 저장·외부 AI 호출은 이 단계에 포함하지 않는다. 클라이언트가 보낸 후보·판정·날짜 필드는 받지 않고 현재 서버 정책으로 다시 평가한다.

검증은 기존 신규 로직 49개, API 계약·저장 경계 26개, 실제 Pydantic 스키마 6개를 포함한다. 설치된 런타임 Pydantic 2.13.5를 실제로 사용했다. FastAPI·HTTPX는 패키지 설치 차단으로 이용할 수 없어 HTTP 테스트 11개를 실행하지 못했다. 전체 대상 92개 중 성공 81개·스킵 11개이며 스킵을 통과로 표시하지 않는다. api.py/app.py/src/scripts/tests의 compileall과 JSON Schema 생성·JSON 읽기도 성공했다.

### Windows API 전체 회귀 확인

2026-10-07 사용자가 `feature/intake-api`의 `ff2fc56`에서 requirements-api.txt를 설치한 뒤 전체 pytest를 실행한 결과:

```text
214 passed, 1 warning, 57 subtests passed in 2.78s
```

실제 FastAPI TestClient 테스트 11개가 포함된 전체 회귀 통과다. 경고는 Starlette TestClient의 httpx 사용에 관한 deprecation이며 테스트 실패는 아니다. 이 결과는 `ff2fc56`의 기록이며 이후 변경 전체가 검증됐다는 뜻은 아니다. 실제 Uvicorn 서버 기동·사용자 로컬 DB·팀원 UI 연동·최신 공식 공고는 별도 확인이 필요하다.

## 3차: 제출 전 실제 서버 점검 도구

- `src/youth_policy/api_smoke.py`, `scripts/check_intake_api.py`: 실행 중인 로컬 HTTP API에 합성 답변을 보내 서버·DB 준비 상태, 런타임 OpenAPI, 상황/목표 경로, 모름·건너뛰기, 답변 수정, 상세 거절·중단·복귀, 준비 단계 전환을 점검한다.
- 사용자 입력·응답 원문·진행 상태를 저장하지 않고 요약만 출력한다. loopback HTTP만 허용하며 프록시·리다이렉트는 사용하지 않는다.
- 후보나 필요한 상세 질문이 없으면 상세 점검을 SKIP으로 표시한다. 실패는 종료 코드 1, `--require-detail` 사용 시 상세 스킵은 종료 코드 2다. 공식 URL이 없는 후보는 WARN으로 표시한다.
- API 계약·제품 로직·선호 질문 범위는 변경하지 않았다. 준비 단계 점검은 문서 생성 검증이 아니다.

개발 환경에서 실제 실행:

```bash
PYTHONPATH="$CODEX_PRIMARY_RUNTIME_ROOT/dependencies/python/lib/python3.12/site-packages" .venv/bin/python -m unittest discover -s tests -p 'test_intake*.py' -v
# Ran 100 tests ... OK (skipped=11): 성공 89개 / HTTP 11개 스킵
```

신규 점검 도구 테스트 8개는 실제 loopback 표준 라이브러리 HTTP 참조 서버와 순수 진행 계약을 연결해 실행했다. 정상 흐름, 마감 정책에 따른 후보 없음·상세 스킵, 503, no-store 누락, 리다이렉트 차단, 잘못된 JSON, 외부 주소 차단, 계약 누락을 확인했다. api.py/app.py/src/scripts/tests의 compileall과 점검 CLI의 --help도 성공했다. 이는 FastAPI 대체 구현이나 실제 Uvicorn 실행 결과가 아니다. 현재 변경의 Windows 전체 pytest·실제 서버 점검은 확인 전이다.

### Windows 전체 회귀와 실제 서버 확인 (`2b8b66b`)

2026-10-07 사용자 실행:

```text
222 passed, 1 warning, 67 subtests passed in 3.44s
```

Uvicorn의 startup complete와 localhost:8000 기동, 점검 CLI의 실제 HTTP 요청 200 응답을 확인했다. `/ready`는 DB 정책 20건, 기본 경로는 후보 5건을 반환했다. 점검 결과는 PASS 5 / FAIL 0 / SKIP 1 / WARN 0이다. 스킵 항목은 상세 중단·복귀이며 첫 선택 정책에 남은 유용한 상세 질문이 없었다. 준비 단계 이동은 통과했으나 문서 생성은 미구현이다. 데이터 20건의 최신성·초기 정책 목록 확정·UI 연동을 인증한 결과는 아니다.

### 상세 점검 보완

기존 도구는 기본 경로에서 질문을 건너뛴 상태로 첫 후보의 상세 질문 가능 여부만 확인해, 다른 후보나 별도의 상세 경로에서 검증 가능한 경우도 스킵할 수 있었다. 새 합성 진행에서 사실에 답하지 않은 상태로 후보를 차례로 확인하고 상세 질문이 필요한 정책을 찾도록 보완했다. 기존 건너뛰기 이력을 지우거나 필요 없는 질문을 강제로 생성하지 않는다. API 계약·제품 로직은 변경하지 않았다.

회귀 사례 2개를 추가해 기본 질문만 필요한 정책의 새 상세 경로, 첫 정책에 상세 질문이 없고 뒤 후보에 있는 경우, 모든 후보에 질문이 없을 때의 정당한 스킵을 검증했다. 개발 환경의 관련 테스트 102개 중 성공 91개·FastAPI 테스트 11개 스킵과 compileall 성공을 확인했다. 이 보완의 실제 사용자 서버 점검과 Windows 전체 회귀는 아직 확인 전이다.

### API 작업세트 최종 확인 (`1862bbe`)

2026-10-07 사용자 Windows Python 3.10 실행:

```text
224 passed, 1 warning, 67 subtests passed in 4.06s
```

실행 중인 Uvicorn 서버에 `scripts/check_intake_api.py --require-detail`을 실행한 결과:

```text
PASS 6 / FAIL 0 / SKIP 0 / WARN 0
정책 DB 20건 / 기본 경로 후보 5건
```

서버·DB·런타임 OpenAPI, 상황 진입·건너뛰기, 목표 진입·답변 수정, 상세 거절, 상세 동의·중단·복귀, 준비 단계 이동을 모두 확인했다. pytest 경고 1개는 기존 Starlette TestClient의 httpx deprecation이다. 점검 도구 경고 0개와는 별도 집계다.

당시 API 작업세트 검증을 완료해 PR #3을 검토 가능한 상태로 전환했다. 이후 변경은 이 결과를 기록하는 문서 갱신이며 실행 코드는 변경하지 않았다. 팀원 UI·브라우저 CORS 연동, 공식 정책 목록 최신성·선정, 정책 관련도 순위와 준비 문서 생성은 후속 검증사항이다. 이번 확인은 해당 기능들의 구현 완료를 뜻하지 않는다.


## 4차: 제출용 3개 데모 화면 (2026-10-07)

팀원은 2–3개 UI만 맡을 예정이며 아직 시작 전이라는 사용자 설명과 담당 변경 지시에 따라, 같은 브랜치에 UI를 추가했다. [결정 기록](docs/decisions/2026-10-demo-ui.md).

- `demo/index.html`, `style.css`, `app.mjs`: 시작·질문·결과 화면, 세로 선택 카드·선택 표시·다음 버튼, 모름·건너뛰기, 직접 답한 조건 수정, 공식 근거와 다음 행동, 선택적 상세 확인 거절·중단·복귀.
- `demo/client.mjs`: 메모리 상태, 성공 응답만 교체, 오류 시 이전 답변 유지, 중복 요청 방지, 안전한 공식 URL·한국 날짜 표시.
- `api_app.py`: `/demo`와 `/demo/`, 데모 정적 파일만 제공하는 `/demo/assets` 추가. API 계약·판정 규칙은 변경하지 않았다.
- `tests/test_intake_http.py`: 화면·정적 파일·no-store와 소스/DB 경로 차단을 확인하는 HTTP 테스트 2개 추가.
- `tests/test_demo_client.mjs`: 상대 경로 POST·이전 상태 보존·중복 요청·잘못된 응답·URL·날짜·화면 단계 관리 7개 테스트.

HTML/CSS/JavaScript 데모이며 React 구현 완료로 표시하지 않는다. npm/Node 빌드는 없고 API 서버 하나로 제공한다. 서버 정책·실제 DB를 사용하며 샘플 정책을 제품에 넣지 않는다. 로고는 기존 서비스 심볼을 재사용한다. 새 데모의 외부 AI 호출·로그인·영구 저장·준비 문서 생성은 없다.

### 현재 변경에서 실행한 검증

- `node --test tests/test_demo_client.mjs`: 7 passed, 0 skipped.
- `node --check demo/app.mjs`, `node --check demo/client.mjs`: 성공.
- 런타임 Pydantic을 연결한 `.venv/bin/python -m unittest discover -s tests -p 'test_intake*.py' -q`: 대상 104개 중 성공 91개·FastAPI HTTP 스킵 13개. FastAPI/httpx 설치 차단으로 신규 2개도 실행하지 못했다.
- api.py/app.py/src/scripts/tests의 compileall: 성공. HTML ID 중복 없음 확인.
- 실제 UI 클라이언트를 참조 HTTP 서버와 실제 순수 진행 계약·Pydantic 스키마에 연결해 상황/목표, 상세 동의·중단·복귀, 취업 상태 답변, 나이 수정 후 후보 제외, 상세 거절, 준비 단계 이동을 확인했다. 합성 테스트 정책만 사용했고 제품 데이터에 적재하지 않았다. 이 결과는 실제 FastAPI·Uvicorn·브라우저 클릭 검증이 아니다.

브라우저가 개발 환경의 로컬 서버에 접속하지 못해 화면 배치·실제 조작은 확인하지 못했다. 위의 224 passed는 UI 추가 전 `1862bbe` 기록이며 새 UI 변경의 전체 회귀로 인용하지 않는다. PR #3은 새 범위를 반영해 draft로 되돌리고, 사용자 Windows에서 전체 pytest와 서버 재시작 후 `/demo` 확인을 기다린다. main은 아직 병합하지 않는다.


### Windows 데모 모듈 MIME 오류와 수정

2026-10-07 사용자가 `f22e949`를 Windows Python 3.10에서 실행한 결과:

```text
2 failed, 226 passed, 1 warning, 73 subtests passed in 4.93s
```

실패 2개는 같은 HTTP 테스트의 app.mjs·client.mjs 하위 사례다. 두 파일의 응답이 `text/plain; charset=utf-8`이라 JavaScript MIME 검증에 실패했다. 화면·CSS 제공과 기존 API 회귀에서 추가 실패는 보고되지 않았으며 Uvicorn startup complete도 확인했다. 이 결과를 전체 통과로 표시하지 않는다.

OS의 파일 확장자 MIME 추측을 사용하던 정적 제공을, style.css·app.mjs·client.mjs만 허용하는 파일 경로로 변경했다. `FileResponse`에 각각 `text/css`·`text/javascript`를 명시해 Windows 분류에 의존하지 않는다. 경로·API 계약·화면은 유지하고 허용하지 않은 파일은 404를 반환한다.

HTTP 회귀 테스트 1개를 추가해 실제 mimetypes의 .mjs 분류를 text/plain으로 바꾼 상태에서도 두 모듈의 JavaScript 헤더와 no-store를 확인한다. 기존 경로 제한 테스트도 목록 밖 파일 차단을 확인하도록 보완했다.

수정 후 개발 환경에서 관련 Python 테스트 105개 중 성공 91개·HTTP 스킵 14개, compileall 성공을 확인했다. 표준 라이브러리에서 잘못된 MIME 분류 재현과 테스트 종료 후 복구도 확인했다. FastAPI/httpx를 설치할 수 없어 HTTP 회귀 테스트의 실제 실행은 사용자 Windows에서 확인해야 한다. 수정 후 전체 pytest와 브라우저 화면 조작은 대기 중이며 PR #3은 draft로 유지한다.
