# 데모 안내

공개 주소: [지원장바구니](https://jiwon-basket.vercel.app/)

로그인·API 키·DB 설치 없이 화면 흐름을 체험한다. **공개 버전은 가상 정책 6개와 가상 비교 조건을 사용한다. 실제 신청 자격·현재 모집 여부를 판정하는 서비스가 아니다.** 실제 제도 참고자료는 별도 목록이며 공식 링크·확인일·기간 주의사항을 표시한다.

## 2분 시연

1. ‘쉬고 있어요’ → 다음 → ‘생활비 부담 줄이기’ → 다음.
2. 서울 거주 질문에 ‘네’ → 만 나이 24 입력. 상황 카드로 미취업을 추정하지 않는다.
3. 청년 활동지원금과 청년 월세 지원을 담고 ‘2개 담기’를 누른다.
4. 상세 확인을 선택해 가구·취업 상태·편한 시간에 답한다. 모르면 건너뛰고, 잠시 멈췄다가 이어갈 수 있다.
5. 개별 조건과 남은 확인사항을 살펴보고 ‘담은 지원 준비하기’로 이동한다.
6. 준비 체크 3개를 직접 표시하고 ‘상담 요약서’를 연다. 복사하거나 인쇄창에서 PDF로 저장한다.
7. 도움말의 ‘공식 정책 참고자료’에서 실제 공고를 연다. 가상 정책의 근거인 것처럼 설명하지 않는다.

## 핵심 확인 시나리오

| 시나리오 | 확인 방법 | 기대 동작 |
|---|---|---|
| 기본 경로 | 위 시연 | 결과와 준비까지 연결 |
| 모름·건너뛰기 | 카드·나이·지역을 건너뛰기 | 정보 부족을 유지하고 후보·다음 확인 안내 |
| 상세 거절 | 상세 제안에서 ‘지금 결과로 볼게요’ | 기본 후보와 공식 참고자료 유지 |
| 답변 수정 | 만 나이를 37로 수정하거나 취업 상태를 명시 | 가상 조건의 명확한 미충족 후보 제외, 모름으로 수정하면 재평가 |
| 후보 없음·오류 | 도움말 → 체험 상황 선택, 다음 전환 진행 | 빈 화면 대신 안내; 오류 전 답변 유지, 기본 흐름으로 바꿔 재시도 |

체험 상황 설정은 다음 진행 요청부터 반영된다. 초기 화면에서 ‘후보 없음’을 선택하면 질문이 줄어들고 바로 빈 결과로 갈 수 있다. 오류 설정 후 요청이 실패하면 설정을 ‘기본 흐름’으로 바꾸고 ‘다시 시도하기’를 누른다.

## 로컬 실제 API 모드

기존 SQLite 데이터가 필요하다. 실행 중인 서버는 Ctrl+C로 종료한 후 최신 코드로 다시 시작한다.

```powershell
git switch main
git pull --ff-only origin main
.\.venv\Scripts\python.exe -m pip install -r requirements-api.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

http://127.0.0.1:8000/demo 에서 실제 API 응답으로 같은 화면을 사용한다. 실제 API는 기존 나이·지역·취업 상태와 선호 계약만 받는다. 가상 데모 전용 가구 질문을 실제 API에 추가하지 않았다. 지역은 실제 5자리 코드를 입력할 수 있고 답변 수정에서도 직접 입력을 지원한다.

다른 PowerShell 창에서 실제 서버·DB를 확인한다.

```powershell
.\.venv\Scripts\python.exe scripts/check_intake_api.py --require-detail
```

## 동일한 공개 체험을 로컬에서 보기

```powershell
.\.venv\Scripts\python.exe scripts/build_demo.py --output demo-build
.\.venv\Scripts\python.exe scripts/serve_demo.py --directory demo-build --port 8080
```

http://127.0.0.1:8080 에서 목데이터 모드가 열린다. 생성 폴더는 Git에서 제외한다. Node가 있으면 다음 테스트를 실행한다.

```powershell
node --test tests/test_demo_client.mjs tests/test_mock_demo.mjs
```

## 데이터와 문서

상담 요약과 문서 초안은 입력·확인사항을 조합한다. 외부 LLM 호출·서류 자동 발급·신청 제출·상담 예약은 수행하지 않는다. 입력·장바구니·체크 표시는 메모리에서만 유지되고 새로고침하면 초기화된다. 준비 완료 표시는 기관의 확인이나 신청 완료를 뜻하지 않는다.

## 자동 브라우저 검증과 캡처

GitHub Actions의 Demo checks는 Chromium에서 5개 핵심 시나리오와 실제 FastAPI 합성 정책 연결을 확인하고 `demo-browser-captures` 아티팩트에 화면 PNG와 상담 요약 PDF를 저장한다. 실제 사용자 정보가 아닌 합성 입력만 사용한다. [워크플로 실행 목록](https://github.com/yurimakes/youth-policy-llm-recommender/actions/workflows/demo-checks.yml)에서 실행별 결과와 생성된 파일을 확인할 수 있다.

수동 시연은 공개 주소에서 진행하면 된다. 로컬 자동 브라우저 검증을 실행하려면 개발용 Node와 `npm install --no-save --package-lock=false @playwright/test`, `npx playwright install chromium`가 필요하다. 목데이터를 `demo-build`에 빌드한 후 Windows PowerShell에서 `$env:TEST_PYTHON=".venv/Scripts/python.exe"`를 설정하고 `npx playwright test --config tests/demo_browser.config.mjs`를 실행한다. 실제 Python 서버 테스트는 격리된 합성 정책으로 자동 시작하며 운영 DB를 사용하지 않는다.
