"""Validate evidence selection, privacy boundaries and fail-safe source quotes."""

from dataclasses import replace
from datetime import date
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from test_intake import basic_state, policy
from youth_policy.evidence_explanation import (
    MAX_EXCERPT, OpenAIEvidenceSelector, load_evidence_selector, recorded_evidence,
    safe_evidence_url, select_evidence,
)
from youth_policy.intake import answer_fact


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.policy = policy(summary="기록된 지원 요약", benefit_text="지원 내용 원문",
                             required_documents="공고의 서류 원문", application_method="공고 접수 방법")
        self.checks = [{"field": "income", "status": "check_required", "reason": "기관 확인"}]

    def select(self, **kwargs):
        values = dict(focus="overview", use_ai=False, selector=None)
        values.update(kwargs)
        return select_evidence(self.policy, basic_state(), self.checks, **values)

    def test_recorded_fields_are_quoted_and_missing_fields_not_added(self):
        evidence = recorded_evidence(policy(application_start=None, application_end=None))
        self.assertEqual(evidence, ())
        self.assertEqual(self.select()["items"][0]["excerpt"], "기록된 지원 요약")

    def test_excerpt_limit_is_explicit(self):
        evidence = recorded_evidence(replace(self.policy, summary="가" * (MAX_EXCERPT + 1)))
        summary = next(item for item in evidence if item.field == "summary")
        self.assertEqual(len(summary.excerpt), MAX_EXCERPT)
        self.assertTrue(summary.truncated)

    def test_partial_period_does_not_invent_a_date(self):
        evidence = recorded_evidence(replace(self.policy, application_end=None))
        self.assertIn("종료일 미확인", next(item.excerpt for item in evidence if item.field == "application_period"))

    def test_ai_needs_explicit_use_request(self):
        selector = Mock(side_effect=AssertionError("must not call"))
        self.assertTrue(self.select(selector=selector)["ai_available"])
        selector.assert_not_called()

    def test_default_disabled_and_incomplete_configuration(self):
        self.assertIsNone(load_evidence_selector({}))
        self.assertIsNone(load_evidence_selector({"OPENAI_API_KEY": "TEST", "POLICY_EXPLANATION_MODEL": "TEST"}))
        self.assertIsNone(load_evidence_selector({"POLICY_EXPLANATION_AI_ENABLED": "1"}))

    def test_configured_adapter_has_transport_budget(self):
        with patch("openai.OpenAI") as factory:
            selector = load_evidence_selector({"POLICY_EXPLANATION_AI_ENABLED": "1", "OPENAI_API_KEY": "TEST", "POLICY_EXPLANATION_MODEL": "TEST"})
            self.assertIsInstance(selector, OpenAIEvidenceSelector)
            factory.assert_called_once_with(api_key="TEST", timeout=5.0, max_retries=0)

    def test_valid_ids_select_original_server_excerpts(self):
        selector = Mock(return_value={"evidence_ids": ["TEST-ONLY:required_documents"]})
        result = self.select(use_ai=True, selector=selector)
        self.assertEqual(result["mode"], "ai_selected")
        self.assertEqual([item["excerpt"] for item in result["items"]], ["공고의 서류 원문"])
        self.assertIsNone(result["fallback_reason"])
        self.assertEqual(self.checks[0]["status"], "check_required")

    def test_invalid_ids_extra_advice_and_duplicates_fall_back(self):
        for output in ({"evidence_ids": ["OTHER:summary"]}, {"evidence_ids": []},
                       {"evidence_ids": ["TEST-ONLY:summary"] * 2},
                       {"evidence_ids": [None]}, {"evidence_ids": ["TEST-ONLY:summary"], "advice": "자격 확정"},
                       {"evidence_ids": ["TEST-ONLY:summary", "TEST-ONLY:benefit_text", "TEST-ONLY:required_documents", "TEST-ONLY:application_method"]},
                       "raw advice"):
            with self.subTest(output=output):
                result = self.select(use_ai=True, selector=lambda _: output)
                self.assertEqual(result["mode"], "source_only")
                self.assertEqual(result["fallback_reason"], "invalid_selection")
                self.assertNotIn("자격 확정", str(result))

    def test_provider_errors_keep_source_data_without_error_details(self):
        for error in (TimeoutError("TEST-SENSITIVE"), RuntimeError("TEST-SENSITIVE")):
            result = self.select(use_ai=True, selector=Mock(side_effect=error))
            self.assertEqual(result["mode"], "source_only")
            self.assertEqual(result["fallback_reason"], "provider_error")
            self.assertNotIn("TEST-SENSITIVE", str(result))

    def test_profile_and_situation_never_enter_model_context(self):
        state = answer_fact(answer_fact(basic_state(), "age", 24), "region_code", "11680")
        captured = []
        def select(context):
            captured.append(context)
            return {"evidence_ids": ["TEST-ONLY:summary"]}
        select_evidence(self.policy, state, self.checks, focus="overview", use_ai=True, selector=select)
        context = captured[0]
        self.assertNotIn("profile", context)
        self.assertNotIn("situation", context)
        self.assertNotIn("11680", str(context))
        self.assertEqual(context["condition_statuses"], [{"field": "income", "status": "check_required"}])
        self.assertEqual(state.profile.age, 24)

    def test_context_mutation_cannot_rewrite_server_quotes(self):
        def select(context):
            context["evidence"][0]["excerpt"] = "자격 확정"
            return {"evidence_ids": ["TEST-ONLY:summary"]}
        result = self.select(use_ai=True, selector=select)
        self.assertEqual(result["items"][0]["excerpt"], "기록된 지원 요약")

    def test_no_usable_url_prevents_external_call(self):
        selector = Mock()
        for value in (None, "javascript:alert(1)", "https://user:pass@example.test", "https://example.test:bad"):
            with self.subTest(url=value):
                result = select_evidence(replace(self.policy, source_url=value), basic_state(), self.checks,
                                         focus="overview", use_ai=True, selector=selector)
                self.assertEqual(result["mode"], "source_only")
                self.assertFalse(result["ai_available"])
                self.assertIsNone(safe_evidence_url(value))
        selector.assert_not_called()

    def test_adapter_requests_ids_only_and_single_bounded_call(self):
        create = Mock(return_value=SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{"evidence_ids":["TEST-ONLY:summary"]}'))]))
        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        selector = OpenAIEvidenceSelector(client, "TEST-MODEL")
        result = self.select(use_ai=True, selector=selector)
        self.assertEqual(result["mode"], "ai_selected")
        create.assert_called_once()
        self.assertEqual(create.call_args.kwargs["max_completion_tokens"], 256)
        self.assertTrue(create.call_args.kwargs["response_format"]["json_schema"]["strict"])


if __name__ == "__main__":
    unittest.main()
