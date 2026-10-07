# 지원장바구니 개발 현황

- 기준일: 2026-10-07
- 브랜치: `feature/intake-api`
- 이전 작업: PR #2 main 병합 완료 (`d0d86f2`)
- 원본 MVP: `v0.1-mvp` → `23f33e7`
- 단계: 1차 회귀 검증 완료 후 API 계약·백엔드 연결 구현

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

- 데모 UI는 팀원 담당이다. FastAPI 코드를 추가했으나 실제 HTTP 실행 검증은 대기 중이다.
- 카드·선호에 따른 정책 관련도 순위는 미구현이다. 선호는 사실과 분리해 저장만 하며 자격에 사용하지 않는다.
- 광역·전국 지역 기준, 복합 소득·학력·예외 조건은 기관 확인으로 남긴다.
- 추가 조건이 기록되지 않은 것을 제한 없음으로 해석하지 않아 전체 정책 요약은 보수적으로 확인 필요를 유지한다.
- 저장한 신청 기간은 요청 날짜로 재평가하지만 최신 공고를 다시 조회하는 기능은 아직 없다.
- PostgreSQL·LangGraph·pgvector/BM25·신규 RAG·준비 문서·배포·실사용 검증은 후속 단계다.
- 초기 정책 20~30개 목록, 모델/API, 개인정보 전달·저장·삭제, 호스팅은 미정이다.
- 최신 공유본의 청년 20명 실사용 테스트는 보류다. 평가 100건 이상·근거 일치율 95% 이상은 향후 목표다.

과거 자동 테스트 122개·실제 API 20건은 2026-07 기록이며 이번 검증과 구분한다.

## 2차: UI 분담과 API 연결

사용자 지시로 팀원이 데모 UI를 담당하며 이 브랜치에는 프론트엔드 화면을 추가하지 않았다.

- `api.py`, `api_app.py`: 시작·상태 전환·health/readiness FastAPI 코드
- `api_schemas.py`, `intake_contract.py`: 구조화 입력·응답, 상태·이력 일관성, 서버 후보·날짜 재평가
- `api_config.py`, `policy_repository.py`: 명시적 CORS, 한국 날짜, SQLite 읽기 전용 조회
- `docs/api/intake-v1.md`, `docs/api/schemas/`: UI 연결 규격과 실제 Pydantic 모델에서 생성한 JSON Schema
- `requirements-api.txt`: 기존 Streamlit과 분리한 API 추가 의존성 목록

서버는 사용자 진행 상태를 저장하지 않고 POST 본문의 상태를 검증·갱신한다. 로그인·인증·브라우저 영구 저장·외부 AI 호출은 이 단계에 포함하지 않는다. 클라이언트가 보낸 후보·판정·날짜 필드는 받지 않고 현재 서버 정책으로 다시 평가한다.

검증은 기존 신규 로직 49개, API 계약·저장 경계 26개, 실제 Pydantic 스키마 6개를 포함한다. 설치된 런타임 Pydantic 2.13.5를 실제로 사용했다. FastAPI·HTTPX는 패키지 설치 차단으로 이용할 수 없어 HTTP 테스트 11개를 실행하지 못했다. 전체 대상 92개 중 성공 81개·스킵 11개이며 스킵을 통과로 표시하지 않는다. api.py/app.py/src/scripts/tests의 compileall과 JSON Schema 생성·JSON 읽기도 성공했다.

2차 코드에 대한 Windows 전체 pytest와 실제 서버 기동은 아직 확인 전이다. 1차의 171 passed 기록은 2차 코드의 전체 회귀 통과 결과로 사용하지 않는다. API 관련 테스트는 API 의존성이 없으면 명시적으로 스킵되므로 requirements-api 설치 후 HTTP 테스트가 실행됐는지 확인해야 한다.
