# 청년 맞춤 정책 추천 작업 현황

## 현재 작업

- 기준일: 2026-07-02
- 단계: 최종 제출물 정리
- 상태: 로컬 MVP 핵심 기능 구현 및 검증 완료

## 완료 사항

### 데이터 수집 및 저장

- [x] 온통청년 OPEN API 인증키 승인
- [x] 실제 청년정책 API 호출
- [x] 2페이지, 총 20건 수집
- [x] 페이지별 raw JSON 및 메타데이터 보존
- [x] 실제 응답을 `PolicyRecord`로 변환
- [x] SQLite 정책 20건 적재 및 재조회
- [x] 정책 ID 기준 중복 방지
- [x] 실제 API 키, raw 데이터, SQLite 파일 Git 제외

### 규칙 기반 평가

- [x] 신청 상태 판정
- [x] 연령 판정
- [x] 지역 판정
- [x] 취업 상태 판정
- [x] 소득 조건 안전 판정
- [x] `MATCH`, `UNKNOWN`, `NO_MATCH` 분류
- [x] 여러 정책 일괄 평가
- [x] 정책별 판정 이유 보존

### Streamlit UI

- [x] 단일 Streamlit 앱 구현
- [x] 사용자 화면 명칭을 `청년 맞춤 정책 추천`으로 통일
- [x] 나이 입력
- [x] 시·도 / 시·군·구 2단계 지역 선택
- [x] 실제 5자리 `region_code` 평가 연결
- [x] 취업 상태 입력
- [x] 자연어 관심사 입력
- [x] 평가 요약 카드
- [x] 정책 상세 카드와 공식 출처 표시
- [x] 최종 자격 확인 안내 표시

### 검색 및 생성형 설명

- [x] `MATCH`, `UNKNOWN` 후보 구성
- [x] OpenAI 임베딩 생성
- [x] FAISS Top-5 검색
- [x] 벡터 위치와 `policy_id` 매핑 유지
- [x] 검색된 공식 정책만 LLM에 전달
- [x] 추천 이유 및 확인사항 생성
- [x] 누락 정보 `확인 필요` 처리
- [x] AI 오류 시 규칙 결과 및 검색 결과 유지

### 테스트 및 Git

- [x] 검색 단위 테스트 3개 통과
- [x] LLM 서비스 단위 테스트 2개 통과
- [x] 전체 테스트 `122 passed`
- [x] `compileall app.py src` 성공
- [x] Streamlit 로컬 실행 성공
- [x] 실제 FAISS 검색 및 OpenAI 설명 화면 확인
- [x] GitHub `main` 브랜치 푸시 완료

## 남은 작업

- [ ] 최종 실행 화면 캡처 선별
- [ ] 결과보고서 작성
- [ ] 활동사진 및 관련 자료 캡션 정리
- [ ] 문서 내용과 실제 화면 최종 대조
- [ ] 문서 변경분 커밋 및 GitHub 푸시
- [ ] 필요 시 Streamlit Community Cloud 배포

## 검증 기록

### 2026-07-02

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_retrieval.py tests/test_llm_service.py -q
```

```text
5 passed
```

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

```text
122 passed
```

```powershell
.\.venv\Scripts\python.exe -m compileall app.py src
```

```text
성공
```

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

```text
로컬 실행 및 실제 AI 추천 설명 확인
```

## 개발 이력

### 2026-06-29 당시

- [x] 정책 데이터 모델 구현
- [x] 코드북 구현
- [x] 공식 예시 JSON 파싱
- [x] SQLite 저장소 구현
- [x] 규칙 기반 일괄 평가 구현
- [x] 당시 전체 테스트 `81 passed`

### 2026-07-01

- [x] 실제 API 호출 및 snapshot 저장
- [x] SQLite 파이프라인 연결
- [x] 여러 페이지 수집
- [x] Streamlit UI 구현

### 2026-07-02

- [x] OpenAI 임베딩 + FAISS 검색 구현
- [x] OpenAI 추천 설명 구현
- [x] 전체 통합 검증
