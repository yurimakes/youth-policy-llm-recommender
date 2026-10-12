"""Exercise adaptive question order and retained uncertainty with synthetic data."""

from dataclasses import replace
from datetime import date
import unittest

from test_intake import basic_state, detail_state, policy
from youth_policy.conditions import ConditionStatus
from youth_policy.intake import answer_fact, choose_card
from youth_policy.intake_contract import response_payload
from youth_policy.intake_service import build_guidance, next_question


TODAY = date(2026, 10, 7)


def example_policies() -> tuple:
    """Isolated examples; no record describes an actual public programme."""
    return (
        policy(policy_id="TEST-REGION-A", region_code="11680", employment_status="제한없음"),
        policy(policy_id="TEST-REGION-B", region_code="11110", employment_status="제한없음"),
        policy(policy_id="TEST-UNCERTAIN", age_min=None, age_max=None, region_code=None,
               employment_status="제한없음", policy_name="추가 확인이 필요한 테스트 지원"),
    )


class AdaptiveQuestionTests(unittest.TestCase):
    def test_diverse_region_conditions_are_asked_before_shared_age_range(self):
        question = next_question(basic_state(), example_policies(), reference_date=TODAY)
        self.assertEqual(question.key, "region_code")
        self.assertIn("현재 후보 3개 중 2개", question.purpose)

    def test_diverse_age_ranges_are_asked_before_shared_region(self):
        records = (policy(policy_id="A", age_min=19, age_max=24),
                   policy(policy_id="B", age_min=25, age_max=34))
        self.assertEqual(next_question(basic_state(), records, reference_date=TODAY).key, "age")

    def test_region_order_and_duplicates_do_not_inflate_condition_groups(self):
        records = (policy(policy_id="A", region_code="11680,11110"),
                   policy(policy_id="B", region_code="11110,11680,11680"))
        for ordered in (records, tuple(reversed(records))):
            self.assertEqual(next_question(basic_state(), ordered, reference_date=TODAY).key, "age")

    def test_excluded_records_do_not_affect_question_priority(self):
        records = (policy(), *(replace(p, application_end=date(2026, 10, 6)) for p in example_policies()))
        self.assertEqual(next_question(basic_state(), records, reference_date=TODAY).key, "age")

    def test_skip_keeps_unknown_without_repeating_the_question(self):
        state = answer_fact(basic_state(), "region_code", None)
        self.assertEqual(next_question(state, example_policies(), reference_date=TODAY).key, "age")
        self.assertIsNone(state.profile.region_code)
        state = answer_fact(state, "age", None)
        self.assertIsNone(next_question(state, example_policies(), reference_date=TODAY))

    def test_remaining_uncertain_policy_does_not_trigger_uncomparable_questions(self):
        state = answer_fact(basic_state(), "region_code", "26110")
        self.assertIsNone(next_question(state, example_policies(), reference_date=TODAY))
        candidates = build_guidance(example_policies(), state, reference_date=TODAY)
        self.assertEqual([p.policy_id for p in candidates], ["TEST-UNCERTAIN"])
        self.assertEqual(candidates[0].assessment.status, ConditionStatus.CHECK_REQUIRED)
        self.assertIsNone(state.profile.age)

    def test_corrected_answer_recomputes_needed_questions(self):
        state = answer_fact(basic_state(), "region_code", "26110")
        state = answer_fact(state, "region_code", "11680")
        self.assertEqual(next_question(state, example_policies(), reference_date=TODAY).key, "age")

    def test_optional_detail_only_uses_selected_policy(self):
        selected = policy(age_min=None, age_max=None, region_code=None)
        question = next_question(detail_state(), (selected, *example_policies()), reference_date=TODAY)
        self.assertEqual(question.key, "employment_status")
        self.assertIn("선택한 지원", question.purpose)
        self.assertIsNone(detail_state().profile.employment_status)

    def test_unknown_cards_do_not_change_question_priority_or_facts(self):
        state = choose_card(basic_state(), "interest", "unknown")
        self.assertEqual(next_question(state, example_policies(), reference_date=TODAY).key, "region_code")
        self.assertIsNone(state.profile.employment_status)

    def test_single_case_needs_one_question_instead_of_two_with_same_final_checks(self):
        records = example_policies()
        answers = {"age": 24, "region_code": "26110"}
        adaptive, fixed = basic_state(), basic_state()
        adaptive_keys, fixed_keys = [], []
        while (question := next_question(adaptive, records, reference_date=TODAY)) is not None:
            adaptive_keys.append(question.key)
            adaptive = answer_fact(adaptive, question.key, answers[question.key])
        for key in ("age", "region_code"):
            candidates = build_guidance(records, fixed, reference_date=TODAY)
            if any(c.field == key and c.status is ConditionStatus.INPUT_MISSING
                   for p in candidates for c in p.assessment.checks):
                fixed_keys.append(key)
                fixed = answer_fact(fixed, key, answers[key])
        self.assertEqual(adaptive_keys, ["region_code"])
        self.assertEqual(fixed_keys, ["age", "region_code"])
        self.assertEqual({p.policy_id: p.assessment for p in build_guidance(records, adaptive, reference_date=TODAY)},
                         {p.policy_id: p.assessment for p in build_guidance(records, fixed, reference_date=TODAY)})

    def test_api_contract_preserves_dynamic_purpose(self):
        response = response_payload(basic_state(), example_policies(), reference_date=TODAY)
        self.assertEqual(response["next_question"]["key"], "region_code")
        self.assertIn("지역 조건", response["next_question"]["purpose"])


if __name__ == "__main__":
    unittest.main()
