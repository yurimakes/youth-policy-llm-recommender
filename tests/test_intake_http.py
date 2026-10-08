"""test_intake_http.py

실제 FastAPI TestClient로 상태 전환·오류·CORS·캐시 헤더를 검증합니다.
"""

from datetime import date
from importlib.util import find_spec
import mimetypes
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from test_intake import policy, basic_state
from youth_policy.api_config import ApiSettings
from youth_policy.intake import start_intake
from youth_policy.intake_contract import state_to_payload
from youth_policy.policy_repository import PolicyDataUnavailable


HAS_HTTP_DEPS = all(find_spec(name) is not None for name in ("fastapi", "httpx", "pydantic"))
if HAS_HTTP_DEPS:
    from fastapi.testclient import TestClient
    from youth_policy.api_app import create_app


@unittest.skipUnless(HAS_HTTP_DEPS, "HTTP 실행 검증에는 requirements-api.txt 설치 필요")
class HttpTests(unittest.TestCase):
    def setUp(self):
        self.settings = ApiSettings(Path("unused.sqlite3"), ("http://localhost:5173",))
        self.client = TestClient(create_app(settings=self.settings, policy_provider=lambda: (policy(),),
                                             date_provider=lambda: date(2026, 10, 7)))
        self.addCleanup(self.client.close)

    def transition(self, state, action):
        return self.client.post("/api/v1/intake/transition", json={"state": state, "action": action})

    def test_health_ready_and_no_cache(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(self.client.get("/ready").json()["policy_count"], 1)

    def test_demo_page_and_local_assets_are_served_without_caching(self):
        for path, content_type in (("/demo", "text/html"), ("/demo/", "text/html"),
                                   ("/demo/assets/style.css", "text/css"),
                                   ("/demo/assets/app.mjs", "javascript"),
                                   ("/demo/assets/client.mjs", "javascript"),
                                   ("/demo/assets/mock.mjs", "javascript"),
                                   ("/demo/assets/official-policies.json", "application/json"),
                                   ("/demo/assets/Pretendard-Regular.woff2", "font/woff2"),
                                   ("/demo/assets/Pretendard-SemiBold.woff2", "font/woff2"),
                                   ("/demo/assets/Pretendard-ExtraBold.woff2", "font/woff2"),
                                   ("/demo/assets/Pretendard-OFL.txt", "text/plain")):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn(content_type, response.headers["content-type"])
                self.assertEqual(response.headers["cache-control"], "no-store")

    def test_local_demo_keeps_api_mode_and_separate_official_catalogue(self):
        self.assertIn('data-runtime="api"', self.client.get("/demo").text)
        catalogue = self.client.get("/demo/assets/official-policies.json").json()
        self.assertEqual(len(catalogue["policies"]), 6)
        self.assertTrue(all(p["reference_id"].startswith("REF-") for p in catalogue["policies"]))

    def test_demo_assets_do_not_expose_source_or_database(self):
        for path in ("/demo/assets/../api.py", "/demo/assets/%2e%2e/api.py", "/demo/assets/policies.sqlite3",
                     "/demo/assets/index.html", "/demo/assets/unlisted.mjs"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)

    def test_demo_modules_ignore_plain_text_os_mime_mapping(self):
        mimetypes.init()
        with patch.dict(mimetypes.types_map, {".mjs": "text/plain"}):
            self.assertEqual(mimetypes.guess_type("app.mjs")[0], "text/plain")
            for filename in ("app.mjs", "client.mjs", "mock.mjs"):
                with self.subTest(filename=filename):
                    response = self.client.get("/demo/assets/" + filename)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.headers["content-type"].split(";")[0], "text/javascript")
                    self.assertEqual(response.headers["cache-control"], "no-store")

    def test_full_flow_uses_response_state(self):
        response = self.client.post("/api/v1/intake/start", json={})
        self.assertEqual(response.status_code, 200)
        state = response.json()["state"]
        actions = (
            {"type": "choose_card", "key": "situation", "value": "resting"},
            {"type": "choose_card", "key": "interest", "value": "living_cost"},
            {"type": "answer_fact", "key": "age", "value": 24},
            {"type": "answer_fact", "key": "region_code", "value": "11680"},
            {"type": "show_results"}, {"type": "select_policy", "policy_id": "TEST-ONLY"},
            {"type": "choose_detail", "accept": True}, {"type": "pause_detail"},
            {"type": "resume_detail"}, {"type": "answer_fact", "key": "employment_status", "value": "미취업자"},
            {"type": "show_results"}, {"type": "prepare"},
        )
        for action in actions:
            response = self.transition(state, action)
            self.assertEqual(response.status_code, 200, response.text)
            state = response.json()["state"]
        self.assertEqual(state["stage"], "preparation")

    def test_bool_age_rejected_and_input_not_echoed(self):
        response = self.transition(state_to_payload(basic_state()),
                                   {"type": "answer_fact", "key": "age", "value": True})
        self.assertEqual(response.status_code, 422)
        response = self.client.post("/api/v1/intake/start", json={"ssn": "TEST-SENSITIVE"})
        self.assertEqual(response.status_code, 422)
        self.assertNotIn("TEST-SENSITIVE", response.text)

    def test_inconsistent_state_rejected(self):
        state = state_to_payload(basic_state())
        state["stage"] = "detail"
        response = self.transition(state, {"type": "pause_detail"})
        self.assertEqual(response.status_code, 422)

    def test_unlisted_policy_selection_is_conflict(self):
        state = self.transition(state_to_payload(basic_state()), {"type": "show_results"}).json()["state"]
        response = self.transition(state, {"type": "select_policy", "policy_id": "outside"})
        self.assertEqual(response.status_code, 409)

    def test_client_cannot_provide_candidate_ids_or_date(self):
        response = self.transition(state_to_payload(basic_state()), {"type": "show_results", "reference_date": "2000-01-01"})
        self.assertEqual(response.status_code, 422)

    def test_missing_data_keeps_start_available(self):
        def unavailable():
            raise PolicyDataUnavailable("internal-private-path")
        client = TestClient(create_app(settings=self.settings, policy_provider=unavailable))
        self.addCleanup(client.close)
        self.assertEqual(client.post("/api/v1/intake/start", json={}).status_code, 200)
        response = client.get("/ready")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("internal-private-path", response.text)

    def test_no_global_user_state(self):
        first = self.client.post("/api/v1/intake/start", json={}).json()["state"]
        self.transition(first, {"type": "choose_card", "key": "situation", "value": "working"})
        second = self.client.post("/api/v1/intake/start", json={}).json()["state"]
        self.assertEqual(first, second)
        self.assertIsNone(second["profile"]["employment_status"])

    def test_empty_data_is_explicit(self):
        client = TestClient(create_app(settings=self.settings, policy_provider=lambda: ()))
        self.addCleanup(client.close)
        self.assertEqual(client.get("/ready").status_code, 503)
        response = client.post("/api/v1/intake/transition", json={"state": state_to_payload(basic_state()), "action": {"type": "show_results"}})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data_status"], "empty")

    def test_allowed_origin_and_blocked_preflight(self):
        allowed = self.client.options("/api/v1/intake/start", headers={
            "Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"})
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.headers["access-control-allow-origin"], "http://localhost:5173")
        blocked = self.client.options("/api/v1/intake/start", headers={
            "Origin": "https://other.example", "Access-Control-Request-Method": "POST"})
        self.assertEqual(blocked.status_code, 400)
        self.assertNotIn("access-control-allow-origin", blocked.headers)

    def test_openapi_documents_discriminated_actions(self):
        schema = self.client.get("/openapi.json").json()
        self.assertIn("/api/v1/intake/transition", schema["paths"])
        self.assertIn("StateSchema", schema["components"]["schemas"])


if __name__ == "__main__":
    unittest.main()
