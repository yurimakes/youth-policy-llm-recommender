"""점검 CLI를 로컬 HTTP 참조 서버로 검증합니다. FastAPI 기동 검증과는 별개입니다."""

from contextlib import contextmanager, redirect_stdout
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import sys
from threading import Thread
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from test_intake import policy
from check_intake_api import main
from youth_policy.api_smoke import LocalApiClient, run_smoke
from youth_policy.intake import start_intake
from youth_policy.intake_contract import apply_action, response_payload, state_from_payload


TODAY = date(2026, 10, 7)


@contextmanager
def reference_server(*, records=None, failure=None):
    """표준 라이브러리 HTTP 서버에 실제 순수 진행 계약을 연결한 테스트 전용 어댑터입니다."""
    records = (policy(),) if records is None else records

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_GET(self):
            self.handle_json()

        def do_POST(self):
            self.handle_json()

        def handle_json(self):
            status = 200
            if self.path == "/health":
                payload = {"status": "ok", "api_version": "1"}
            elif self.path == "/ready":
                payload = {"status": "ready", "policy_count": len(records)}
            elif self.path == "/openapi.json":
                payload = {"paths": {path: {} for path in (
                    "/health", "/ready", "/api/v1/intake/start", "/api/v1/intake/transition")}}
            elif self.path.startswith("/api/v1/intake/"):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                if self.path.endswith("/start"):
                    state = start_intake(body.get("start_mode", "situation"))
                else:
                    state = apply_action(state_from_payload(body["state"]), body["action"],
                                         records, reference_date=TODAY)
                payload = response_payload(state, records, reference_date=TODAY)
            else:
                status, payload = 404, {"error": "unknown"}
            if failure == "unavailable" and self.path == "/ready":
                status, payload = 503, {"error": {"message": "PRIVATE-ERROR-BODY"}}
            if failure == "redirect":
                status = 302
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            if failure != "cache":
                self.send_header("Cache-Control", "no-store")
            if failure == "redirect":
                self.send_header("Location", "https://example.test/should-not-be-contacted")
            self.end_headers()
            self.wfile.write(b"PRIVATE-NOT-JSON" if failure == "json" else json.dumps(payload).encode())

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


class SmokeTests(unittest.TestCase):
    def test_http_reference_flow_covers_skip_correction_decline_and_resume(self):
        with reference_server() as url:
            checks = run_smoke(LocalApiClient(url))
        self.assertEqual(len(checks), 6)
        self.assertEqual({c.status for c in checks}, {"PASS"})

    def test_closed_policy_is_no_candidate_and_detail_checks_are_skipped(self):
        closed = policy(application_start=date(2026, 9, 1), application_end=date(2026, 9, 30))
        with reference_server(records=(closed,)) as url:
            checks = run_smoke(LocalApiClient(url))
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(["--base-url", url, "--require-detail"])
        self.assertEqual(code, 2)
        self.assertEqual(sum(c.status == "SKIP" for c in checks), 2)
        self.assertFalse(any(c.status == "FAIL" for c in checks))
        self.assertEqual(json.loads(output.getvalue())["skipped"], 2)

    def test_data_unavailable_is_failure_without_server_error_body(self):
        with reference_server(failure="unavailable") as url:
            checks = run_smoke(LocalApiClient(url))
        self.assertEqual(checks[-1].status, "FAIL")
        self.assertIn("503", checks[-1].message)
        self.assertNotIn("PRIVATE-ERROR-BODY", repr(checks))

    def test_missing_no_store_header_is_failure(self):
        with reference_server(failure="cache") as url:
            checks = run_smoke(LocalApiClient(url))
        self.assertEqual(checks[-1].status, "FAIL")
        self.assertIn("no-store", checks[-1].message)

    def test_redirect_is_not_followed(self):
        with reference_server(failure="redirect") as url:
            checks = run_smoke(LocalApiClient(url))
        self.assertEqual(checks[-1].status, "FAIL")
        self.assertIn("302", checks[-1].message)

    def test_invalid_json_is_failure_without_raw_response(self):
        with reference_server(failure="json") as url:
            checks = run_smoke(LocalApiClient(url))
        self.assertEqual(checks[-1].status, "FAIL")
        self.assertNotIn("PRIVATE-NOT-JSON", repr(checks))

    def test_external_urls_credentials_and_invalid_timeout_rejected(self):
        for url in ("https://127.0.0.1:8000", "http://example.test", "http://u:p@localhost:8000",
                    "http://localhost:8000/path", "http://localhost:8000?x=1", "http://localhost:invalid"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                LocalApiClient(url)
        for timeout in (0, -1, float("nan"), float("inf")):
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                LocalApiClient("http://localhost:8000", timeout=timeout)

    def test_missing_notice_is_contract_failure(self):
        class MissingNoticeClient:
            def request(self, path, body=None):
                if path == "/health":
                    return {"status": "ok", "api_version": "1"}
                if path == "/ready":
                    return {"status": "ready", "policy_count": 1}
                if path == "/openapi.json":
                    return {"paths": {p: {} for p in ("/health", "/ready", "/api/v1/intake/start", "/api/v1/intake/transition")}}
                return {"state": {"profile": {"age": None}}}

            def transition(self, response, action):
                return {"state": {"profile": {"age": None}, "stage": "results"},
                        "next_question": None, "data_status": "ready"}

        checks = run_smoke(MissingNoticeClient())
        self.assertEqual(checks[-1].status, "FAIL")
        self.assertEqual(checks[-1].message, "response does not match the intake contract")


if __name__ == "__main__":
    unittest.main()
