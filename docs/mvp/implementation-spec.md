# 보존 기록: 2026-07 MVP 명세

이 문서는 과거 구현 기록이다. 현재 개발 기준은 루트 PROJECT_SPEC.md를 따른다.

# 청년 맞춤 정책 추천 프로젝트 명세서

## 1. 문서 기준

- 기준일: 2026-07-02
- 저장소: `github.com/yurimakes/youth-policy-llm-recommender`
- 사용자 화면 명칭: **청년 맞춤 정책 추천**
- 현재 단계: 로컬 MVP 핵심 기능 구현 및 검증 완료
- 전체 자동 테스트: `122 passed`
- 로컬 구문 검증: `python -m compileall app.py src` 성공
- 로컬 Streamlit 실행 및 실제 OpenAI 설명 생성 확인

이 문서는 제품 요구사항, 기술 구조, 안전 원칙, 구현 범위와 현재 한계를 정의한다.

## 2. 프로젝트 개요

청년정책은 중앙정부와 지방자치단체, 여러 공공기관에 분산되어 있으며 정책마다 연령, 지역, 취업 상태, 소득, 신청 기간 등의 조건이 다르다. 사용자는 여러 공고문을 직접 비교해야 하고, 자연어로 작성된 자격 조건 때문에 자신에게 맞는 정책을 찾기 어렵다.

본 프로젝트는 공식 청년정책 데이터를 표준화한 뒤 사용자 조건을 규칙 기반으로 평가하고, 자연어 관심사를 반영해 관련 정책을 검색하며, 검색된 공식 정보만 바탕으로 추천 이유를 설명하는 웹서비스를 구축한다.

이 서비스는 정책 탐색과 정보 확인을 돕는 보조 도구이며 법적·행정적 신청 자격을 최종 확정하거나 사용자를 대신해 신청을 수행하지 않는다.

## 3. 서비스 목표

1. 공식 청년정책 데이터를 공통 구조로 정규화한다.
2. 나이, 지역, 취업 상태 등 명확한 조건을 규칙 기반으로 판정한다.
3. 불명확한 조건은 임의로 추측하지 않고 `UNKNOWN`으로 유지한다.
4. 명확한 `NO_MATCH` 정책을 제외하고 후보를 구성한다.
5. 자연어 관심사를 OpenAI 임베딩으로 변환하고 FAISS로 관련 정책을 검색한다.
6. 검색된 공식 정책 정보만 사용해 OpenAI 추천 설명을 생성한다.
7. 공식 출처와 최종 확인 필요 안내를 함께 표시한다.

## 4. 현재 구현 범위

### 4.1 데이터 수집 및 저장

- 온통청년 청년정책 API 실제 호출
- `pageSize=10`, `max_pages=2` 기준 2페이지, 총 20건 수집
- 페이지별 raw JSON과 메타데이터 분리 저장
- `PolicyRecord` 표준 모델 변환
- SQLite 정책 20건 적재 및 재조회
- 정책 ID 기준 upsert로 중복 증가 방지
- 실제 API 키, raw 파일, SQLite 파일은 Git에서 제외

### 4.2 규칙 기반 평가

- 나이 입력
- 시·도 및 시·군·구 선택
- 취업 상태 입력
- 실제 5자리 `region_code` 기반 지역 판정
- `MATCH`, `UNKNOWN`, `NO_MATCH` 3단계 결과
- 정책별 판정 이유 보존
- `MATCH`, `UNKNOWN`, `NO_MATCH` 개수 요약

### 4.3 관심사 기반 검색

- 자연어 관심사 입력
- `MATCH`, `UNKNOWN` 정책만 검색 후보로 사용
- 기존 `embedding_text` 우선 사용
- 값이 없으면 공식 정책 필드를 결합해 임베딩 텍스트 생성
- OpenAI 임베딩 모델 기본값 `text-embedding-3-small`
- L2 정규화 후 FAISS `IndexFlatIP` 검색
- Top-5 반환
- FAISS 벡터 위치와 `policy_id` 매핑 유지

### 4.4 생성형 설명

- 검색된 Top-5 정책만 LLM 문맥으로 전달
- 추천 이유
- 사용자 조건과 일치하는 점
- 확인이 필요한 조건
- 신청 기간 및 공식 출처 안내
- 정책 데이터에 없는 내용은 `확인 필요`로 표시
- 최종 자격을 확정하는 표현 금지
- AI 호출 실패 시 규칙 기반 결과와 검색 결과 유지

### 4.5 Streamlit UI

- 밝은 파란색·흰색 중심 단일 페이지 UI
- 나이, 시·도, 시·군·구, 취업 상태, 자연어 관심사 입력
- 규칙 기반 평가 요약 카드
- AI 추천 설명 영역
- 관심사 기반 Top-5 정책 카드
- 공식 출처 링크
- 최종 자격 확인 안내

## 5. MVP 제외 범위

초기 MVP에서는 다음 기능을 제외한다.

- FastAPI 서버 분리
- MySQL 또는 PostgreSQL
- ChromaDB
- Selenium 기반 대규모 크롤링
- 여러 정책 제공처 동시 통합
- 사용자 계정과 로그인
- 개인정보 프로필 영구 저장
- 정책 신청 자동 제출
- 결제 기능
- 관리자 대시보드
- 네이티브 모바일 애플리케이션

## 6. 기술 스택

| 영역 | 기술 |
|---|---|
| 언어 | Python 3.10 |
| 웹 UI | Streamlit |
| HTTP 통신 | Requests |
| 데이터 처리 | Pandas |
| 구조화 저장소 | JSON, SQLite |
| 규칙 판정 | Python |
| 벡터 검색 | FAISS |
| 임베딩 | OpenAI API |
| 설명 생성 | 환경 변수로 지정한 OpenAI 채팅 모델 |
| 테스트 | pytest |
| 배포 목표 | Streamlit Community Cloud |
| 버전 관리 | Git, GitHub |

## 7. 전체 처리 흐름

```text
온통청년 공식 API
        ↓
페이지별 raw snapshot 보존
        ↓
PolicyRecord 표준 변환
        ↓
SQLite 적재 및 재조회
        ↓
사용자 조건 입력
        ↓
MATCH / UNKNOWN / NO_MATCH 규칙 평가
        ↓
MATCH + UNKNOWN 후보 구성
        ↓
OpenAI 임베딩 생성
        ↓
FAISS Top-5 검색
        ↓
검색된 공식 정책만 LLM에 전달
        ↓
추천 이유 및 확인사항 생성
        ↓
Streamlit 결과 화면
```

## 8. 정책 데이터 모델

주요 canonical 필드는 다음과 같다.

- `policy_id`
- `policy_name`
- `category`
- `summary`
- `region_code`
- `region_name`
- `age_min`
- `age_max`
- `income_condition`
- `employment_status`
- `education_status`
- `application_start`
- `application_end`
- `application_status`
- `eligibility_text`
- `benefit_text`
- `application_method`
- `required_documents`
- `contact`
- `source_name`
- `source_url`
- `last_verified_at`
- `embedding_text`

공식 API에서 제공하지 않는 값은 임의로 생성하지 않는다. 누락되거나 해석하기 어려운 값은 `None` 또는 확인 필요 상태로 유지한다.

## 9. 규칙 기반 판정 원칙

### 9.1 판정 상태

| 상태 | 의미 |
|---|---|
| `MATCH` | 현재 구조화 데이터상 사용자 조건과 일치 |
| `UNKNOWN` | 데이터 누락, 자유 텍스트 또는 추가 확인 필요 |
| `NO_MATCH` | 구조화된 필드에서 명확한 불일치 |

최종 우선순위는 다음과 같다.

```text
NO_MATCH → UNKNOWN → MATCH
```

### 9.2 조건별 원칙

- 신청 마감이 명확하면 `NO_MATCH`
- 사용자 나이가 정책 범위를 벗어나면 `NO_MATCH`
- 사용자 5자리 지역 코드가 정책 지역 목록에 없으면 `NO_MATCH`
- 취업 상태가 명확히 다르면 `NO_MATCH`
- 소득·교육·자연어 조건이 불명확하면 자동 탈락시키지 않고 `UNKNOWN`
- 누락값을 근거로 자격을 확정하지 않음

## 10. 검색 및 LLM 안전 원칙

- LLM은 검색 결과 밖의 정책을 추가하지 않는다.
- 공식 정책 데이터에 없는 금액, 날짜, 서류, 연락처를 만들지 않는다.
- `신청 가능합니다`, `자격이 확정되었습니다`와 같은 표현을 사용하지 않는다.
- 출처와 확인일을 가능한 범위에서 유지한다.
- 사용자의 자연어 입력과 비밀키를 로그나 문서에 기록하지 않는다.
- OpenAI 호출 실패 시 공식 정책 결과를 숨기지 않는다.

UI에는 다음 의미의 안내를 표시한다.

> 지원 가능성이 높은 정책입니다. 최종 신청 자격과 세부 조건은 반드시 공식 공고문에서 확인해야 합니다.

## 11. 설정 및 비밀정보

사용 환경 변수 또는 Streamlit secrets 이름은 다음과 같다.

```text
ONTONG_API_KEY=
OPENAI_API_KEY=
OPENAI_CHAT_MODEL=
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

관리 원칙:

- 실제 키는 `.streamlit/secrets.toml` 또는 로컬 환경 변수에 저장
- `.env`, `.streamlit/secrets.toml`은 Git 제외
- 키를 코드, 테스트, 문서, 캡처, 로그에 포함하지 않음
- 모델명은 환경 설정으로 변경 가능하게 유지

## 12. 테스트 및 검증

검증된 명령:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall app.py src
.\.venv\Scripts\python.exe -m streamlit run app.py
```

현재 결과:

- 전체 테스트: `122 passed`
- compileall: 성공
- Streamlit 로컬 실행: 성공
- 실제 관심사 입력 기반 FAISS Top-5 검색: 성공
- 실제 OpenAI 추천 설명 생성: 성공
- GitHub `main` 브랜치 푸시: 완료

단위 테스트에서는 실제 외부 API를 호출하지 않고 mock 또는 fixture를 사용한다.

## 13. 현재 한계

- 현재 실제 데이터 검증 범위는 2페이지, 총 20건이다.
- 소득 조건의 개인·가구 기준과 단위는 완전 구조화되지 않았다.
- 교육 상태와 복잡한 자연어 자격 조건은 자동 확정하지 않는다.
- 임베딩과 LLM 호출은 실행 시 OpenAI API 사용량이 발생한다.
- raw 데이터와 SQLite 파일이 Git에 없으므로 새 환경에서는 데이터 파이프라인을 다시 실행해야 한다.
- Streamlit Community Cloud 배포는 아직 완료되지 않았다.

## 14. 남은 작업

- 최종 실행 화면 검증 및 캡처 정리
- 결과보고서 작성
- README와 보고서의 실행 근거 최종 확인
- 필요 시 Streamlit Community Cloud 배포
- 최종 커밋 및 GitHub 푸시

## 15. MVP 완료 기준

현재 로컬 MVP 핵심 기능은 완료되었다. MVP 완료 기준은 다음 항목까지 확인하는 것이다.

- 실제 데이터 20건 수집 및 중복 방지
- 규칙 기반 3단계 평가
- FAISS Top-5 검색
- 공식 데이터 기반 OpenAI 설명
- AI 실패 시 규칙 결과 유지
- 공식 출처 및 최종 확인 안내 표시
- 전체 테스트 통과
- 로컬 Streamlit 실행 화면 확보
- 결과보고서와 화면 캡처 정리
- 문서와 실제 구현 상태 일치

## 16. 개발 이력

### 2026-06-29

- 정책 데이터 모델, 코드북, 예시 JSON 파서, SQLite 저장소 구현
- 규칙 기반 단건·일괄 평가 구현
- 당시 전체 테스트 `81 passed`
- 당시 다음 목표는 규칙 기반 Streamlit 데모 UI 구현

### 2026-07-01

- 실제 온통청년 API 호출 및 snapshot 파이프라인 연결
- SQLite 적재·재조회 및 중복 방지 확인
- 여러 페이지 수집으로 20건 확보
- Streamlit UI와 지역 선택 구현

### 2026-07-02

- OpenAI 임베딩 + FAISS Top-5 검색 구현
- 검색 결과 기반 OpenAI 추천 설명 구현
- 실제 실행 화면 검증
- 전체 테스트 `122 passed`
- GitHub `main` 반영 완료
