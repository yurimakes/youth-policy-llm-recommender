## 현재 상태 (2026-07-01)

이 저장소는 `github.com/choiyuri-dev/youth-policy-llm-recommender`를 기준으로 관리합니다.

온통청년 OPEN API 인증키 승인이 완료되었고, 최신 청년정책 API 엔드포인트 `https://www.youthcenter.go.kr/go/ythip/getPlcy`에 맞춰 목록 JSON 조회 흐름을 구현했습니다. 요청 파라미터는 `apiKeyNm`, `pageNum`, `pageSize`, `pageType`, `rtnType`을 사용합니다.

실제 API JSON 호출로 전체 정책 수 `2,633`건을 확인했고, 1페이지 정책 10건의 원본 JSON과 메타데이터를 저장했습니다. 실제 응답의 정책 목록은 `result.youthPolicyList`에 있으며, 저장된 실제 정책 10건은 기존 `PolicyRecord` 파서로 변환됩니다. `sbizCd`와 `sBizCd` 필드명은 모두 안전하게 처리합니다.

snapshot JSON → `PolicyRecord` → SQLite 적재 → SQLite 재조회 파이프라인을 구현했습니다. 실제 정책 입력 10건, SQLite 저장·재조회 10건을 확인했고, 동일 snapshot 재적재 시 중복 행이 증가하지 않습니다. SQLite 조회 결과는 기존 `evaluate_policies()`에 연결됩니다.

실제 검증 프로필은 나이 24세, 지역 코드 `11680`, 취업 상태 `미취업자`이며, 평가 결과는 `MATCH` 2건, `UNKNOWN` 1건, `NO_MATCH` 7건, 총 10건입니다.

현재 전체 자동 테스트 결과는 `102 passed`이고 `python compileall`도 성공했습니다. `data/raw`, `data/processed`, SQLite 산출물은 `.gitignore`로 제외하며 실제 raw 데이터 파일과 실제 SQLite 파일은 Git에 포함하지 않습니다.

다음 작업은 온통청년 API를 여러 페이지 순차 수집하고 각 raw 응답을 보존하면서 SQLite에 중복 없이 적재하는 기능 구현입니다. 초기 안전 검증 범위는 `pageSize=10`, `max_pages=2`, 정책 최대 20건입니다.

## 아직 완료되지 않은 작업 (2026-07-01)

* 여러 페이지 수집
* 전체 또는 필요한 범위 정책 적재
* Streamlit UI
* FAISS 검색
* LLM 설명
* 배포

## 개발 진행 이력

### 2026-06-29부터 2026-07-01 이전 기록
# 청년 맞춤 정책 추천 및 신청 지원 웹서비스

청년의 나이, 거주 지역, 취업 상태, 소득 조건을 바탕으로 신청 가능성이 있는 청년정책을 추천하는 LLM 기반 웹서비스 프로젝트입니다.

현재는 온통청년 예시 정책 데이터를 이용한 **규칙 기반 1차 정책 매칭과 추천 후보 분류 기능**까지 구현되어 있습니다.

## 프로젝트 목표

청년정책은 제공 기관마다 대상 조건과 신청 방식이 달라 사용자가 자신에게 맞는 정책을 직접 찾기 어렵습니다.

본 프로젝트는 공공 청년정책 데이터를 표준화하고, 사용자 조건에 따라 신청 가능성이 있는 정책을 먼저 선별한 뒤 벡터 검색과 LLM을 이용하여 추천 이유와 신청 정보를 제공하는 것을 목표로 합니다.

이 서비스는 정책 탐색과 정보 확인을 돕는 보조 도구입니다. 최종 신청 자격을 확정하거나 사용자를 대신해 정책 신청을 제출하지 않습니다.

> 지원 가능성이 높은 정책입니다. 최종 신청 자격과 세부 조건은 반드시 공식 공고문에서 확인해야 합니다.

## 개발 진행 이력 — 2026-06-29 당시 개발 상태

* 기준일: 2026년 6월 29일
* 전체 MVP 예상 진행률: 약 55%
* 백엔드 기반 예상 진행률: 약 75%
* 전체 자동 테스트: 81개 통과
* 2026-06-29 당시 다음 개발 작업: Streamlit 규칙 기반 데모 UI 구현

현재 완료된 핵심 범위는 다음과 같습니다.

* 온통청년 정책 데이터 구조 분석
* 정책 표준 데이터 모델 구현
* 공식 예시 JSON 10건 파싱
* 코드북 기반 코드값 변환
* SQLite 정책 저장·조회·갱신
* 신청 상태·연령·지역·취업 상태·소득 조건 판정
* 여러 정책의 일괄 평가
* 추천 가능·추가 확인·조건 불일치 정책 분류
* pytest 자동 테스트
* Git 및 GitHub 버전 관리

## 개발 진행 이력 — 2026-06-29 당시 구현된 기능

### 1. 정책 표준 모델

온통청년 정책 데이터를 공통 구조로 처리하기 위한 `PolicyRecord` 모델을 구현했습니다.

주요 필드는 다음과 같습니다.

* 정책 ID 및 정책명
* 정책 분류 및 요약
* 지역 코드 및 지역명
* 최소·최대 연령
* 취업 상태
* 소득 조건
* 교육 상태
* 신청 시작일 및 종료일
* 신청 상태
* 지원 내용
* 신청 방법
* 필요 서류
* 문의처
* 공식 출처
* 데이터 검증 시각
* 벡터 검색용 텍스트

### 2. 온통청년 JSON 파싱

온통청년 공식 예시 JSON 데이터를 `PolicyRecord` 객체로 변환하는 파서를 구현했습니다.

원본 코드값은 코드북을 이용하여 사람이 확인할 수 있는 한국어 값으로 변환합니다.

현재 공식 예시 정책 10건을 이용하여 다음 항목을 검증했습니다.

* 정책 기본 정보
* 신청 기간과 신청 상태
* 연령 조건
* 지역 코드
* 취업 상태
* 소득 조건
* 지원 및 신청 정보

### 3. SQLite 정책 저장소

정책 데이터를 로컬에서 저장하고 조회할 수 있도록 SQLite 저장소를 구현했습니다.

지원 기능:

* 데이터베이스 연결
* 정책 테이블 초기화
* 정책 추가 및 갱신
* 정책 ID 기준 단건 조회
* 전체 정책 목록 조회
* 조회 결과의 `PolicyRecord` 변환

### 4. 규칙 기반 정책 매칭

사용자 프로필과 정책을 비교하는 규칙 기반 판정 기능을 구현했습니다.

판정 결과는 다음 세 상태로 구분합니다.

| 상태         | 의미              |
| ---------- | --------------- |
| `MATCH`    | 입력한 기본 조건과 일치   |
| `UNKNOWN`  | 세부 조건의 추가 확인 필요 |
| `NO_MATCH` | 명확한 조건 불일치      |

최종 판정 우선순위:

```text
NO_MATCH → UNKNOWN → MATCH
```

조건 판정 순서:

```text
신청 상태 → 연령 → 지역 → 취업 상태 → 소득
```

#### 신청 상태

* 마감된 정책은 `NO_MATCH`
* 신청 예정 정책은 `UNKNOWN`
* 신청 상태를 확인할 수 없으면 `UNKNOWN`
* 신청 가능한 정책은 나머지 조건을 계속 판정

#### 연령

* 정책의 연령 범위에 포함되면 `MATCH`
* 최소 또는 최대 연령을 벗어나면 `NO_MATCH`
* 사용자 나이나 정책 연령 조건이 없으면 `UNKNOWN`

#### 지역

* 사용자 지역 코드가 정책의 지역 코드 목록에 포함되면 `MATCH`
* 사용자 지역이 목록에 없으면 `NO_MATCH`
* 사용자 또는 정책 지역값을 확인할 수 없으면 `UNKNOWN`

전국 정책은 여러 지역 코드가 나열된 형태이므로 동일한 포함 여부 비교 방식으로 처리합니다.

#### 취업 상태

* 사용자와 정책 취업 상태가 같으면 `MATCH`
* 정책 취업 조건이 `제한없음`이면 `MATCH`
* 취업 상태가 명확히 다르면 `NO_MATCH`
* 사용자 또는 정책 값이 없으면 `UNKNOWN`

#### 소득 조건

현재 정책 데이터에는 금액 단위와 개인·가구 기준이 완전히 구조화되어 있지 않아 보수적으로 판정합니다.

* 소득 조건이 정확히 `무관`이면 `MATCH`
* 소득 조건이 없으면 `UNKNOWN`
* 연소득 금액, 기준중위소득, 가구 조건 등은 `UNKNOWN`
* 불명확한 소득 조건으로 사용자를 자동 탈락시키지 않음

### 5. 여러 정책 일괄 평가

여러 정책을 한꺼번에 평가하는 `evaluate_policies()` 함수를 구현했습니다.

평가 결과는 다음 세 그룹으로 나뉩니다.

* `matched`: 추천 가능한 정책
* `unknown`: 추가 확인이 필요한 정책
* `no_match`: 조건이 일치하지 않는 정책

각 평가 결과에는 원래 정책 데이터와 판정 상태, 판정 이유가 함께 저장됩니다.

다음 동작도 검증했습니다.

* 빈 정책 목록 처리
* 리스트 입력 처리
* generator 입력 처리
* 각 결과 그룹에서 입력 정책의 상대적 순서 유지
* SQLite 전체 조회 결과 직접 연결
* 추천 후보와 제외 정책 분리

### 6. 실제 API snapshot SQLite 파이프라인

저장된 온통청년 실제 API JSON snapshot을 기존 파서와 SQLite 저장소에 연결하는 파이프라인을 구현했습니다.

구현된 흐름:

```text
snapshot JSON
        ↓
PolicyRecord 변환
        ↓
SQLite 적재
        ↓
SQLite 재조회
        ↓
evaluate_policies() 연결
```

확인된 결과:

* 실제 정책 입력 10건
* SQLite 저장·재조회 10건
* 동일 snapshot 재적재 시 중복 증가 없음
* 실제 검증 프로필 기준 `MATCH` 2건, `UNKNOWN` 1건, `NO_MATCH` 7건

## 개발 진행 이력 — 2026-06-29 당시 처리 흐름

```text
온통청년 예시 JSON
        ↓
정책 데이터 파싱
        ↓
PolicyRecord 표준 모델
        ↓
SQLite 저장 및 조회
        ↓
사용자 조건 입력
        ↓
신청 상태·연령·지역·취업·소득 조건 판정
        ↓
MATCH / UNKNOWN / NO_MATCH 분류
        ↓
추천 후보 목록 생성
```

## 기술 스택

| 영역       | 사용 기술                        |
| -------- | ---------------------------- |
| 언어       | Python 3.10                  |
| 웹 애플리케이션 | Streamlit                    |
| HTTP 통신  | Requests                     |
| 데이터 처리   | Pandas                       |
| 구조화 저장소  | JSON, CSV, SQLite            |
| 벡터 검색    | FAISS 예정                     |
| 임베딩      | OpenAI API 예정                |
| 설명 생성    | OpenAI API 예정                |
| 테스트      | pytest                       |
| 배포       | Streamlit Community Cloud 예정 |

현재 Streamlit, FAISS, OpenAI 관련 패키지는 개발 환경에 포함되어 있으나 웹 화면, 벡터 검색, LLM 설명 생성 기능은 아직 연결하지 않았습니다.

## 테스트

전체 테스트 실행:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

현재 테스트 결과:

```text
102 passed
```

검증된 영역:

* 정책 데이터 모델
* 온통청년 코드북
* JSON 파싱
* SQLite 저장 및 조회
* 신청 상태 판정
* 연령 조건 판정
* 지역 조건 판정
* 취업 상태 판정
* 소득 조건 안전 판정
* 여러 정책 일괄 평가
* SQLite 조회 결과와 평가 기능 연동

## 주요 프로젝트 파일

추가로 현재 구현에 포함된 주요 파일:

```text
src/career_catch/config.py
src/career_catch/ontong_client.py
src/career_catch/pipeline.py
scripts/fetch_ontong_policies.py
scripts/load_ontong_snapshot.py
tests/test_ontong_client.py
tests/test_pipeline.py
```

```text
src/career_catch/
├── models.py
├── codebook.py
├── ontong_parser.py
├── sqlite_store.py
└── matching.py

tests/
├── fixtures/
├── test_models.py
├── test_codebook.py
├── test_ontong_parser.py
├── test_sqlite_store.py
└── test_matching.py

PROJECT_SPEC.md
PROJECT_STATUS.md
TASKS.md
AGENTS.md
requirements.txt
.env.example
```

## 개발 진행 이력 — 2026-06-29 당시 제한 사항

* 실제 온통청년 API 인증키 기반 데이터 호출 미연결
* 공식 예시 JSON 10건을 중심으로 기능 검증
* 복잡한 자연어 자격 조건 자동 판정 미구현
* 소득 금액 단위와 개인·가구 기준 미구조화
* 벡터 유사도 검색 미구현
* LLM 추천 이유 및 신청 안내 미구현
* Streamlit 웹 화면 미구현
* 서비스 배포 미진행

불명확한 정책 조건은 잘못된 자동 탈락을 방지하기 위해 `UNKNOWN`으로 분류합니다.

## 개발 예정 순서

* [x] 정책 데이터 모델 구현
* [x] 온통청년 예시 JSON 파싱
* [x] SQLite 저장 및 조회
* [x] 규칙 기반 단건 정책 판정
* [x] 여러 정책 일괄 평가 및 후보 분류
* [x] 실제 온통청년 API 호출
* [x] 실제 API snapshot 저장 및 파싱
* [x] 실제 정책 데이터 SQLite 적재 및 재조회
* [x] SQLite 조회 결과와 규칙 기반 평가 연결
* [ ] 온통청년 API 여러 페이지 수집
* [ ] Streamlit 규칙 기반 데모 UI
* [ ] FAISS 벡터 유사도 검색
* [ ] LLM 추천 이유 및 신청 정보 생성
* [ ] Streamlit 통합 화면 개선
* [ ] 배포 및 최종 검증
* [ ] 최종 보고서 및 발표 자료 작성

## 저장소

GitHub 저장소:

```text
choiyuri-dev/youth-policy-llm-recommender
```
