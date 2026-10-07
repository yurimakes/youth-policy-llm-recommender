# 지원장바구니 작업 현황

## 기획 기준 전환

- [x] 기존 MVP 태그 보존 확인
- [x] 서비스명 지원장바구니 및 최신 팀 공유본 반영
- [x] 과거 MVP 명세·원본 링크 보존
- [x] README / PROJECT_SPEC / AGENTS 개발 기준 갱신

## 첫 코드 구현과 검증

- [x] 카드·사실·선호·모름·건너뛰기 상태
- [x] 상세 전환 선택·거절·중단·복귀와 답변 수정
- [x] 후보별 필요한 질문과 중복 방지
- [x] 네 가지 조건 상태, 날짜 재평가와 다음 행동
- [x] 신규 단위·통합 사례 테스트 49개 및 compileall
- [x] 기존 SQLite 읽기 전용 개발용 CLI와 흐름 테스트
- [x] Windows Python 3.10 전체 pytest 회귀 검증: 171 passed, 23 subtests passed (2026-10-07 사용자 실행)

## 후속 개발

- [x] API 연결 계약·JSON Schema 정리
- [x] FastAPI 코드와 stateless 상태 전환·입출력 검증 추가
- [x] Python 계약·저장 경계 26개와 Pydantic 스키마 6개 검증
- [x] API 커밋 ff2fc56 Windows 전체 pytest: 214 passed, 57 subtests passed, 경고 1개 (HTTP 테스트 11개 포함)
- [x] 실행 중인 로컬 서버 점검 CLI와 테스트 8개 추가: 결과별 통과·실패·스킵 구분
- [x] 커밋 2b8b66b Windows 전체 pytest: 222 passed, 67 subtests passed, 경고 1개
- [x] 실제 Uvicorn·정책 DB 20건 점검: PASS 5 / SKIP 1 / FAIL 0 / WARN 0, 기본 후보 5건
- [x] 상세 중단·복귀 점검의 첫 후보·기존 건너뛰기 의존 제거 및 회귀 사례 2개 추가
- [x] 커밋 1862bbe Windows 전체 pytest: 224 passed, 67 subtests passed, 경고 1개
- [x] 보완된 실제 서버 점검: 상세 중단·복귀 포함 PASS 6 / FAIL 0 / SKIP 0 / WARN 0
- [x] 사용자 담당 변경에 따라 제출용 시작·질문·결과 3개 화면 구현
- [x] 세로 선택 카드·선택 표시·다음 버튼, 모름·건너뛰기·답변 수정 연결
- [x] 정책별 조건·공식 링크·선택적 상세 거절·중단·복귀·다음 확인 항목 연결
- [x] FastAPI에서 `/demo`와 로컬 정적 파일 제공, 기존 API 계약 재사용
- [x] JavaScript 상태 관리 테스트 7개와 실제 순수 진행 계약의 참조 HTTP 연결 확인
- [ ] UI 추가 후 Windows 전체 pytest 및 신규 HTTP 테스트 2개 확인
- [ ] 실제 `/demo` 브라우저 배치·카드 선택/다음·답변 수정·상세·오류 복구 확인
- [ ] 확인 완료 후 PR #3 검토·main 병합 및 제출 데모 고정
- [ ] 카드·선호 기반 정책 관련도 순위와 지원 방향 연결
- [ ] 서울·전국 주거·취업 공식 정책 20~30개 목록 확정
- [ ] PostgreSQL / 버전·근거·필요 서류 구조화
- [ ] LangGraph 도구 연결 및 모델 실패 폴백
- [ ] pgvector·BM25 / RAG 효과 평가
- [ ] 체크리스트·발급 안내·상담 요약·문의 초안
- [ ] 기술 평가 100건 이상과 정답·지표 정의
- [ ] 실제 청년 20명 검증 (현재 보류)
- [ ] 개인정보 자문·처리 설계와 배포·운영 결정
