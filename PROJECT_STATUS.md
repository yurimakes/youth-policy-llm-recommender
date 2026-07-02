# 청년 맞춤 정책 추천 개발 현황

## 1. 현재 상태

- 기준일: 2026-07-02
- 저장소: `github.com/choiyuri-dev/youth-policy-llm-recommender`
- 현재 단계: 로컬 MVP 핵심 기능 구현 및 검증 완료
- 사용자 화면 명칭: **청년 맞춤 정책 추천**
- 전체 테스트: `122 passed`
- GitHub `main` 브랜치 반영 완료

## 2. 완료 사항

### 2.1 실제 정책 데이터 수집

- 온통청년 청년정책 API 실제 호출 성공
- 2페이지, 총 20건 수집
- 페이지별 raw JSON과 메타데이터 저장
- 실제 응답의 정책 목록을 `PolicyRecord`로 변환
- `sbizCd`와 `sBizCd` 필드 하위 호환 처리
- API 키와 전체 요청 URL은 출력하지 않음

### 2.2 SQLite 파이프라인

- snapshot JSON → `PolicyRecord` → SQLite 적재 → SQLite 재조회 흐름 구현
- 정책 20건 저장 및 재조회 확인
- 정책 ID 기준 upsert로 동일 정책 중복 증가 방지
- SQLite 조회 결과를 규칙 평가 서비스에 연결
- raw 데이터와 SQLite 산출물은 Git에서 제외

### 2.3 규칙 기반 평가

- 나이, 지역 코드, 취업 상태를 입력으로 사용
- 시·도 및 시·군·구 선택값을 실제 5자리 `region_code`로 변환
- `MATCH`, `UNKNOWN`, `NO_MATCH`로 결과 분류
- 판정 이유 보존
- 불명확한 소득 및 자연어 조건은 자동 탈락시키지 않고 `UNKNOWN` 처리

### 2.4 Streamlit UI

- 단일 Streamlit 앱 구현
- 나이 입력
- 시·도 / 시·군·구 2단계 지역 선택
- 취업 상태 입력
- 자연어 관심사 입력
- 규칙 평가 요약 카드
- 정책 상세 카드와 공식 출처 표시
- 최종 신청 자격 확인 안내 표시

### 2.5 FAISS 검색

- 규칙 결과 중 `MATCH`, `UNKNOWN` 정책만 검색 후보로 사용
- 정책 `embedding_text` 또는 공식 필드 결합 텍스트 사용
- OpenAI 임베딩 생성
- 벡터 정규화 후 FAISS `IndexFlatIP` 검색
- Top-5 정책 반환
- 벡터 위치와 `policy_id` 매핑 유지

### 2.6 OpenAI 추천 설명

- 검색된 Top-5 공식 정책 정보만 프롬프트에 포함
- 추천 이유, 일치 조건, 확인 조건, 신청 기간, 공식 출처 설명
- 누락 정보는 `확인 필요`로 표시
- 최종 신청 자격을 확정하지 않음
- 설명 생성 실패 시 규칙 기반 결과와 검색 결과를 유지

## 3. 현재 처리 흐름

```text
온통청년 공식 API
        ↓
raw snapshot 저장
        ↓
PolicyRecord 변환
        ↓
SQLite 적재 및 조회
        ↓
사용자 조건 규칙 평가
        ↓
MATCH / UNKNOWN 후보 유지
        ↓
OpenAI 임베딩
        ↓
FAISS Top-5 검색
        ↓
공식 데이터 기반 OpenAI 설명
        ↓
Streamlit 결과 표시
```

## 4. 검증 결과

### 자동 검증

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

결과:

```text
122 passed
```

### 구문 검증

```powershell
.\.venv\Scripts\python.exe -m compileall app.py src
```

결과: 성공

### 수동 실행 검증

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

확인한 입력 예시:

- 나이: 24
- 지역: 서울특별시 / 강남구
- 취업 상태: 미취업자
- 관심사: 자격증 시험 비용과 월세 지원

확인한 결과:

- 규칙 기반 정책 평가 표시
- FAISS 관심사 기반 Top-5 검색 표시
- 실제 OpenAI 추천 설명 표시
- 공식 출처와 확인 필요 안내 표시

## 5. 주요 변경 파일

- `app.py`
- `src/career_catch/codebook.py`
- `src/career_catch/ui_service.py`
- `src/career_catch/retrieval.py`
- `src/career_catch/llm_service.py`
- `tests/test_ui_service.py`
- `tests/test_retrieval.py`
- `tests/test_llm_service.py`
- `assets/`

## 6. 주요 Git 반영 이력

- `d124ea2` — 여러 페이지 온통청년 수집
- `f159d91` — Streamlit 정책 추천 UI
- `bacefcc` — FAISS 검색 및 OpenAI 설명

현재 로컬 브랜치와 원격 `main`은 동기화된 상태로 확인했다.

## 7. 현재 한계

- 실제 정책 데이터 검증 범위는 20건이다.
- 소득 조건은 단위와 개인·가구 기준이 완전히 구조화되지 않았다.
- 복잡한 자유 텍스트 자격 조건은 자동 확정하지 않는다.
- 새 환경에서는 Git에서 제외된 raw 데이터와 SQLite 파일을 다시 생성해야 한다.
- OpenAI API 키와 사용 가능한 잔액이 필요하다.
- Streamlit Community Cloud 배포는 아직 완료되지 않았다.

## 8. 남은 작업

- 최종 제출용 실행 화면 캡처 정리
- 결과보고서 작성
- 문서와 화면 문구 최종 점검
- 필요 시 Streamlit Community Cloud 배포
- 문서 변경분 최종 커밋 및 푸시

## 9. 개발 이력

### 2026-06-29

- 정책 표준 모델, 코드북, 예시 JSON 파서, SQLite 저장소 구현
- 규칙 기반 단건 및 일괄 평가 구현
- 당시 전체 테스트 `81 passed`

### 2026-07-01

- 실제 API 호출 및 snapshot 파이프라인 연결
- SQLite 적재·재조회와 중복 방지 확인
- 여러 페이지 수집으로 20건 확보
- Streamlit UI 구현

### 2026-07-02

- FAISS Top-5 검색 구현
- OpenAI 추천 설명 구현
- 전체 테스트 `122 passed`
- 로컬 통합 실행 검증 및 GitHub 반영 완료
