"""test_intake_contract.py

JSON 상태 계약·전환·서버 재평가와 정책 읽기 경계를 검증합니다.
"""

from copy import deepcopy
from dataclasses import replace
from datetime import date
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from test_intake import policy, basic_state, detail_state
from youth_policy.api_config import load_api_settings, korea_today
from youth_policy.intake import Stage, answer_fact, pause_detail, show_results, start_intake
from youth_policy.intake_contract import (
    PayloadError, TransitionConflict, apply_action, response_payload, state_from_payload,
    state_to_payload,
)
from youth_policy.policy_repository import PolicyDataUnavailable, load_policies_readonly
from youth_policy.sqlite_store import connect_database, initialize_database, upsert_policies


TODAY = date(2026, 10, 7)


class ContractTests(unittest.TestCase):
    def apply(self, state, action, records=None):
        return apply_action(state_from_payload(state_to_payload(state)), action,
                            (policy(),) if records is None else records, reference_date=TODAY)

    def test_start_and_basic_roundtrip(self):
        for state in (start_intake(), start_intake("goal"), basic_state(), detail_state(), pause_detail(detail_state())):
            with self.subTest(stage=state.stage):
                self.assertEqual(state_from_payload(state_to_payload(state)), state)

    def test_start_question_does_not_assume_profile(self):
        response = response_payload(start_intake(), (), reference_date=TODAY, data_status="not_loaded")
        self.assertEqual(response["next_question"]["key"], "situation")
        self.assertIsNone(response["state"]["profile"]["age"])
        self.assertEqual(response["candidates"], [])

    def test_goal_start_question(self):
        response = response_payload(start_intake("goal"), (), reference_date=TODAY)
        self.assertEqual(response["next_question"]["key"], "goal")

    def test_action_and_question_sequence(self):
        state = self.apply(start_intake(), {"type": "choose_card", "key": "situation", "value": "resting"})
        self.assertEqual(response_payload(state, (), reference_date=TODAY)["next_question"]["key"], "interest")
        state = self.apply(state, {"type": "choose_card", "key": "interest", "value": "living_cost"})
        self.assertEqual(response_payload(state, (policy(),), reference_date=TODAY)["next_question"]["key"], "age")

    def test_every_response_state_can_be_sent_back(self):
        state = basic_state()
        for action in (
            {"type": "answer_fact", "key": "age", "value": 24},
            {"type": "answer_fact", "key": "region_code", "value": "11680"},
            {"type": "show_results"}, {"type": "select_policy", "policy_id": "TEST-ONLY"},
            {"type": "choose_detail", "accept": True},
            {"type": "answer_preference", "key": "participation_format", "value": "online"},
            {"type": "pause_detail"}, {"type": "resume_detail"},
            {"type": "answer_fact", "key": "employment_status", "value": "미취업자"},
            {"type": "show_results"}, {"type": "prepare"},
        ):
            state = self.apply(state, action)
            envelope = response_payload(state, (policy(),), reference_date=TODAY)
            self.assertEqual(state_from_payload(envelope["state"]), state)

    def test_response_does_not_offer_detail_without_interest(self):
        response = response_payload(show_results(basic_state()), (policy(),), reference_date=TODAY)
        self.assertFalse(response["detail_offer_available"])

    def test_detail_offer_requires_missing_facts_and_user_choice(self):
        state = self.apply(show_results(basic_state()), {"type": "select_policy", "policy_id": "TEST-ONLY"})
        self.assertTrue(response_payload(state, (policy(),), reference_date=TODAY)["detail_offer_available"])
        state = self.apply(state, {"type": "choose_detail", "accept": False})
        self.assertEqual(state.stage, Stage.RESULTS)
        self.assertFalse(response_payload(state, (policy(),), reference_date=TODAY)["detail_offer_available"])

    def test_policy_selection_cannot_use_client_candidate_list(self):
        with self.assertRaises(PayloadError):
            self.apply(show_results(basic_state()), {"type": "select_policy", "policy_id": "outside", "candidate_ids": ["outside"]})
        with self.assertRaises(TransitionConflict):
            self.apply(show_results(basic_state()), {"type": "select_policy", "policy_id": "outside"})

    def test_clear_exclusion_recomputed_after_answer_change(self):
        state = self.apply(detail_state(), {"type": "answer_fact", "key": "age", "value": 35})
        response = response_payload(state, (policy(),), reference_date=TODAY)
        self.assertEqual(response["candidates"], [])
        self.assertTrue(response["selected_policy_excluded"])

    def test_cannot_resume_excluded_policy(self):
        state = pause_detail(answer_fact(detail_state(), "age", 35))
        with self.assertRaises(TransitionConflict):
            self.apply(state, {"type": "resume_detail"})

    def test_card_correction_resets_stale_detail_selection(self):
        state = self.apply(pause_detail(detail_state()), {"type": "choose_card", "key": "interest", "value": "counseling"})
        self.assertIsNone(state.interested_policy_id)
        self.assertFalse(state.detail_paused)
        self.assertEqual(state_from_payload(state_to_payload(state)), state)

    def test_unsupported_or_extra_state_fields(self):
        for key, value in (("candidates", []), ("ssn", "TEST-SENSITIVE"), ("qualification", True)):
            payload = state_to_payload(start_intake())
            payload[key] = value
            with self.subTest(key=key), self.assertRaises(PayloadError):
                state_from_payload(payload)

    def test_invalid_history_and_profile(self):
        changes = [
            {"answered": ["situation", "situation"]}, {"skipped": ["situation"]},
            {"profile": {"age": True, "region_code": None, "employment_status": None}},
            {"profile": {"age": 24, "region_code": None, "employment_status": None}},
            {"cards": {"situation": "not-a-card"}}, {"preferences": {"income": "low"}},
            {"revision": True}, {"revision": -1}, {"detail_choice": "true"},
            {"detail_paused": True}, {"start_mode": []},
        ]
        for change in changes:
            payload = state_to_payload(basic_state())
            payload.update(change)
            with self.subTest(change=change), self.assertRaises(PayloadError):
                state_from_payload(payload)

    def test_forged_detail_state_without_choice_rejected(self):
        payload = state_to_payload(basic_state())
        payload["stage"] = "detail"
        with self.assertRaises(PayloadError):
            state_from_payload(payload)

    def test_opening_state_cannot_contain_later_answers(self):
        payload = state_to_payload(basic_state())
        payload["stage"] = "start"
        with self.assertRaises(PayloadError):
            state_from_payload(payload)

    def test_unknown_can_be_corrected_and_roundtripped(self):
        state = self.apply(basic_state(), {"type": "answer_fact", "key": "age", "value": None})
        state = self.apply(state, {"type": "answer_fact", "key": "age", "value": 24})
        self.assertNotIn("age", state.skipped)
        self.assertEqual(state_from_payload(state_to_payload(state)), state)

    def test_action_cannot_override_server_date(self):
        with self.assertRaises(PayloadError):
            self.apply(basic_state(), {"type": "show_results", "reference_date": "2026-01-01"})

    def test_action_fact_boolean_rejected(self):
        with self.assertRaises(PayloadError):
            self.apply(basic_state(), {"type": "answer_fact", "key": "age", "value": True})

    def test_actions_do_not_modify_input_payload(self):
        payload = state_to_payload(basic_state())
        before = deepcopy(payload)
        state = state_from_payload(payload)
        self.apply(state, {"type": "answer_fact", "key": "age", "value": 24})
        self.assertEqual(payload, before)

    def test_response_keeps_official_source_fields(self):
        result = response_payload(basic_state(), (policy(),), reference_date=TODAY)["candidates"][0]
        self.assertEqual(result["source_name"], "TEST ONLY")
        self.assertEqual(result["source_url"], "https://example.test/official")
        self.assertEqual(result["status"], "check_required")
        self.assertTrue(any(c["status"] == "input_missing" for c in result["checks"]))


class RepositoryAndSettingsTests(unittest.TestCase):
    def test_readonly_repository_roundtrip_does_not_write(self):
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / "policies.sqlite3"
            connection = connect_database(database)
            initialize_database(connection)
            upsert_policies(connection, (policy(),))
            connection.close()
            before = database.read_bytes()
            self.assertEqual(load_policies_readonly(database)[0], policy())
            self.assertEqual(database.read_bytes(), before)

    def test_repository_missing_or_bad_data_has_domain_error(self):
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / "missing.sqlite3"
            with self.assertRaises(PolicyDataUnavailable):
                load_policies_readonly(database)
            self.assertFalse(database.exists())
            database.write_bytes(b"not a sqlite database")
            with self.assertRaises(PolicyDataUnavailable):
                load_policies_readonly(database)

    def test_empty_repository_is_distinguished_from_missing(self):
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / "empty.sqlite3"
            connection = connect_database(database)
            initialize_database(connection)
            connection.close()
            self.assertEqual(load_policies_readonly(database), ())

    def test_settings_path_does_not_depend_on_working_directory(self):
        root = Path("temporary-project")
        settings = load_api_settings(environ={}, project_root=root)
        self.assertEqual(settings.policy_db_path, root / "data/processed/policies.sqlite3")
        self.assertEqual(settings.cors_origins, ("http://localhost:5173", "http://localhost:3000"))

    def test_custom_origins_and_no_wildcards(self):
        for origin in ("*", "http://*", "http://localhost:invalid", "http://localhost:99999",
                       "https://demo.example/path", "file:///demo", "https://u:p@demo.example", "https://demo.example?x=1"):
            with self.subTest(origin=origin), self.assertRaises(ValueError):
                load_api_settings(environ={"API_CORS_ORIGINS": origin})
        settings = load_api_settings(environ={"API_CORS_ORIGINS": "http://localhost:8080"})
        self.assertEqual(settings.cors_origins, ("http://localhost:8080",))
        self.assertEqual(load_api_settings(environ={"API_CORS_ORIGINS": ""}).cors_origins, ())

    def test_korea_date_has_date_type(self):
        self.assertIs(type(korea_today()), date)


if __name__ == "__main__":
    unittest.main()
