"""Preserve recorded preparation fields and missing data in the API contract."""

from datetime import date
import unittest

from test_intake import basic_state, policy
from youth_policy.api_schemas import IntakeResponse
from youth_policy.intake_contract import response_payload


class PreparationContractTests(unittest.TestCase):
    def test_recorded_fields_survive_response_validation(self):
        record = policy(required_documents="원문 서류 안내", application_method="원문 신청 안내", contact="원문 문의처")
        payload = response_payload(basic_state(), (record,), reference_date=date(2026, 10, 7))
        candidate = IntakeResponse.model_validate(payload).candidates[0]
        self.assertEqual(candidate.application_start, record.application_start)
        self.assertEqual(candidate.application_end, record.application_end)
        self.assertEqual(candidate.required_documents, record.required_documents)
        self.assertEqual(candidate.application_method, record.application_method)
        self.assertEqual(candidate.contact, record.contact)

    def test_missing_fields_are_not_invented(self):
        record = policy(application_start=None, application_end=None)
        payload = response_payload(basic_state(), (record,), reference_date=date(2026, 10, 7))
        for field in ("application_start", "application_end", "required_documents", "application_method", "contact"):
            self.assertIsNone(payload["candidates"][0][field])


if __name__ == "__main__":
    unittest.main()
