# 실제 API 실행·배포 준비

[실행 안내](../getting-started/README.md) · [API 규격](intake-v1.md)

FastAPI와 실제 API 모드 화면을 **같은 origin**에서 실행한다. 루트 `/`는 `/demo`로 연결되고 상대 경로 요청은 같은 서버의 `/api/v1/intake/*`로 간다. 공개 Vercel 사이트는 계속 합성 정책 데모다. 이 문서는 공개 API 배포 완료나 G5 통과 증빙이 아니다.

## 실행기

기존 Streamlit 환경과 별도로 Intake 서비스 의존성만 설치할 수 있다.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-service.txt
$env:POLICY_DB_PATH = (Resolve-Path data/processed/policies.sqlite3).Path
.\.venv\Scripts\python.exe scripts/run_intake_api.py
```

DB를 읽기 전용으로 조회하고, 파일 누락·잘못된 형식·빈 DB이면 서버를 열지 않고 종료 코드 2를 반환한다. 레코드 존재는 최신 공고·현재 신청 가능·coverage를 보장하지 않는다. [데이터 점검](../validation/README.md)과 공식 공고 확인을 함께 수행한다. 기존 `uvicorn api:app` 실행은 유지되며 누락 DB에서 `/ready`와 후보 요청은 503을 반환한다.

| 설정 | 실행기 기본값 | 용도 |
|---|---|---|
| `POLICY_DB_PATH` | `data/processed/policies.sqlite3` | 외부 SQLite. 상대 경로는 저장소 루트 기준 |
| `API_HOST` | `127.0.0.1` | bind 주소. 컨테이너 기본값은 `0.0.0.0` |
| `PORT` | `8000` | 플랫폼 지정 포트. 1–65535 정수 |
| `API_CORS_ORIGINS` | localhost 개발 origin | 정확한 origin 목록. 같은 origin 배포에서는 빈 값 |
| `POLICY_EXPLANATION_AI_ENABLED` | 설정 없으면 꺼짐 | `1`이고 모델·키가 준비된 경우에만 활성화 |

`--host`, `--port`는 환경 변수보다 우선한다. `.env`와 Streamlit secrets는 실행기가 자동으로 읽지 않는다. AI 설정은 [설명 API](intake-v1.md#출처를-연결한-설명)를 따른다. AI 없이 질문·조건 판정·기록된 근거가 동작한다. 외부 모델은 사용자 요청당 최대 1회, 서버 timeout 5초, 재시도 0회, 출력 상한 256토큰이다.

## Docker 실행

Docker가 설치된 환경에서 저장소 루트 기준으로 실행한다. `.dockerignore`는 실행 소스만 허용하고 Dockerfile은 필요한 경로만 복사한다. 데이터와 키는 이미지에 포함하지 않는다. 준비·점검한 정책 DB를 별도 파일로 읽기 전용 연결한다.

```powershell
docker build -t jiwon-basket-api:local .
$policyDatabase = (Resolve-Path data/processed/policies.sqlite3).Path
docker run --rm --name jiwon-basket-api -p 127.0.0.1:8000:8000 --mount "type=bind,source=$policyDatabase,target=/data/policies.sqlite3,readonly" jiwon-basket-api:local
```

[실제 API 화면](http://127.0.0.1:8000/)을 연다. 이미지는 UID/GID `10001:10001`로 실행한다. Linux 호스트에서는 이 UID가 DB와 상위 경로를 읽을 수 있어야 한다. SQLite에는 쓰기 권한을 부여하지 않는다. 갱신은 별도 수집·감사를 완료한 새 DB 파일로 교체한 뒤 서버 준비 상태를 다시 점검한다.

Docker healthcheck는 **`/ready`**를 조회한다. DB를 읽을 수 없거나 비어 있으면 준비 실패다. Docker healthcheck를 지원하지 않는 플랫폼에서는 readiness 경로를 `/ready`로 지정한다. `PORT`를 바꾸면 컨테이너 포트 연결도 바꾼다. 내부 `PORT`를 healthcheck에 동일하게 적용한다.

공개 호스팅에는 이 이미지 또는 `python scripts/run_intake_api.py` 시작 명령, `API_HOST=0.0.0.0`, 별도 정책 DB 경로와 HTTPS origin이 필요하다. 프록시 헤더와 access log는 실행기에서 기본적으로 사용하지 않는다. 플랫폼의 TLS와 ingress 설정으로 HTTPS를 제공한다. 실제 AI를 켠 공개 서비스의 호출 접근 제어·비용 한도는 추가 운영 검증 대상이다.

## 연결 검사

서버를 실행한 채 다른 터미널에서 합성 답변으로 점검한다. 실제 사용자 답변은 사용하지 않고 원문 응답·키·입력을 저장하거나 출력하지 않는다.

```powershell
.\.venv\Scripts\python.exe scripts/check_intake_api.py --require-detail
```

지정한 공개 HTTPS API를 검사하려면 배포 모드를 명시한다.

```powershell
.\.venv\Scripts\python.exe scripts/check_intake_api.py --deployment --base-url https://your-api.example.com --require-detail
```

주소는 예시다. 기본 모드는 loopback HTTP만 허용한다. 배포 모드는 경로·query·인증 정보 없는 HTTPS origin만 받는다. 환경 프록시와 리다이렉트는 사용하지 않아 다른 origin으로 검사를 옮기지 않는다. PASS/FAIL/SKIP/WARN을 구분하고 `--require-detail` 사용 시 데이터 때문에 상세 검사가 생략되면 종료 코드 2를 반환한다. 서버·DB·진행 계약 검사이며 실시간 공고나 모델 품질 검증이 아니다.

## 느린 요청과 복구

실제 API 화면은 POST 시작부터 JSON 읽기까지 10초로 제한한다. 시간이 지나면 요청을 취소하고 이전 성공 응답·답변·선택을 유지한다. 사용자가 ‘다시 시도하기’를 눌러야 진행 요청을 다시 보낸다. 늦게 도착한 응답은 새 상태를 덮어쓰지 않는다. 근거 조회에도 같은 시간 제한을 적용하며, 실패하면 이전 근거 표시를 지우고 답변·후보를 유지한다. AI 요청을 자동 반복하지 않는다. 브라우저 요청 취소가 서버나 모델에서 이미 처리한 요청의 비용 취소를 보장하지는 않는다.

## 검증 범위

자동 검사는 합성 SQLite를 외부 경로에 두고 패키징된 코드에서 실제 서버를 시작한다. 다른 작업 디렉터리에서도 시작·화면·JS 모듈·진행·readiness가 동작하는지, DB 제거 후 readiness가 실패하는지, DB 내용이 바뀌지 않는지 확인한다. 브라우저에서는 응답 지연을 주입해 시간 제한·답변 유지·명시적 재시도를 확인한다.

Docker 이미지 빌드·Linux 실행, 공개 HTTPS endpoint, 실제 정책 최신성, 외부 모델 응답·비용은 각각 해당 환경에서 별도로 검증해야 한다. 운영 릴리스에는 이미지 digest와 의존성 버전·데이터 snapshot hash·source commit을 함께 고정한다. 현재 기본 이미지 태그와 일부 의존성은 범위를 사용하므로 완전히 고정된 운영 릴리스가 아니다.

공식 참고: [Dockerfile](https://docs.docker.com/reference/dockerfile/), [dockerignore](https://docs.docker.com/build/building/context/#dockerignore-files), [Uvicorn 배포](https://uvicorn.dev/deployment/).
