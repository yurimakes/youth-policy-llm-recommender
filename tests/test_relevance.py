"""Validate interest ranking independently from eligibility and user facts."""

from dataclasses import replace
from datetime import date
import unittest

from test_intake import basic_state, policy
from youth_policy.intake import answer_fact, choose_card, start_intake
from youth_policy.intake_contract import response_payload
from youth_policy.intake_service import build_guidance
from youth_policy.relevance import assess_relevance


TODAY = date(2026, 10, 7)


class RelevanceTests(unittest.TestCase):
    def setUp(self):
        self.housing = policy(policy_id="HOUSE", policy_name="월세 지원", category="주거")
        self.job = policy(policy_id="JOB", policy_name="구직 프로그램", category="일자리")

    def test_changed_goal_reorders_same_eligible_candidates(self):
        records = (self.job, self.housing)
        housing = choose_card(start_intake("goal"), "goal", "housing")
        employment = choose_card(housing, "goal", "employment")
        first = build_guidance(records, housing, reference_date=TODAY)
        second = build_guidance(records, employment, reference_date=TODAY)
        self.assertEqual([p.policy_id for p in first], ["HOUSE", "JOB"])
        self.assertEqual([p.policy_id for p in second], ["JOB", "HOUSE"])
        self.assertEqual({p.policy_id: p.assessment for p in first},
                         {p.policy_id: p.assessment for p in second})
        self.assertEqual(housing.profile, employment.profile)

    def test_matching_interest_cannot_restore_age_region_or_expired_exclusion(self):
        state = answer_fact(answer_fact(basic_state(), "age", 24), "region_code", "11680")
        records = (
            replace(self.housing, policy_id="AGE", age_max=23),
            replace(self.housing, policy_id="REGION", region_code="26110"),
            replace(self.housing, policy_id="CLOSED", application_end=date(2026, 10, 6)),
            self.job,
        )
        self.assertEqual([p.policy_id for p in build_guidance(records, state, reference_date=TODAY)], ["JOB"])

    def test_unknown_and_skip_preserve_order_without_fact_inference(self):
        records = (self.job, self.housing)
        for value in ("unknown", None):
            state = choose_card(choose_card(start_intake(), "situation", "resting"), "interest", value)
            self.assertEqual([p.policy_id for p in build_guidance(records, state, reference_date=TODAY)], ["JOB", "HOUSE"])
            self.assertIsNone(state.profile.employment_status)
            self.assertEqual(assess_relevance(self.housing, state).score, 0)

    def test_policy_requirements_are_not_relevance_evidence(self):
        state = choose_card(start_intake("goal"), "goal", "employment")
        record = policy(policy_name="청년 지원", category=None, summary=None,
                        eligibility_text="취업 및 구직", benefit_text="일자리")
        result = assess_relevance(record, state)
        self.assertEqual(result.score, 0)
        self.assertNotIn("취업 및 구직", " ".join(result.reasons))

    def test_low_burden_keywords_do_not_promise_ease(self):
        state = choose_card(basic_state(), "interest", "low_burden")
        result = assess_relevance(policy(category="문화", policy_name="청년 활동"), state)
        self.assertGreater(result.score, 0)
        self.assertTrue(any("별도로 확인" in reason for reason in result.reasons))

    def test_response_exposes_recorded_evidence_and_does_not_mutate_state(self):
        state = basic_state()
        payload = response_payload(state, (self.job, self.housing), reference_date=TODAY)
        reasons = payload["candidates"][0]["recommendation_reasons"]
        self.assertTrue(any("월세" in reason and "정책명" in reason for reason in reasons))
        self.assertEqual(state.profile.age, None)
        self.assertEqual(payload["candidates"][0]["policy_id"], "HOUSE")


if __name__ == "__main__":
    unittest.main()
