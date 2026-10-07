# 지원장바구니 개발 현황

- 기준일: 2026-10-07
- 브랜치: `docs/service-redesign`
- 원본 MVP: `v0.1-mvp` → `23f33e7`
- 단계: 기획 전환과 첫 Python 핵심 로직 구현

## 이번에 구현한 내용

| 파일 | 변경 내용 |
|---|---|
| `src/youth_policy/intake.py` | 상황/목표 카드, 모름·건너뛰기, 사실·선호 분리, 상세 선택·거절·중단·복귀와 답변 수정 |
| `src/youth_policy/conditions.py` | 조건별 네 가지 상태와 원인, 요청 날짜의 신청 기간 재평가, 명확한 제외와 불확실성 유지 |
| `src/youth_policy/intake_service.py` | 필요한 기초/상세 질문, 현재 후보의 조건 갱신, 공식 근거와 다음 확인 행동 |
| `scripts/preview_intake.py` | 기존 SQLite를 읽기 전용으로 연결하는 개발용 터미널 흐름 |
| `tests/test_intake*.py` | 신규 단위·통합 테스트 49개 |

기존 `app.py`, 데이터 수집·저장·검색·LLM 모듈과 과거 테스트는 수정하지 않았다. `main`과 원본 태그는 그대로 두고 고도화 브랜치에 일반 커밋을 추가한다. 최신 공유본 원문과 과거 명세, 첨부 로고 미리보기를 함께 기록했다.

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

기존 공식 예시 fixture → 기존 파서 → 임시 SQLite → 신규 안내 흐름 통합을 실행했다. 로컬 CLI의 상세 거절·추가 답변에 따른 후보 제외도 입력을 모의해 실행했다. 실제 사용자 답변 저장과 외부 API 호출은 하지 않았다. Windows 실행은 미검증이다.

`python -m pytest`는 pytest 패키지가 없어 실행되지 않았다. Git 직접 clone과 npm/pip 패키지 설치가 차단돼 있어 고정 커밋의 파일을 GitHub 연결로 가져와 검증했다. 기존 전체 122개 회귀 테스트는 사용자의 기존 설치 환경에서 실행해야 한다. 이번 49개 결과를 전체 회귀 통과로 해석하지 않는다.

## 구현 한계와 다음 단계

- React·TypeScript 카드 화면과 FastAPI는 아직 미구현이다. 카드 선택은 핵심 로직·CLI에 구현했다.
- 카드·선호에 따른 정책 관련도 순위는 미구현이다. 선호는 사실과 분리해 저장만 하며 자격에 사용하지 않는다.
- 광역·전국 지역 기준, 복합 소득·학력·예외 조건은 기관 확인으로 남긴다.
- 추가 조건이 기록되지 않은 것을 제한 없음으로 해석하지 않아 전체 정책 요약은 보수적으로 확인 필요를 유지한다.
- 저장한 신청 기간은 요청 날짜로 재평가하지만 최신 공고를 다시 조회하는 기능은 아직 없다.
- PostgreSQL·LangGraph·pgvector/BM25·신규 RAG·준비 문서·배포·실사용 검증은 후속 단계다.
- 초기 정책 20~30개 목록, 모델/API, 개인정보 전달·저장·삭제, 호스팅은 미정이다.
- 최신 공유본의 청년 20명 실사용 테스트는 보류다. 평가 100건 이상·근거 일치율 95% 이상은 향후 목표다.

과거 자동 테스트 122개·실제 API 20건은 2026-07 기록이며 이번 검증과 구분한다.
