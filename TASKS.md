# TASKS.md

## 1. 현재 상태

이 저장소는 현재 최소 정책 데이터 모델 구현 단계입니다.

- 저장소 루트: `career-catch-4/`
- Python 버전: 3.10.11 가상환경에서 패키지 설치 및 import 검증 완료
- 최소 설정 파일: `requirements.txt`, `.env.example` 생성됨
- canonical `PolicyRecord` 모델: 구현됨
- `PolicyRecord` 단위 테스트: 구현 및 통과
- API 수집: 아직 시작하지 않음
- 애플리케이션 구현: 아직 시작하지 않음
- 데이터 파일, SQLite 데이터베이스, FAISS 산출물: 아직 생성되지 않음
- 배포: 아직 수행되지 않음

## 2. 확정된 MVP 범위

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

주 데이터 소스는 온통청년 청년정책 API입니다. raw 데이터, processed 데이터, vector artifacts는 추적 가능하고 재현 가능하게 관리해야 합니다.

## 3. 현재 작업

**작업:** canonical `PolicyRecord` 모델 구현 및 테스트

**상태:** 구현 및 테스트 완료, 사용자 검토 대기 중입니다.

이번 작업에서는 온통청년 API 정제 데이터의 기준이 될 최소 정책 데이터 모델과 단위 테스트만 구현했습니다. API 필드 매핑, SQLite 저장, 필터링 로직, FAISS, OpenAI API, Streamlit UI, 데이터 파일은 구현하지 않았습니다.

## 4. 생성된 파일

- `src/career_catch/__init__.py`
- `src/career_catch/models.py`
- `tests/test_models.py`

## 5. 검증 상태

실제 실행한 테스트 명령:

```bash
python -m pytest tests/test_models.py -q
```

실제 결과:

```text
No module named pytest
```

현재 셸의 `python`이 전역 Python을 가리켜 pytest를 찾지 못했습니다. 검증된 가상환경 Python으로 같은 테스트 대상을 다시 실행했습니다.

실제 재실행 명령:

```bash
.\.venv\Scripts\python.exe -m pytest tests/test_models.py -q
```

실제 재실행 결과:

```text
8 passed
```

테스트는 외부 네트워크나 API 키 없이 실행됩니다.

## 6. 아직 시작하지 않은 작업

- 온통청년 API 수집
- API 필드 매핑
- SQLite 저장
- 필터링 로직
- FAISS 인덱싱 및 검색
- OpenAI API 연동
- Streamlit UI
- 데이터 파일 생성

## 7. MVP 제외 및 향후 확장 항목

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

## 8. 정책 추천 안전 문구

추천 결과는 최종 신청 자격을 확정하지 않습니다.

필수 안내 문구:

> 지원 가능성이 높은 정책입니다. 최종 신청 자격과 세부 조건은 반드시 공식 공고문에서 확인해야 합니다.
