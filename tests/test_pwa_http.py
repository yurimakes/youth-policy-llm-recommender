"""설치 리소스의 실제 HTTP 경로·MIME·아이콘·캐시 경계를 검증합니다."""

from functools import partial
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import struct
import sys
from threading import Thread
from urllib.request import urlopen

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
from scripts.build_demo import build
from scripts.serve_demo import DemoHandler
from youth_policy.api_app import create_app


def check_resources(fetch):
    response = fetch("/manifest.webmanifest")
    assert response[0] == "application/manifest+json"
    manifest = json.loads(response[1])
    assert manifest["start_url"] == "/demo/" and manifest["display"] == "standalone"
    assert manifest["scope"] == "/" and not manifest["prefer_related_applications"]
    assert {icon["sizes"] for icon in manifest["icons"]} == {"192x192", "512x512"}
    for icon in manifest["icons"]:
        media, body = fetch(icon["src"])
        assert media == "image/png" and body[:8] == b"\x89PNG\r\n\x1a\n"
        width, height = struct.unpack(">II", body[16:24])
        assert icon["sizes"] == f"{width}x{height}"
    media, body = fetch("/demo/assets/apple-touch-icon.png")
    assert media == "image/png" and struct.unpack(">II", body[16:24]) == (180, 180)
    media, body = fetch("/sw.js")
    assert media == "text/javascript" and body == (ROOT / "demo/sw.js").read_bytes()
    media, body = fetch("/offline.html")
    assert media == "text/html" and b'data-offline-page="jiwon-basket"' in body
    assert b"/demo/assets" not in body  # Notice has no network dependencies.


def test_actual_api_serves_installation_without_loading_policy_db():
    def forbidden_provider():
        raise AssertionError("installation assets must not read policy data")
    with TestClient(create_app(policy_provider=forbidden_provider)) as client:
        def fetch(path):
            response = client.get(path)
            assert response.status_code == 200
            assert response.headers["Cache-Control"] == "no-store"
            return response.headers["Content-Type"].split(";")[0], response.content
        check_resources(fetch)
        html = client.get("/demo/").text
        assert 'href="/manifest.webmanifest"' in html and 'data-runtime="api"' in html
        assert 'id="install-app"' in html
        assert client.get("/demo/assets/not-public.png").status_code == 404


def test_static_preview_serves_all_installation_resources(tmp_path):
    build(tmp_path)
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(DemoHandler, directory=str(tmp_path)))
    worker = Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
    worker.start()
    try:
        def fetch(path):
            with urlopen(f"http://127.0.0.1:{server.server_port}" + path, timeout=2) as response:
                assert response.status == 200 and response.headers["Cache-Control"] == "no-store"
                return response.headers.get_content_type(), response.read()
        check_resources(fetch)
        assert b'data-runtime="mock"' in fetch("/demo/")[1]
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)
