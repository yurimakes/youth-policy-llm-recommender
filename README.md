# 청년 맞춤 정책 추천

**공식 청년정책 데이터를 구조화하고, 사용자 조건과 자연어 관심사를 연결하는 정책 탐색 웹서비스**

나이·지역·취업 상태로 정책 후보를 평가한 뒤, 관심사와 관련된 정책을 FAISS로 검색하고 검색된 공식 정보를 바탕으로 LLM이 추천 이유와 확인사항을 설명합니다.

현재 구현 범위는 **로컬 MVP**입니다. 정책 탐색과 신청 전 정보 확인을 돕는 보조 도구이며, 최종 신청 자격을 확정하거나 신청을 대신 제출하지 않습니다.

## 프로젝트 배경

청년정책마다 연령, 거주 지역, 취업 상태, 소득, 신청 기간이 다릅니다. 사용자는 여러 공고를 비교해야 하고, 조건이 누락되거나 자유 텍스트로 작성된 경우 자신에게 해당하는지 판단하기 어렵습니다.

이 프로젝트는 공식 데이터를 공통 모델로 정리하고, 명확한 조건과 추가 확인이 필요한 조건을 구분합니다. 여기에 자연어 검색과 추천 설명을 더해 **정책을 찾는 과정부터 공식 공고를 확인하는 과정까지** 연결하는 것을 목표로 합니다.

## 주요 기능

| 단계 | 구현 내용 |
|---|---|
| 수집 | 온통청년 청년정책 API 페이지 수집, 원본 JSON과 수집 메타데이터 분리 보존 |
| 정규화 | API 응답을 `PolicyRecord`로 변환, 코드값 해석, 신청 기간·상태 처리 |
| 저장 | SQLite 적재·조회, `policy_id` 기준 upsert로 중복 증가 방지 |
| 조건 평가 | 나이·지역·취업 상태·신청 상태 등을 `MATCH`, `UNKNOWN`, `NO_MATCH`로 분류 |
| 관심사 검색 | `MATCH`와 `UNKNOWN` 후보를 OpenAI 임베딩 + FAISS로 검색해 최대 5건 반환 |
| 추천 설명 | 검색된 정책의 공식 정보와 규칙 평가 이유를 바탕으로 LLM 설명 생성 |
| 결과 화면 | 평가 요약, 정책별 상세 정보, 확인사항, 제공된 출처 링크 표시 |
| 오류 대응 | AI 호출 실패 시 규칙 평가 결과 유지, 설명 생성만 실패하면 검색 결과도 유지 |

사용자가 관심사를 비워 두면 AI 검색·설명 없이 규칙 평가 결과를 확인할 수 있습니다.

## 구조와 설계

데이터 준비와 사용자 요청 처리를 분리한 단일 Streamlit 애플리케이션입니다.

| 구간 | 처리 흐름 |
|---|---|
| 데이터 준비 | 공식 API → 원본 snapshot → `PolicyRecord` 정규화 → SQLite |
| 사용자 요청 | SQLite 조회 → 사용자 조건 평가 → `MATCH`·`UNKNOWN` 후보 → 임베딩·FAISS 검색 → LLM 설명 → 결과 표시 |

### 1. 규칙으로 조건을 평가합니다

| 상태 | 의미 | 검색 후보 포함 |
|---|---|---|
| `MATCH` | 평가한 구조화 조건과 일치 | 포함 |
| `UNKNOWN` | 조건이 누락되었거나 추가 확인 필요 | 포함 |
| `NO_MATCH` | 평가한 조건에서 명확한 불일치 또는 신청 마감 | 제외 |

여러 조건 중 `NO_MATCH`가 있으면 이를 우선하고, 불일치가 없어도 `UNKNOWN` 조건이 있으면 최종 평가를 `UNKNOWN`으로 유지합니다. `MATCH`도 전체 공고의 신청 자격이 확정되었다는 의미는 아닙니다.

소득 조건은 사용자 소득과 수치 비교하지 않습니다. 현재는 소득 무관 여부를 확인하고, 그 외 조건은 추가 확인 대상으로 남깁니다.

### 2. 벡터 검색으로 관심사를 반영합니다

정책의 `embedding_text`를 우선 사용하고, 없으면 정책명·분류·요약·자격·지원 내용·신청 방법 등 공식 필드를 결합합니다. 정책 벡터와 질의 벡터를 L2 정규화한 뒤 FAISS `IndexFlatIP`로 유사도를 계산합니다.

검색 결과에는 `policy_id`, 벡터 위치, 유사도 점수를 함께 보관합니다. **유사도 점수는 관심사와의 관련도를 나타내며, 지원 자격 충족 확률이 아닙니다.** 현재는 요청마다 후보 임베딩과 메모리 인덱스를 생성합니다.

### 3. LLM은 검색된 정책을 설명합니다

LLM에는 검색된 최대 5개 정책, 사용자 조건, 규칙 평가 이유를 전달합니다. 프롬프트는 추천 이유·일치 조건·확인사항·신청 기간·출처를 설명하고, 제공된 데이터에 없는 내용은 `확인 필요`로 표시하도록 요구합니다.

현재는 프롬프트로 설명 범위를 제한하는 방식입니다. 생성된 문장마다 공식 원문과 일치하는지 자동 검증하는 기능은 구현되어 있지 않으므로, 최종 판단에는 공식 공고 확인이 필요합니다.

## 기술 스택

| 영역 | 기술 및 역할 |
|---|---|
| 언어 | Python, 기존 개발 환경 Python 3.10 |
| UI | Streamlit |
| API 통신 | Requests |
| 데이터 처리 | Python dataclass, Pandas |
| 저장소 | JSON snapshot, SQLite |
| 검색 | OpenAI 임베딩, FAISS |
| 설명 생성 | OpenAI Chat Completions API, 설정으로 모델 지정 |
| 검증 | pytest, compileall |

의존성 버전은 [requirements.txt](requirements.txt)에 고정되어 있습니다.

## 디렉터리 구조

| 경로 | 역할 |
|---|---|
| `app.py` | Streamlit 진입점, 입력·결과 화면, 검색·설명 호출 |
| `src/youth_policy/models.py` | 정책 데이터 모델과 기본 유효성 검사 |
| `src/youth_policy/codebook.py`, `ontong_parser.py` | 코드값 해석과 공식 응답 정규화 |
| `src/youth_policy/ontong_client.py`, `collection.py` | API 호출, snapshot 보존, 여러 페이지 수집 |
| `src/youth_policy/pipeline.py`, `sqlite_store.py` | snapshot 적재, SQLite 저장·조회 |
| `src/youth_policy/matching.py` | 사용자 조건의 3단계 평가 |
| `src/youth_policy/retrieval.py`, `llm_service.py` | 벡터 검색, 공식 정보 기반 설명 생성 |
| `src/youth_policy/config.py`, `ui_service.py` | 수집 설정과 UI용 데이터 로딩·평가 |
| `scripts/` | 데이터 수집·적재 CLI |
| `tests/` | 모델·파서·저장소·규칙·검색 입력·설명 프롬프트 테스트 |
| `assets/` | UI 이미지 |
| `data/raw/ontong/` | 실행 시 생성되는 원본 JSON·메타데이터, Git 제외 |
| `data/processed/policies.sqlite3` | 앱에서 읽는 로컬 정책 DB, Git 제외 |

## 로컬 실행

아래 안내는 Windows PowerShell에서 저장소 루트를 기준으로 합니다. 원본 정책 데이터와 DB는 저장소에 포함되지 않으므로 앱 실행 전에 데이터를 준비해야 합니다.

### 1. 저장소와 가상환경 준비

```powershell
git clone https://github.com/yurimakes/youth-policy-llm-recommender.git
cd youth-policy-llm-recommender
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Python 버전·운영체제에 따라 고정된 의존성의 설치 가능 여부를 확인해야 합니다.

### 2. API 설정

온통청년 API 인증키와 OpenAI API 키를 준비합니다. 저장소 루트에 `.streamlit/secrets.toml`을 만들고 아래 항목을 설정합니다.

```toml
ONTONG_API_KEY = ""
OPENAI_API_KEY = ""
OPENAI_CHAT_MODEL = ""
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
```

키와 채팅 모델명은 사용 가능한 값으로 입력합니다. 빈 채팅 모델 설정은 앱의 기본값을 사용합니다. 환경 변수도 지원하며, 수집 CLI와 앱 모두 환경 변수를 먼저 읽고, 값이 없으면 Streamlit secrets를 읽습니다. `.env` 파일을 자동으로 불러오는 기능은 없습니다.

### 3. 정책 수집과 SQLite 적재

수집 CLI는 페이지별 원본을 보존하고 정규화된 정책을 DB에 함께 적재합니다.

```powershell
.\.venv\Scripts\python.exe scripts/collect_ontong_pages.py `
  --db data/processed/policies.sqlite3 `
  --page-size 10 `
  --max-pages 2
```

이 설정은 최대 2페이지를 수집합니다. 과거 실제 API 검증에서는 20건이 적재되었으며, 현재 반환 건수와 내용은 API 응답에 따라 달라질 수 있습니다. CLI 출력의 `fetched_policies`와 `stored_policies`로 수집·저장 건수를 확인합니다.

이미 보존한 snapshot이 있다면 `scripts/load_ontong_snapshot.py`의 `--input`, `--db` 옵션으로 재적재할 수 있습니다.

### 4. 웹서비스 실행

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

나이, 시·도와 시·군·구, 취업 상태를 입력하고 필요하면 관심사를 작성한 뒤 `맞춤 정책 추천받기`를 누릅니다. 예: `자격증 시험 비용과 월세 지원이 필요해요.` 지역 선택지는 현재 적재된 정책의 지역 정보에서 구성됩니다.

## 테스트와 검증 범위

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall app.py src scripts
```

기존 개발 기록의 **2026-07-02 검증 결과**는 전체 테스트 `122 passed`, 실제 API 2페이지·20건 수집, SQLite 재조회·중복 방지, 로컬 Streamlit 실행, 실제 FAISS 검색 및 OpenAI 설명 생성 성공입니다. 이 결과는 해당 시점의 검증 기록이며, 현재 API 데이터나 배포 환경의 동작을 보증하지 않습니다.

자동 테스트는 외부 API를 직접 호출하지 않고 mock·fixture를 사용합니다. 모델 유효성, 필드 매핑, 날짜·누락값 처리, SQLite 왕복·upsert, 조건 평가, 페이지 수집, UI용 서비스, 임베딩 입력·호출, 설명 프롬프트를 검증합니다. 추천 품질이나 LLM 사실 정확도를 측정한 성능 지표는 아직 없습니다.

## 현재 한계와 개선 방향

| 현재 한계 | 개선 방향 |
|---|---|
| 실제 통합 검증 데이터는 20건이며 전체 정책을 포괄하지 않음 | 수집 범위 확대, 지역·분류별 데이터 품질 점검 |
| 소득 수치 비교·학력 조건 평가·복잡한 자격 해석은 미구현 | 개인·가구 기준과 단위를 구조화하고 조건별 테스트 확대 |
| 지역 코드는 목록 포함 여부, 취업 상태는 문자열 비교 중심 | 전국·광역 범위와 복합 취업 조건의 처리 정교화 |
| 신청 상태는 적재 시점 기준으로 계산됨 | 데이터 갱신 또는 조회 시점 재평가로 최신성 유지 |
| 요청마다 후보 임베딩과 인덱스를 생성함 | 정책 변경을 고려한 임베딩 캐시와 인덱스 재사용 |
| 생성된 설명의 사실 일치를 문장 단위로 검증하지 않음 | 근거 연결·출력 검증 및 평가 사례 구축 |
| 원문 데이터·DB를 새 환경에서 다시 준비해야 함 | 데이터 준비 절차와 배포 환경의 재현성 개선 |

로그인, 사용자 프로필의 영구 저장, 신청 자동 제출은 현재 MVP 범위에 포함되지 않습니다. 배포 목표는 Streamlit Community Cloud이며, 기존 개발 기록상 배포는 미완료입니다.

## 데이터 출처와 관리

- **주요 출처:** [온통청년](https://www.youthcenter.go.kr/) 청년정책 API
- **수집 endpoint:** `https://www.youthcenter.go.kr/go/ythip/getPlcy`
- **추적 정보:** `source_name`, 제공된 `source_url`, 적재·확인 시각 `last_verified_at`
- **보존 방식:** 원본 snapshot과 수집 메타데이터를 분리하고, 정규화 결과는 SQLite에 저장

`last_verified_at`은 데이터 적재·처리 시 기록한 시각이며, 담당 기관이 모든 자격 조건을 재확인했다는 의미는 아닙니다. 출처 URL이 누락된 경우에는 공식 공고를 별도로 확인해야 합니다.

실제 API 키, `.streamlit/secrets.toml`, `.env`, 원본 데이터와 로컬 DB는 Git에 포함하지 않습니다. AI 검색·설명을 사용할 때 관심사와 사용자 조건 등이 OpenAI API로 전달되며 사용량에 따른 비용이 발생합니다.

데이터의 사용·재배포에는 제공기관의 개별 이용 조건을 확인해야 합니다. 저장소에는 현재 코드 라이선스가 지정되어 있지 않습니다.
