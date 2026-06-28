# 청년 맞춤 정책 추천 및 신청 지원 웹서비스

## 현재 상태

이 저장소는 현재 문서 및 최소 개발 환경 설정 준비 단계입니다.

애플리케이션 기능은 아직 구현되지 않았습니다. 현재 저장소에는 Streamlit 앱, 데이터 수집 스크립트, 정제 데이터셋, SQLite 데이터베이스, FAISS 인덱스, 자동화 테스트, 배포 URL이 없습니다.

최소 설정 파일로 `requirements.txt`와 `.env.example`이 생성되었습니다. Python 3.10.11 가상환경에서 `requirements.txt`의 직접 의존성 설치가 성공했고, 핵심 패키지 import와 버전 출력도 성공한 것으로 기록합니다. 애플리케이션 실행과 pytest 테스트는 아직 수행하지 않았습니다.

저장소 루트는 `career-catch-4/`입니다.

## 프로젝트 목표

이 프로젝트는 공식 공공 데이터를 바탕으로 청년 사용자에게 관련 정책을 탐색할 수 있도록 돕는 MVP 웹 프로토타입을 만드는 것을 목표로 합니다.

이 서비스는 추천 및 정보 제공 보조 도구입니다. 최종 법적 또는 행정적 신청 자격을 판정하지 않으며, 사용자를 대신해 정책 신청을 제출하지 않습니다.

필수 안전 문구:

> 지원 가능성이 높은 정책입니다. 최종 신청 자격과 세부 조건은 반드시 공식 공고문에서 확인해야 합니다.

## 계획된 MVP 범위

계획된 MVP는 다음 기능을 목표로 합니다.

- 사용자 조건과 선택 입력된 자연어 요청을 수집합니다.
- 온통청년 청년정책 API를 주 데이터 소스로 사용합니다.
- API 원본 JSON 또는 XML 스냅샷을 보존합니다.
- 정책 데이터를 canonical fields로 정규화합니다.
- 정제 데이터를 CSV와 SQLite로 저장합니다.
- `MATCH`, `NO_MATCH`, `UNKNOWN` 기반의 결정적 tri-state 필터링을 적용합니다.
- 남은 후보를 FAISS semantic search로 순위화합니다.
- OpenAI API는 검색된 공식 정책 데이터를 설명하는 용도로만 사용합니다.
- 공식 출처 링크, 검증일, 확인이 필요한 조건을 표시합니다.

위 기능은 계획된 범위이며 아직 구현되지 않았습니다.

## 초기 MVP 제외 항목

초기 MVP에서는 다음 항목을 제외합니다.

- FastAPI
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

이 항목들은 MVP가 검증되고 범위가 명시적으로 승인된 뒤 향후 확장으로만 검토합니다.

## 계획된 기술 스택

| 영역 | 계획된 선택 |
|---|---|
| 언어 | Python 3.10 |
| 웹 애플리케이션 | Streamlit |
| HTTP 수집 | Requests |
| 데이터 처리 | Pandas |
| 구조화 저장소 | raw snapshots, processed CSV, SQLite |
| 벡터 검색 | FAISS |
| 임베딩 | OpenAI API, 기본값 `text-embedding-3-small` |
| 설명 생성 | OpenAI API, 환경 변수로 지정한 chat model |
| 테스트 | pytest |
| 배포 대상 | Streamlit Community Cloud |

## 설정 파일

현재 생성된 최소 설정 파일은 다음과 같습니다.

- `requirements.txt`: 검증된 직접 Python 의존성 목록
- `.env.example`: 필요한 환경 변수 이름과 기본 embedding model 값

`requirements.txt`에는 Python 표준 라이브러리인 SQLite, pathlib 등을 포함하지 않았고, 전이 의존성도 추가하지 않았습니다. 직접 의존성은 실제 설치 및 import 검증 결과를 기준으로 버전을 고정했습니다.

`.env.example`에는 실제 API 키나 임의의 가짜 키를 넣지 않았습니다.

## 검증된 직접 의존성

Python 3.10.11 가상환경에서 패키지 설치와 import 버전 확인이 성공했습니다.

| 패키지 | 검증된 버전 |
|---|---|
| streamlit | 1.58.0 |
| requests | 2.34.2 |
| pandas | 2.3.3 |
| faiss-cpu | 1.14.3 |
| openai | 2.44.0 |
| pytest | 9.1.1 |

확인된 import 대상은 `streamlit`, `requests`, `pandas`, `faiss`, `openai`, `pytest`입니다.

## 계획된 데이터 산출물

계획된 데이터 구조는 다음과 같습니다.

- `raw`: API 원본 JSON 또는 XML 스냅샷
- `processed`: 정제 CSV 파일과 SQLite 데이터베이스
- `vector artifacts`: FAISS 인덱스와 정책 ID 매핑 데이터

이 파일과 폴더는 아직 생성되지 않았습니다.

## 계획된 애플리케이션 흐름

1. 사용자 프로필 조건과 선택 입력된 자연어 요청을 수집합니다.
2. 구조화된 정책 필드에 Python rule-based filtering을 적용합니다.
3. 불확실한 조건은 `UNKNOWN`으로 유지합니다.
4. 남은 후보를 FAISS semantic similarity로 순위화합니다.
5. 검색된 공식 정책 데이터만 OpenAI API에 전달합니다.
6. 새로운 자격 판정이 아니라 근거 기반 설명을 생성합니다.
7. 결과, 불확실성, 공식 출처 링크, 검증일을 Streamlit에 표시합니다.

## 설정 상태

Python 3.10.11 가상환경에서 패키지 설치와 핵심 패키지 import 검증은 완료했습니다.

애플리케이션 코드가 아직 없으므로 Streamlit 실행 검증은 수행하지 않았습니다. 테스트 파일도 아직 없으므로 pytest 테스트 실행은 수행하지 않았습니다.

## 계획된 검증

관련 파일이 생성되고 구현이 진행된 뒤 다음 명령을 사용할 예정입니다.

```bash
python -m pytest
python -m compileall app.py src
python -m streamlit run app.py
```

이 명령들은 아직 이 저장소에서 실행하거나 검증하지 않았습니다.

## 현재 제한 사항

- 애플리케이션 코드가 아직 없습니다.
- API 데이터가 아직 수집되지 않았습니다.
- 정제 데이터와 데이터베이스가 아직 없습니다.
- FAISS 인덱스가 아직 없습니다.
- 테스트가 아직 없습니다.
- 애플리케이션 실행 검증이 아직 수행되지 않았습니다.
- pytest 테스트 실행이 아직 수행되지 않았습니다.
- 배포가 아직 수행되지 않았습니다.
