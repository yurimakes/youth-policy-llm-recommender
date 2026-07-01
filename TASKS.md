# TASKS.md

## 현재 작업 (2026-07-01)

* 작업: 온통청년 API 여러 페이지 수집 기능 구현
* 상태: API 수집·파서 연결·SQLite 파이프라인·규칙 평가 연결 완료, 여러 페이지 수집 대기
* 초기 안전 검증 범위: `pageSize=10`, `max_pages=2`, 정책 최대 20건

## 현재 완료 사항 (2026-07-01)

* [x] GitHub 저장소 `github.com/choiyuri-dev/youth-policy-llm-recommender` 기준 정리
* [x] 온통청년 OPEN API 인증키 승인 완료
* [x] 최신 엔드포인트 `https://www.youthcenter.go.kr/go/ythip/getPlcy` 반영
* [x] 최신 요청 파라미터 `apiKeyNm`, `pageNum`, `pageSize`, `pageType`, `rtnType` 반영
* [x] 실제 API JSON 호출 성공
* [x] 실제 응답 전체 정책 수 `2,633`건 확인
* [x] 1페이지 정책 10건 원본 JSON 및 메타데이터 저장 성공
* [x] 실제 응답 구조 `result.youthPolicyList` 확인
* [x] 실제 정책 10건 `PolicyRecord` 변환 성공
* [x] `sbizCd` 및 `sBizCd` 하위 호환 처리
* [x] API 수집 및 실제 응답 파서 연결 완료
* [x] snapshot JSON → `PolicyRecord` → SQLite 적재 → SQLite 재조회 파이프라인 구현
* [x] 실제 정책 입력 10건, SQLite 저장·재조회 10건 확인
* [x] 동일 snapshot 재적재 시 중복 행 증가 방지 기능 구현
* [x] SQLite 조회 결과를 `evaluate_policies()`에 연결 완료
* [x] 실제 검증 프로필 나이 24세, 지역 코드 `11680`, 취업 상태 `미취업자`로 평가
* [x] 실제 평가 결과 `MATCH` 2건, `UNKNOWN` 1건, `NO_MATCH` 7건, 총 10건 확인
* [x] 전체 자동 테스트 `102 passed` 확인
* [x] `python compileall` 성공 확인
* [x] API 수집·파서 연결 커밋과 SQLite 파이프라인 커밋 GitHub `main` 푸시 완료
* [x] 실제 raw 데이터 파일은 Git에 포함하지 않음
* [x] `data/raw`, `data/processed`, SQLite 산출물 `.gitignore` 제외

## 남은 작업 (2026-07-01)

* [ ] 여러 페이지 수집
* [ ] 전체 또는 필요한 범위 정책 적재
* [ ] Streamlit UI
* [ ] FAISS 검색
* [ ] LLM 설명
* [ ] 배포

## 날짜별 검증 기록

### 2026-07-01

* `.\.venv\Scripts\python.exe -m pytest tests/test_ontong_parser.py -q`: 13 passed
* 실제 검증 프로필: 나이 24세, 지역 코드 `11680`, 취업 상태 `미취업자`
* 실제 평가 결과: `MATCH` 2건, `UNKNOWN` 1건, `NO_MATCH` 7건, 총 10건
* `.\.venv\Scripts\python.exe -m pytest -q`: 102 passed
* `.\.venv\Scripts\python.exe -m compileall src scripts`: 성공

### 2026-06-29

2026-06-29 당시에는 실제 API 호출 전 단계였고, 공식 예시 JSON과 최소 저장·파서 기능을 중심으로 검증했다.

## 개발 이력 — 2026-06-29

## 개발 이력 — 2026-06-29 당시 상태

이 저장소는 현재 온통청년 공식 예시 JSON을 canonical `PolicyRecord` 목록으로 변환하는 최소 파서 구현 후 사용자 검토 단계입니다.

- 저장소 루트: `career-catch-4/`
- Python 버전: 3.10.11 가상환경 기준
- 주 데이터 소스: 온통청년 청년정책 API
- 실제 API 네트워크 호출: 인증키 승인 전이라 아직 수행하지 않음
- 개인 인증키 검증: 아직 수행하지 않음
- Streamlit 애플리케이션 UI 구현: 아직 시작하지 않음
- 실제 API 수집 데이터, SQLite 데이터베이스, FAISS 산출물: 아직 생성하지 않음
- 배포: 아직 수행하지 않음

MVP는 단일 Streamlit 애플리케이션으로 계획합니다.

- Python 3.10
- Streamlit
- Requests
- Pandas
- SQLite
- FAISS
- OpenAI API
- pytest
- Streamlit Community Cloud

raw 데이터, processed 데이터, vector artifacts는 추적 가능하고 재현 가능하게 관리해야 합니다.

## 개발 이력 — 2026-06-29 당시 작업

**작업:** SQLite 정책 저장 계층 구현 및 사용자 검토

**상태:** 구현과 테스트 완료, 사용자 검토 대기

이번 작업에서는 공식 예시 JSON을 파싱한 `PolicyRecord` 10건을 SQLite에 저장하고 조회하는 최소 저장 계층을 구현했습니다. upsert, 단건 조회, 전체 조회, 행 수 확인, 날짜 및 datetime 타입 복원, `ApplicationStatus` 타입 복원을 구현했습니다. 테스트에서는 pytest `tmp_path`만 사용했으며 저장소 내부에 실제 SQLite DB 파일은 생성하지 않았습니다. 실제 API 네트워크 호출과 API 키는 사용하지 않았습니다.

## 3. 할 일

- [ ] 인증키 승인 후 실제 API 호출 검증
- [ ] 실제 API 응답 저장 및 공식 예시와 비교
- [ ] API 필드 매핑 보완
- [ ] 조건 필터링
- [ ] FAISS 검색
- [ ] OpenAI 설명 생성
- [ ] Streamlit UI
- [ ] 배포

## 4. 완료된 작업

- [x] 프로젝트 목표, MVP 범위 및 기술 스택 확정
- [x] 프로젝트 문서 AGENTS.md, PROJECT_SPEC.md, README.md, 초기 TASKS.md 작성
- [x] Git 저장소 초기화, 가상환경 생성 및 초기 개발 설정 파일 구성
- [x] 개발 환경과 직접 의존성 설치 및 import 검증
- [x] canonical `PolicyRecord` 모델 구현
- [x] `PolicyRecord` 단위 테스트 8개 통과
- [x] 온통청년 API 코드북 구현
- [x] 공식 예시 JSON fixture 10건 저장
- [x] 온통청년 공식 예시 JSON 파서 구현
- [x] 온통청년 파서 테스트 10개 통과
- [x] SQLite 정책 저장 계층 구현
- [x] SQLite 저장 계층 테스트 1개 통과
- [x] 현재 전체 테스트 30개 통과

## 5. 검증 기록

- Python 3.10.11 가상환경에서 직접 의존성 설치와 핵심 패키지 import 및 버전 확인 완료
- `.\.venv\Scripts\python.exe -m pytest tests/test_models.py -q`: 8 passed
- `.\.venv\Scripts\python.exe -m pytest tests/test_codebook.py -q`: 11 passed
- `.\.venv\Scripts\python.exe -m pytest tests/test_ontong_parser.py -q`: 10 passed
- `.\.venv\Scripts\python.exe -m pytest tests/test_sqlite_store.py -q`: 1 passed
- `.\.venv\Scripts\python.exe -m pytest -q`: 30 passed

검증은 외부 네트워크나 API 키 없이 수행했습니다. 실제 API 네트워크 호출과 개인 인증키 검증은 아직 수행하지 않았습니다.

## 6. MVP 제외 및 향후 확장 항목

다음 항목은 초기 MVP에서 제외하며, 명시적 승인 후 향후 확장으로만 검토합니다.

- FastAPI 서버 분리
- MySQL 또는 PostgreSQL
- ChromaDB
- Selenium 기반 대규모 크롤링
- 여러 정책 제공처의 동시 통합
- 사용자 계정 또는 로그인
- 개인정보 프로필 저장
- 정책 신청 제출 또는 자동 신청
- 결제 기능
- 관리자 대시보드
- 네이티브 모바일 애플리케이션

## 7. 정책 추천 안전 문구

추천 결과는 최종 신청 자격을 확정하지 않습니다.

필수 안내 문구:

> 지원 가능성이 높은 정책입니다. 최종 신청 자격과 세부 조건은 반드시 공식 공고문에서 확인해야 합니다.


## 현재 개발 진행 상황 — 2026-06-29 오전 1:46

### 완료

* [x] 프로젝트 개발 환경 및 패키지 구조 구성
* [x] `PolicyRecord` 정책 데이터 모델 구현
* [x] 온통청년 코드북 구현
* [x] 공식 예시 JSON 10건 저장 및 파싱
* [x] SQLite 정책 저장·조회·갱신 기능 구현
* [x] 신청 상태 기반 정책 판정
* [x] 연령 조건 기반 정책 판정
* [x] 지역 조건 기반 정책 판정
* [x] 취업 상태 기반 정책 판정
* [x] 소득 조건 안전 판정
* [x] `MATCH`, `UNKNOWN`, `NO_MATCH` 결과 구조 구현
* [x] 여러 정책 일괄 평가 및 후보 그룹 분류
* [x] SQLite 조회 결과와 일괄 평가 기능 연결
* [x] 전체 자동 테스트 81개 통과
* [x] GitHub 저장소 생성 및 `main` 브랜치 푸시
* [x] 개발 현황 문서 `PROJECT_STATUS.md` 작성

### 다음 작업

* [ ] Streamlit 규칙 기반 데모 UI 구현

### Streamlit 데모 UI 요구사항

* 사용자 나이 입력
* 사용자 지역 코드 입력
* 사용자 취업 상태 선택
* 예시 정책 데이터 10건 로딩
* 기존 `evaluate_policies()` 호출
* 추천 가능 정책 표시
* 추가 확인 필요 정책 표시
* 조건 불일치 정책 표시
* 정책별 규칙 기반 판정 이유 표시
* 실제 LLM 기능과 혼동되지 않도록 현재 결과를 규칙 기반 MVP로 명시

### 이후 예정 작업

* [ ] 실제 온통청년 API 호출 및 응답 검증
* [ ] 실제 정책 데이터 SQLite 적재
* [ ] 벡터 유사도 검색 구현
* [ ] LLM 추천 이유 및 신청 안내 생성
* [ ] Streamlit 통합 화면 개선
* [ ] 배포 및 최종 테스트
* [ ] README 및 최종 보고서 정리
