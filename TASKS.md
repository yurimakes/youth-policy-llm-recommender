# TASKS.md

## 1. 현재 상태

이 저장소는 현재 문서 및 최소 개발 환경 설정 준비 단계입니다.

- 저장소 루트: `career-catch-4/`
- Python 버전: 3.10
- 애플리케이션 코드: 아직 구현되지 않음
- 데이터 수집 파이프라인: 아직 구현되지 않음
- 정제 데이터, SQLite 데이터베이스, FAISS 산출물: 아직 생성되지 않음
- 자동화 테스트: 아직 구현되지 않음
- 최소 설정 파일: `requirements.txt`, `.env.example` 생성됨
- 패키지 설치 및 호환성 검증: 아직 수행되지 않음
- 배포: 아직 수행되지 않음

이전 일일 보고서나 계획 문서는 실제 코드, 데이터, 테스트, 배포 산출물이 존재한다는 근거로 보지 않습니다.

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

**작업:** 최소 프로젝트 설정 파일 생성 및 검토

**상태:** 사용자 검토 및 승인 대기 중입니다.

이번 작업에서는 `requirements.txt`와 `.env.example`만 새로 생성하고, `README.md`와 `TASKS.md`에 현재 상태를 반영합니다. 패키지 설치, 명령 실행, 애플리케이션 코드 생성, 데이터 파일 생성, 테스트 파일 생성, 폴더 생성은 하지 않습니다.

## 4. 현재 작업의 완료 조건

- `requirements.txt`에 승인된 외부 Python 패키지만 포함합니다.
- `requirements.txt`에 SQLite, pathlib 같은 Python 표준 라이브러리를 포함하지 않습니다.
- 패키지 버전을 임의로 고정하지 않습니다.
- `.env.example`에 `OPENAI_API_KEY`, `OPENAI_CHAT_MODEL`, `OPENAI_EMBEDDING_MODEL`만 포함합니다.
- `.env.example`에 실제 API 키나 임의의 가짜 키를 넣지 않습니다.
- `README.md`에 설정 파일 생성 사실과 설치·실행·테스트 미검증 상태를 반영합니다.
- `TASKS.md`에 현재 작업과 검증 상태를 반영합니다.
- `AGENTS.md`, `PROJECT_SPEC.md`, `.gitignore`는 수정하지 않습니다.
- app.py, Python 코드, 데이터 파일, 테스트 파일, 폴더를 생성하지 않습니다.
- 변경 파일 목록과 전체 `git diff`를 사용자에게 보고합니다.

## 5. 검증 상태

이번 작업에서는 패키지 설치, 테스트, 컴파일, Streamlit 실행 명령을 실행하지 않았습니다.

아래 명령은 관련 파일이 생성되고 구현 작업이 승인된 뒤 사용할 예정입니다.

```bash
python -m pytest
python -m compileall app.py src
python -m streamlit run app.py
```

이 명령들은 아직 이 저장소에서 검증된 사용법으로 보지 않습니다.

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

