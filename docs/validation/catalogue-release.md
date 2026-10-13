# 정책 DB 갱신과 복구

[데이터 검사](README.md) · [API 배포](../api/deployment.md)

운영 DB를 수집기에 직접 지정하지 않고 **격리된 후보 DB 준비 → 감사 → 해시 확인 후 교체** 순서로 갱신한다. 기존 `collect_ontong_pages.py`는 페이지별 upsert 방식으로 유지된다. 네트워크·후속 페이지 오류가 나면 일부 페이지가 적재될 수 있으므로 운영 갱신에는 새 `release_policy_catalogue.py`를 사용한다.

## 1. 후보 준비

저장소 루트에서 실행한다. 원격 수집은 기존 온통청년 키를 환경 변수 또는 `.streamlit/secrets.toml`에서 읽는다. OpenAI 키는 사용하지 않는다.

```powershell
.\.venv\Scripts\python.exe scripts/release_policy_catalogue.py prepare --collect --page-size 10 --max-pages 2 --minimum-policies 20
```

이미 수집한 여러 원본을 사용할 수도 있다. 원본은 읽어서 별도 세대로 복사하며 변경하지 않는다.

```powershell
.\.venv\Scripts\python.exe scripts/release_policy_catalogue.py prepare --snapshot data/raw/page_1.json --snapshot data/raw/page_2.json --minimum-policies 20
```

기본 작업 위치는 Git 제외 경로 `.policy-evidence/catalogues/catalogue-*`다. 성공한 세대에는 `candidate.sqlite3`, 원본 `raw/`, `audit.json`, `release.json`이 있다. 실패한 세대는 진단용으로 남지만 `release.json`을 만들지 않아 publish할 수 없다. 운영 DB는 prepare에 전달하지 않는다.

감사는 최소 정책 수, ID 중복 없음, 사용 가능한 HTTP(S) 출처 URL 형태, 모든 정규화 행과 원본 행 일치, 미래 처리 시각 없음 등을 확인한다. 출처 URL의 공식 기관 여부·최신 공고·이용허락은 별도 확인이다. 기간·서류 등의 결측을 임의로 채우지 않는다.

`release.json`에는 DB·원본 SHA-256, 처리 시각·기준일·정책 수·요청 페이지 범위를 기록한다. raw 원문·감사 자료는 비공개 경로에 보존한다. CLI 성공 출력에는 원문 응답·키·사용자 답변을 포함하지 않는다. `total_available`은 공급자 응답의 총량이고 수집한 건수가 아니다. 기본 2페이지를 전국·서울 정책 전체 목록으로 해석하지 않는다.

## 2. 후보와 현재 DB 확인

prepare 출력의 `directory`, `database_sha256`을 기록하고 해당 세대의 `audit.json`에서 기간·지역·분야·필드 완전성을 확인한다. 마감 정책만 있거나 범위가 맞지 않는 후보를 운영 데이터로 채택하지 않는다. 최소 건수 통과는 초기 정책 20–30개의 범위 확보나 G2 통과를 뜻하지 않는다.

```powershell
.\.venv\Scripts\python.exe scripts/release_policy_catalogue.py inspect --db data/processed/policies.sqlite3
```

현재 DB의 SHA-256·건수·기간·처리 시각 요약을 출력한다. 파일이 없으면 `database_sha256`은 `missing`이며 빈 DB를 만들지 않는다. 준비 자료와 검사 결과를 확인한 뒤 다음 명령의 예시 디렉터리·해시를 실제 값으로 바꾼다.

## 3. 교체

```powershell
.\.venv\Scripts\python.exe scripts/release_policy_catalogue.py publish --directory .policy-evidence/catalogues/catalogue-EXAMPLE --db data/processed/policies.sqlite3 --expected-candidate-sha256 CANDIDATE_SHA256 --expected-current-sha256 CURRENT_SHA256
```

기존 DB가 없는 최초 설치에는 현재 해시 대신 `missing`을 사용한다. 후보 DB·원본 파일 해시를 다시 확인하고 현재 날짜 기준으로 원본 대조·최소 건수를 재검사한다. 현재 DB가 검사 후 바뀌면 거절한다. 기존 정책 ID가 후보에서 빠지면 기본적으로 교체를 거절한다. 범위를 의도적으로 줄일 때만 누락 ID를 확인한 후 `--allow-removals`를 명시한다.

교체 직전에 운영 DB 옆 `catalogue-backup-*/previous.sqlite3`에 이전 DB를 복사하고 해시를 확인한다. 후보를 대상과 같은 디렉터리의 임시 파일에 복사·flush/fsync한 뒤 `os.replace`로 교체한다. 소스는 유지하고, 기존 파일 권한을 보존한다. POSIX에서는 기존 소유자·그룹 보존이 불가능하면 교체 전에 실패한다. 성공 출력에는 새 DB 해시·이전 해시·백업 경로가 있다. 교체 완료 후 lock 정리가 실패하면 성공 상태와 `release_lock_retained` 경고를 함께 반환해 실제 교체를 실패로 오인하지 않는다.

동시 갱신 CLI는 대상별 release lock으로 차단한다. SQLite `-wal`, `-shm`, `-journal` 파일이 있으면 준비 중인 쓰기 상태로 보고 교체를 거절한다. **기존 Streamlit·수집기 등 DB writer는 갱신 동안 중지해야 한다.** 이 lock을 따르지 않는 외부 writer와 파일 시스템 전원 장애까지 원자성을 보장하지 않는다. Windows에서 열린 파일 때문에 교체가 거절되면 기존 DB를 유지한다. 중단으로 lock이 남으면 실행 중인 갱신이 없는지 확인한 후 해당 lock만 정리한다.

일반 API는 다음 요청에서 읽기 전용 연결을 새로 연다. Docker에 DB 한 파일을 bind mount한 경우에는 호스트 파일 교체 후 컨테이너를 다시 생성해 새 파일을 연결한다. 기존 mount가 이전 파일을 유지할 수 있으므로 컨테이너의 `/ready` 통과만으로 새 세대 반영을 판단하지 않는다.

## 4. 복구

```powershell
.\.venv\Scripts\python.exe scripts/release_policy_catalogue.py restore --backup data/processed/catalogue-backup-EXAMPLE/previous.sqlite3 --db data/processed/policies.sqlite3 --expected-backup-sha256 PREVIOUS_SHA256 --expected-current-sha256 CANDIDATE_SHA256
```

백업과 현재 DB의 예상 해시를 확인하고 읽을 수 있는 비어 있지 않은 백업만 복구한다. 복구 직전의 현재 DB도 새 백업에 보존한다. 이것은 이전 버전 복구이며 원본 공고를 최신 상태로 만드는 작업이 아니다.

## 검증 범위

합성 snapshot·페이지 응답으로 성공·후속 수집 실패·잘못된 JSON·빈 데이터·출처 누락·최소 건수·중복 ID·후보/원본/현재 해시 변경·경로 이탈·DB sidecar·동시 lock·파일 교체 실패·정책 삭제 옵션·백업 복구를 검사한다. DB 값을 바꾸고 해시를 재계산해도 원본 대조가 교체를 막는지 확인한다. 실제 FastAPI의 정책명이 교체·복구 뒤 갱신되는지도 검사한다.

실시간 온통청년 수집, 최신 정책 목록 확보, 공식 공고 확인, Linux 권한·Docker mount·운영 파일 시스템은 각각 별도 검증 대상이다. 처리 시각은 적재 시각이며 원본 공고의 확인일로 표현하지 않는다.
