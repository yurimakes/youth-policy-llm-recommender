"""생성한 목데이터 데모를 명시적 MIME 타입과 loopback HTTP로 미리 봅니다."""
from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


class DemoHandler(SimpleHTTPRequestHandler):
    """OS의 .mjs 분류와 관계없이 허용한 데모 자산만 제공합니다."""

    extensions_map = {".mjs": "text/javascript", ".html": "text/html; charset=utf-8",
                      ".css": "text/css; charset=utf-8", ".json": "application/json; charset=utf-8",
                      ".woff2": "font/woff2", ".txt": "text/plain; charset=utf-8"}

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        assets = {"style.css", "app.mjs", "client.mjs", "mock.mjs", "official-policies.json",
                  "Pretendard-Regular.woff2", "Pretendard-SemiBold.woff2",
                  "Pretendard-ExtraBold.woff2", "Pretendard-OFL.txt"}
        if path not in {"/", "/index.html", "/demo", "/demo/", "/demo/index.html"} and path not in {
            "/demo/assets/" + name for name in assets
        }:
            self.send_error(404)
            return
        super().do_GET()

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main() -> None:
    """폴더의 체험 모드를 확인한 뒤 로컬 서버를 실행합니다."""
    parser = argparse.ArgumentParser(description="Preview the built, labelled mock demo")
    parser.add_argument("--directory", type=Path, default=Path("demo-build"))
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    index = args.directory / "index.html"
    if not index.is_file() or 'data-runtime="mock"' not in index.read_text(encoding="utf-8"):
        parser.error("먼저 build_demo.py로 목데이터 화면을 생성하세요.")
    server = ThreadingHTTPServer(("127.0.0.1", args.port), partial(DemoHandler, directory=str(args.directory.resolve())))
    print(f"Demo preview: http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
