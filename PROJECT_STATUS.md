# 지원장바구니 개발 현황

- 갱신일: 2026-10-08, 한국 시간
- 개발 브랜치: `feature/intake-api`, PR #3 draft
- main: 1차 고도화 PR #2 병합 완료 (`d0d86f2`)
- 원본: `v0.1-mvp` → `23f33e7`, 변경 없음
- 공개 제출 체험: https://youth-support-demo-20261008.cyr3918.chatgpt.site
- 현재 단계: 확정 UI와 공개 목데이터 체험 배포 완료. 최신 전체 Windows 회귀·브라우저 수동 시연 확인 후 main 병합.

## 현재 구현과 경계

| 구간 | 구현 | 한계 |
|---|---|---|
| 진행·조건 | Python 카드·질문·상세·수정, 조건 4상태, 명확한 제외, 날짜 재평가 | 복합 소득·학력·예외는 기관 확인 |
| 실제 API | stateless FastAPI, SQLite 읽기 전용, 상태·전환·스키마 검증 | 공개 Python 서버 운영·인증·영구 저장 미구현 |
| 확정 UI | 상황·관심·기초·방향·상세 제안·상세·갱신·준비·상담 요약 | 최신 브라우저 수동 시연 대기, React 구현 아님 |
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
| 최신 전체 pytest·HTTP·브라우저 | 대기 | 현재 환경에 pytest/FastAPI/httpx와 로컬 브라우저 런타임 없음 |

실행 명령:

```bash
node --test tests/test_demo_client.mjs tests/test_submission_demo.mjs
node --check demo/app.mjs
PYTHONPATH="$CODEX_PRIMARY_RUNTIME_ROOT/dependencies/python/lib/python3.12/site-packages" .venv/bin/python -m unittest discover -s tests -p 'test_intake*.py'
.venv/bin/python -m unittest discover -s tests -p 'test_submission_build.py'
.venv/bin/python -m compileall -q api.py app.py src scripts tests
.venv/bin/python scripts/build_submission_demo.py --output <정적 출력 폴더>
```

자동 검증에서는 모름·건너뛰기, 상세 거절·중단·복귀, 명시적 취업·나이 수정에 따른 제외와 모름으로 복원, 선호와 자격 분리, 후보 없음·데이터 오류 후 이전 답변 유지와 재시도를 확인했다. 실제 브라우저 클릭·레이아웃·클립보드·PDF 인쇄의 수동 실행 결과는 아니다. 정적 HTML에는 연결된 자산이 존재하고 실제 API HTML은 API 모드를 유지한다.

Windows 재발 방지를 위해 모듈 3개와 JSON의 MIME을 직접 지정하고 HTTP 사례를 추가했다. Windows Python 3.10의 전체 pytest와 Node·정적 빌드를 수행하는 `Submission checks` 워크플로를 추가한다. 설정 존재와 성공한 실행은 구분하며, 실행 결과가 확보될 때 기록을 갱신한다.

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

## 제출과 병합

시연·실행·구현 범위는 `docs/submission/2026-10-08-demo.md`, 계획 현황은 `docs/planning/submission-mvp-2026-10-08.md`를 따른다. 제출 시각 확정 후 2~3시간 전 기능 동결, 제출처 요구 캡처·파일과 링크 확인, 최신 전체 회귀·핵심 실제 연동 확인 후 PR #3 main 병합과 제출 커밋 고정을 진행한다. 그 전에는 공개 체험 링크를 제공하되 실제 운영 서비스 완성으로 설명하지 않는다.

정책 20~30개 전체 확정, PostgreSQL, LangGraph·신규 RAG, 모델 연결, 개인정보 처리 설계, 기술 평가·실사용 검증은 후속이다.
