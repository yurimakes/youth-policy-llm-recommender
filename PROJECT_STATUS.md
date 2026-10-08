# 지원장바구니 개발 현황

- 갱신일: 2026-10-08, 한국 시간
- 후속 작업 브랜치: `docs/clean-ui-capture` (main 기준, 상담 화면 캡처 수정)
- 후속 변경: v0 이미지의 글자 굵기에 맞춘 Pretendard 파일 제공, 일반 데모 안내·계획·빌드·검증 경로로 정리.
- 현재 기준: `main`. `feature/intake-api`의 PR #3 병합 완료 (`2e120f3`)
- 이전 검증 코드 기준: `97cd09a` (공개 체험 버전 3)
- main: 1차 고도화 PR #2 병합 완료 (`d0d86f2`)
- 원본: `v0.1-mvp` → `23f33e7`, 변경 없음
- 공개 데모: https://jiwon-basket.vercel.app/ (사용자 배포·접속 확인)
- 현재 단계: 확정 UI·공개 목데이터 배포·Windows 전체 회귀·Chromium 핵심 시연 완료. 데모 코드 작업세트를 main에 병합했다.

## 현재 구현과 경계

| 구간 | 구현 | 한계 |
|---|---|---|
| 진행·조건 | Python 카드·질문·상세·수정, 조건 4상태, 명확한 제외, 날짜 재평가 | 복합 소득·학력·예외는 기관 확인 |
| 실제 API | stateless FastAPI, SQLite 읽기 전용, 상태·전환·스키마 검증 | 공개 Python 서버 운영·인증·영구 저장 미구현 |
| 확정 UI | 상황·관심·기초·방향·상세 제안·상세·갱신·준비·상담 요약 | Chromium 자동 시연 완료. 사람의 디자인 검토·모바일 실기기 확인과 React 구현은 별도 |
| 공개 체험 | 정적 목데이터 6개, 상단·후보·문서에 가상 표시 | 실제 정책 자격 판정·실제 DB 연동 없음 |
| 준비·문서 | 메모리 장바구니, 사용자 완료 체크, 요약·체크리스트·발급 안내·문의 초안, 복사·인쇄 PDF | 기관 확인·자동 발급·AI 생성·자동 연락 없음 |
| 공식 참고 | 실제 제도 6개의 공식 페이지, ID·URL·확인일·기간 안내 | 가상 후보와 연결 안 함. 전체 조건의 정규화·실제 DB 선별 미완료 |

확정 ZIP과 재첨부 ZIP의 SHA-256이 일치한다. 사용자 지시는 초기 3개 화면 범위를 확장했으며 `docs/decisions/2026-10-approved-ui-and-public-demo.md`에 기록했다. Python 계약은 확장하지 않았다. 새 가구·참여 시간 질문과 관심 관련도 정렬은 목데이터 진행에만 사용한다. 상황 카드에서 미취업·소득·거주를 추정하지 않는다.

## 이번 변경에서 실제 실행한 검증

| 검증 | 결과 | 구분 |
|---|---|---|
| Node 클라이언트·가상 진행 | 15 passed, 0 failed, 0 skipped | API 요청 상태 보존 + 가상 핵심 시나리오 |
| Python 공개 빌드 | 2 tests OK | 원본 API 모드 유지, 정적 리소스·배포 파일 경계 |
| Python 관련 진행·계약 | 성공 91, HTTP 스킵 15 | FastAPI/httpx 미설치. 스킵을 통과로 집계하지 않음 |
| compileall / JS syntax | 성공 | api.py, app.py, src, scripts, tests와 모듈 구문 |
| 공개 정적 빌드·배포 | 배포 succeeded, audience public | 로그인 없는 공개 URL, 실제 서버 공개 운영 검증 아님 |
| 공식 참고 페이지 | 2026-10-08 확인, 6개 기록 | 청년수당·월세의 해당 모집 종료 표시; 나머지 기관·예약 확인 필요 |
| Windows 전체 pytest·HTTP | 230 passed, 82 subtests passed, warning 1 | 최신 코드 97cd09a, GitHub Actions Windows Python 3.10. 실제 TestClient 경로 포함 |
| 브라우저 화면·캡처 | 6 passed (11.7s) | Chromium의 5개 핵심 시나리오 + 실제 FastAPI 합성 정책 연결, 복사·PDF·모바일 가로 넘침 확인 |

실행 명령:

```bash
node --test tests/test_demo_client.mjs tests/test_mock_demo.mjs
node --check demo/app.mjs
PYTHONPATH="$CODEX_PRIMARY_RUNTIME_ROOT/dependencies/python/lib/python3.12/site-packages" .venv/bin/python -m unittest discover -s tests -p 'test_intake*.py'
.venv/bin/python -m unittest discover -s tests -p 'test_demo_build.py'
.venv/bin/python -m compileall -q api.py app.py src scripts tests
.venv/bin/python scripts/build_demo.py --output <정적 출력 폴더>
```

자동 검증에서는 모름·건너뛰기, 상세 거절·중단·복귀, 명시적 취업·나이 수정에 따른 제외와 모름으로 복원, 선호와 자격 분리, 후보 없음·데이터 오류 후 이전 답변 유지와 재시도를 확인했다. 첫 로컬 단위 검증은 실제 브라우저 결과가 아니며, 이후 확보한 Chromium 자동 시연 결과는 아래 최종 기록에 구분한다. 사람의 수동 시연과 모바일 실기기 검증은 아니다. 정적 HTML에는 연결된 자산이 존재하고 실제 API HTML은 API 모드를 유지한다.

Windows 재발 방지를 위해 모듈 3개와 JSON의 MIME을 직접 지정하고 HTTP 사례를 추가했다. Windows Python 3.10 전체 pytest, Node, 정적 빌드와 Chromium 시연을 수행하는 `Demo checks` 워크플로를 운영한다. 성공한 실행과 단순 설정을 구분해 기록한다.

## 이전 사용자 실행 기록

| 커밋 | 사용자 Windows 결과 | 의미 |
|---|---|---|
| ad7b911 | 5 failed, 166 passed, 23 subtests passed | UTF-8 fixture를 CP949로 읽는 오류 |
| 1d67ade | 171 passed, 23 subtests passed | UTF-8 명시 후 전체 회귀 |
| ff2fc56 | 214 passed, 57 subtests passed, warning 1 | FastAPI 계약·HTTP 추가 후 회귀 |
| 2b8b66b | 222 passed, 67 subtests passed, warning 1 | 실제 서버 점검 CLI 추가 후 회귀 |
| 1862bbe | 224 passed, 67 subtests passed, warning 1 | 상세 중단·복귀 점검 보완 후 회귀 |
| f22e949 | 226 passed, failed subtests 2, 73 subtests passed, warning 1 | Windows .mjs가 text/plain인 MIME 오류 |
| 2216f84 | 사용자가 기존 /demo 화면 표시 확인 | MIME 타입 명시. 수정 후 전체 pytest 출력 미제공 |

`1862bbe` 실제 Uvicorn·로컬 정책 DB 20건에서 기본 후보 5건, 점검 PASS 6 / FAIL 0 / SKIP 0 / WARN 0을 확인했다. 이 결과와 기존 TestClient 의존성 경고 1개는 당시 기록이며 현재 변경의 전체 통과로 인용하지 않는다. 원본 Streamlit·수집·저장·검색·LLM 모듈은 유지했다.

## 데모와 병합

시연·실행·구현 범위는 `docs/demo/README.md`, 계획 현황은 `docs/planning/demo-mvp.md`를 따른다. 전체 회귀와 합성 정책을 이용한 실제 FastAPI·브라우저 연동 확인 후 PR #3을 main에 병합했다. 코드 97cd09a와 공개 버전 3은 이전 검증 기록이다. 현재 공개 데모와 실제 운영 서비스의 구현 범위는 구분한다.

정책 20~30개 전체 확정, PostgreSQL, LangGraph·신규 RAG, 모델 연결, 개인정보 처리 설계, 기술 평가·실사용 검증은 후속이다.


## Windows 자동 회귀 확보 (2b9eaab)

[Demo checks 실행](https://github.com/yurimakes/youth-policy-llm-recommender/actions/runs/37706147803)에서 Windows Python 3.10 전체 pytest **230 passed, 82 subtests passed, 경고 1개**, JavaScript 15개와 정적 빌드의 성공을 확인했다. 경고는 기존 Starlette TestClient의 httpx 관련 안내다. 이후 모바일 헤더 정렬과 MIME을 고정한 정적 미리보기 서버, 브라우저 회귀/캡처 도구를 추가하므로 최신 head의 결과는 별도로 확인한다.


### 첫 Chromium 시연과 문서 버튼 보완

400ea8e의 Windows 전체 pytest는 다시 230 passed, 82 subtests passed로 통과했다. Chromium은 4 passed / 2 failed였다. 두 실패는 가상 체험·실제 FastAPI 모두 상담 요약 버튼의 접근성 이름에 아이콘 문자가 포함되어 제목으로 찾을 수 없는 문제였다. 문서 도구에 명시적 aria-label을 지정하고 재검증한다. 다른 4개 시나리오와 실제 API의 수동 지역 코드 수정·공식 링크 연결은 해당 버튼 전까지 정상 진행했다. 브라우저 전체 통과나 PDF 성공으로 표시하지 않는다.


## 최종 검증·배포·병합 (97cd09a)

- Windows Python 3.10 전체 pytest: **230 passed, 82 subtests passed, 경고 1개**. HTTP 테스트 스킵 없음.
- Node 클라이언트·가상 진행: **15 passed, 실패·스킵 0**. compileall·정적 빌드 성공.
- Chromium: **6 passed (11.7s)**. 기본 흐름과 상세 중단/복귀·준비/요약, 건너뛰기, 상세 거절, 수정 후 장바구니 제외와 모름 복원, 빈 결과/오류 후 재시도, 실제 FastAPI 합성 정책 연결과 수동 지역 코드 수정·공식 링크를 확인했다.
- 상담 요약 클립보드 복사와 Chromium PDF 출력, 모바일 가로 넘침 없음, 화면 PNG 6개와 상담 PDF 1개 생성. 사람의 인쇄창에서 저장 위치 선택을 확인한 결과는 아니다.
- 공개 체험 버전 3 배포 succeeded, audience public. 배포 자산이 검증한 저장소 demo 파일과 일치한다.
- PR #3 main 병합 성공: `2e120f3701b853a7cfb0312a7fa9eeb9e7f00ce7`. 이전 검증 코드 기준 `97cd09a46e9a09883348b6c85d9734b38f44f049`.
- 원본 태그가 `23f33e7bc8e51d3e26812faeb479aae7f83ee596`을 가리키며 설명도 유지됨을 재확인했다.

[검증 실행](https://github.com/yurimakes/youth-policy-llm-recommender/actions/runs/37707391655) · [화면 PNG·상담 PDF](https://github.com/yurimakes/youth-policy-llm-recommender/actions/runs/37707391655/artifacts/11520561167)

캡처 아티팩트는 2026-10-15까지 보관된다. 캡처 파일은 그 전에 내려받아 보관한다. 실제 정책 DB 20건은 이전 사용자 실행 기록이며 현재 Chromium의 실제 API 테스트는 격리된 합성 정책으로 수행했다. 새로운 정책 전체의 최신성·실사용 효과·공개 Python API 운영을 검증한 것으로 확대하지 않는다.

## 글꼴·데모 안내 후속 변경

Pretendard Regular·SemiBold·ExtraBold 원본 WOFF2와 OFL 원문을 함께 제공한다. 제목·카드·본문의 굵기와 행간을 v0 이미지에 맞춰 조정했다. 로컬 FastAPI와 공개 정적 빌드 모두 같은 글꼴을 제공하며 MIME과 허용 자산 목록을 갱신했다. 이전 데모 안내·계획·스크립트·테스트·워크플로 경로는 일반 이름으로 정리했다. 문서 날짜·정책 확인일·과거 검증 커밋은 출처 기록으로 유지한다.

초기 로컬 검증: JavaScript 15 passed, 정적 빌드 2 passed, 관련 Python 진행·계약 85 passed / 21 skipped, compileall·정적 빌드 성공. 이 환경에는 pytest·FastAPI·httpx·Playwright가 없어 전체 pytest와 HTTP·브라우저 검증을 실행하지 못했다. 이는 코드 실패와 구분한다. 새 자산의 HTTP 응답과 실제 글꼴 로딩은 후속 PR의 `Demo checks` Windows 전체 회귀·Chromium 실행 기록을 기준으로 확인한다. 위의 230개·Chromium 6개 수치는 이전 코드 97cd09a의 결과다.


### 최신 글꼴 버전 검증·배포 (d429571)

- Windows Python 3.10: **230 passed, 86 subtests passed, 기존 경고 1개**, HTTP 스킵 없음. 새 글꼴 3개·라이선스의 명시적 MIME 응답 포함.
- JavaScript: **15 passed**, compileall·정적 빌드 성공.
- Chromium: **6 passed (15.6s)**. 실제 Pretendard 400·800 로딩, 제목 800 굵기, 기존 흐름·실제 FastAPI 합성 정책·복사·PDF·모바일 가로 넘침 확인.
- 공개 데모 **버전 4** 배포 succeeded, audience public. CSS·모듈·JSON·글꼴·라이선스 9개 자산이 검증한 저장소 파일과 일치한다.
- 아래 실행 이후에는 문서의 검증 기록·자산 목록만 추가 정리했으며 앱·글꼴·테스트 코드는 바꾸지 않았다.

[최신 검증 실행](https://github.com/yurimakes/youth-policy-llm-recommender/actions/runs/37711672670) · [글꼴 적용 화면·상담 PDF](https://github.com/yurimakes/youth-policy-llm-recommender/actions/runs/37711672670/artifacts/11522440067)

## README 서비스 화면 추가

README 상단에 상황 선택·지원 후보·신청 준비·상담 요약의 실제 Chromium 화면 4장을 2열로 배치했다. 파일은 `assets/screens/`에 보관하며, 글꼴 적용 코드 `d429571`의 성공한 자동 검증에서 생성한 가상 체험 캡처를 사용한다. 4장의 화면을 직접 확인했으며 이미지 링크와 Git blob 일치를 점검했다. 서비스 코드 변경은 없다. 공개 데모 링크는 사용자가 배포한 Vercel 주소로 갱신했다. 이번 작업에서 새 브라우저 캡처·전체 회귀·Vercel 동작 검증을 수행한 것은 아니다.

## 상담 화면 캡처의 복사 알림 제거

복사 동작 전에 알림이 숨겨져 있는지 검사하고 상담 화면을 캡처하도록 순서를 조정했다. 기존 클립보드·PDF 기능 검증은 유지했다. [Demo checks 실행](https://github.com/yurimakes/youth-policy-llm-recommender/actions/runs/37727689846)이 성공했으며, 새 PNG를 직접 확인해 README의 상담 화면 이미지를 교체했다. 서비스 런타임 코드는 변경하지 않았다.
