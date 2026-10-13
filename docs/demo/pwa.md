# 홈 화면 설치와 연결 끊김

[데모 안내](README.md) · [실제 API 실행·배포](../api/deployment.md)

웹앱 manifest와 설치 아이콘을 제공한다. 공개 정적 데모와 실제 API의 `/demo/` 화면 모두 같은 설치 구성을 사용한다. 설치해도 공개 사이트는 합성 정책 체험이며 실제 API 정책으로 전환되는 것은 아니다.

## 설치

‘이용 안내’를 열면 홈 화면 설치 안내가 있다. 브라우저가 설치 이벤트를 제공하면 ‘홈 화면에 추가하기’가 표시된다. 사용자가 눌러 설치를 선택한다. 이벤트가 없는 브라우저는 브라우저 메뉴의 설치·홈 화면 추가 기능을 사용한다.

iPhone Safari에서는 공유 메뉴 → ‘홈 화면에 추가’를 선택한다. 브라우저·OS에 따라 설치 방식이 달라진다. 설치 기능은 HTTPS 또는 localhost·loopback 개발 환경에서 사용한다. 로컬 주소의 앱은 로컬 서버가 실행 중이어야 한다.

## 데이터와 오프라인

- 답변·장바구니·완료 체크는 실행 중인 화면 메모리에만 유지한다. 새로 열거나 새로고침하면 초기화된다.
- 연결이 끊기면 연결 상태 안내를 표시한다. 현재 답변을 유지하고 연결 후 사용자가 요청을 다시 시도한다.
- 오프라인에서 페이지를 다시 열면 고정된 연결 안내를 표시한다. 정책 후보·자격·모집 상태나 이전 답변을 보여주지 않는다.
- Cache Storage에는 `/offline.html` 한 파일만 저장한다. 정책 API·공식 참고 목록·앱 HTML·문서·사용자 입력은 저장하지 않는다. API와 정적 자산 요청은 서비스 워커가 가로채지 않는다.
- 서비스 워커가 준비되지 않았거나 저장소가 차단되면 일반 브라우저로 이용할 수 있다. 이 경우 오프라인 안내가 없을 수 있다.

온라인 HTTP 오류를 오프라인 정책 결과로 바꾸지 않는다. 연결 배너는 브라우저의 online/offline 신호다. online 표시가 API 서버 정상 응답을 보장하지 않으며 API 오류·timeout은 기존 오류 안내와 재시도 경로를 사용한다.

## 업데이트

새 서비스 워커가 대기 중이면 ‘이용 안내’에 ‘새 버전 열기’가 표시된다. **답변과 담은 지원이 초기화된다는 안내를 확인한 뒤** 적용한다. 취소하면 현재 진행을 유지한다. 설치·연결 변경·다른 탭의 업데이트 때문에 현재 입력 화면을 자동 새로고침하지 않는다.

## 구현과 검사

`demo/manifest.webmanifest`, `sw.js`, `offline.html`, `pwa.mjs`, PNG 아이콘을 사용한다. API와 정적 빌드·미리보기에서 실제 경로·MIME을 검사한다. 기존 환경의 Pillow로 `scripts/build_app_icons.py`를 실행해 아이콘을 재생성할 수 있다. 웹앱 실행에는 Pillow가 필요하지 않다.

Chromium에서는 manifest·서비스 워커·단일 안내 캐시·사용자 입력 저장 없음·연결 상태·오프라인 재진입·재접속 후 초기화를 검사한다. 설치 버튼 검사는 주입한 이벤트를 사용한다. 실제 OS 설치창, iPhone Safari 설치·standalone 실행과 기기별 접근성은 별도 수동 검증 대상이다. 이 구현만으로 G5 운영 검증 완료를 주장하지 않는다.

공식 참고: [MDN 설치 요건](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Making_PWAs_installable), [서비스 워커 fetch](https://developer.mozilla.org/en-US/docs/Web/API/ServiceWorkerGlobalScope/fetch_event), [Apple iPhone 사용 설명서](https://support.apple.com/guide/iphone/turn-a-website-into-an-app-iph42ab2f3a7/ios).
