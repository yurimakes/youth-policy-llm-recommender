"""test_intake_schema.py

실제 Pydantic으로 HTTP 입력·응답 스키마와 강제 형변환 방지를 검증합니다.
"""

from datetime import date
from importlib.util import find_spec
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from test_intake import policy, basic_state
from youth_policy.intake import start_intake
from youth_policy.intake_contract import response_payload, state_to_payload


HAS_PYDANTIC = find_spec("pydantic") is not None
if HAS_PYDANTIC:
    from pydantic import ValidationError
    from youth_policy.api_schemas import IntakeResponse, StartRequest, TransitionRequest


@unittest.skipUnless(HAS_PYDANTIC, "Pydantic 설치 필요: requirements-api.txt")
class SchemaTests(unittest.TestCase):
    def test_start_default_and_forbidden_extra(self):
        self.assertEqual(StartRequest.model_validate({}).start_mode, "situation")
        with self.assertRaises(ValidationError):
            StartRequest.model_validate({"user_name": "TEST-SENSITIVE"})

    def test_actual_envelope_matches_response_schema(self):
        for state in (start_intake(), basic_state()):
            response = response_payload(state, (policy(),), reference_date=date(2026, 10, 7))
            validated = IntakeResponse.model_validate(response)
            self.assertEqual(validated.state.stage, state.stage)

    def test_no_boolean_or_float_coercion_to_age(self):
        for value in (True, 24.5):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                TransitionRequest.model_validate({"state": state_to_payload(basic_state()),
                                                   "action": {"type": "answer_fact", "key": "age", "value": value}})

    def test_string_true_is_not_detail_choice(self):
        with self.assertRaises(ValidationError):
            TransitionRequest.model_validate({"state": state_to_payload(basic_state()),
                                               "action": {"type": "choose_detail", "accept": "true"}})

    def test_unknown_action_and_extra_fields_rejected(self):
        for action in ({"type": "apply_automatically"}, {"type": "show_results", "reference_date": "2026-01-01"}):
            with self.subTest(action=action), self.assertRaises(ValidationError):
                TransitionRequest.model_validate({"state": state_to_payload(basic_state()), "action": action})

    def test_state_profile_range_and_region_format(self):
        for field, value in (("age", 121), ("age", "24"), ("region_code", "서울")):
            state = state_to_payload(basic_state())
            state["profile"][field] = value
            with self.subTest(field=field), self.assertRaises(ValidationError):
                TransitionRequest.model_validate({"state": state, "action": {"type": "show_results"}})


if __name__ == "__main__":
    unittest.main()
