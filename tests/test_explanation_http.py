"""Check explicit explanation requests against current candidate eligibility."""

from datetime import date
from pathlib import Path
import unittest
from unittest.mock import Mock

from fastapi.testclient import TestClient
from test_intake import basic_state, policy
from youth_policy.api_app import create_app
from youth_policy.api_config import ApiSettings
from youth_policy.intake import answer_fact, show_results
from youth_policy.intake_contract import state_to_payload


class ExplanationHttpTests(unittest.TestCase):
    def setUp(self):
        self.selector = Mock(return_value={"evidence_ids": ["TEST-ONLY:summary"]})
        self.policy = policy(summary="공고 요약 기록", required_documents="서류 기록")
        self.client = TestClient(create_app(settings=ApiSettings(Path("unused.sqlite3")),
            policy_provider=lambda: (self.policy,), date_provider=lambda: date(2026, 10, 7), evidence_selector=self.selector))
        self.addCleanup(self.client.close)
        self.state = show_results(basic_state())

    def request(self, **changes):
        payload = {"state": state_to_payload(self.state), "policy_id": "TEST-ONLY"}
        payload.update(changes)
        return self.client.post("/api/v1/intake/explanation", json=payload)

    def test_source_default_and_explicit_ai_keep_identical_checks(self):
        source = self.request()
        self.assertEqual(source.status_code, 200)
        self.selector.assert_not_called()
        ai = self.request(use_ai=True)
        self.assertEqual(ai.status_code, 200)
        self.assertEqual(ai.json()["mode"], "ai_selected")
        self.assertEqual(source.json()["checks"], ai.json()["checks"])
        self.assertEqual(source.headers["cache-control"], "no-store")

    def test_known_mismatch_never_calls_provider(self):
        state = answer_fact(self.state, "age", 35)
        response = self.request(state=state_to_payload(state), use_ai=True)
        self.assertEqual(response.status_code, 409)
        self.selector.assert_not_called()

    def test_stage_and_unknown_policy_are_rejected(self):
        self.assertEqual(self.request(state=state_to_payload(basic_state())).status_code, 409)
        self.assertEqual(self.request(policy_id="UNKNOWN").status_code, 409)
        self.selector.assert_not_called()

    def test_invalid_payload_is_not_coerced_or_echoed(self):
        for changes in ({"use_ai": "true"}, {"focus": "TEST-SENSITIVE"}, {"source_text": "TEST-SENSITIVE"}):
            response = self.request(**changes)
            self.assertEqual(response.status_code, 422)
            self.assertNotIn("TEST-SENSITIVE", response.text)
        self.selector.assert_not_called()

    def test_provider_failure_stays_successful_with_uncertainty(self):
        self.selector.side_effect = TimeoutError("TEST-SENSITIVE")
        response = self.request(use_ai=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["mode"], "source_only")
        self.assertEqual(response.json()["fallback_reason"], "provider_error")
        self.assertTrue(any(c["status"] == "check_required" for c in response.json()["checks"]))
        self.assertNotIn("TEST-SENSITIVE", response.text)


if __name__ == "__main__":
    unittest.main()
