"""test_intake.py

간편 진입·선택적 상세 흐름과 조건 원인 분리를 외부 호출 없이 검증합니다.
"""

from dataclasses import replace
from datetime import date, datetime
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from youth_policy.conditions import ConditionStatus, assess_conditions
from youth_policy.intake import (
    Stage, answer_fact, answer_preference, choose_card, choose_detail, pause_detail,
    prepare, resume_detail, select_policy, show_results, start_intake,
)
from youth_policy.intake_service import build_guidance, detail_is_useful, next_question
from youth_policy.matching import MatchStatus, UserProfile
from youth_policy.models import ApplicationStatus, PolicyRecord


TODAY = date(2026, 10, 7)


def policy(**overrides: object) -> PolicyRecord:
    """실제 공고가 아닌 격리된 단위 테스트용 데이터입니다."""
    values = dict(
        policy_id="TEST-ONLY", policy_name="단위 테스트 전용 정책", category="주거",
        summary=None, region_code="11680", region_name=None, age_min=19, age_max=34,
        income_condition="무관", employment_status="미취업자", education_status="제한없음",
        application_start=date(2026, 10, 1), application_end=date(2026, 10, 31),
        application_status=ApplicationStatus.OPEN, eligibility_text=None, benefit_text=None,
        application_method=None, required_documents=None, contact=None, source_name="TEST ONLY",
        source_url="https://example.test/official", last_verified_at=datetime(2026, 10, 1),
        embedding_text="",
    )
    values.update(overrides)
    return PolicyRecord(**values)


def basic_state():
    return choose_card(choose_card(start_intake(), "situation", "resting"), "interest", "living_cost")


def detail_state():
    state = show_results(basic_state())
    state = select_policy(state, "TEST-ONLY", ("TEST-ONLY",))
    return choose_detail(state, True, needs_information=True)


def check(field: str, record=None, profile=None):
    result = assess_conditions(record or policy(), profile or UserProfile(), reference_date=TODAY)
    return next(c for c in result.checks if c.field == field)


class IntakeTests(unittest.TestCase):
    def test_resting_does_not_infer_profile(self):
        state = basic_state()
        self.assertEqual(state.profile, UserProfile())
        self.assertEqual(state.stage, Stage.BASIC)

    def test_working_card_is_not_employment_fact(self):
        state = choose_card(start_intake(), "situation", "working")
        self.assertIsNone(state.profile.employment_status)

    def test_goal_unknown_can_start(self):
        state = choose_card(start_intake("goal"), "goal", "unknown")
        self.assertEqual(state.stage, Stage.BASIC)
        self.assertIn("goal", state.skipped)

    def test_skipping_opening_keeps_normal_path(self):
        state = choose_card(start_intake(), "situation", None)
        self.assertEqual(state.stage, Stage.INTEREST)
        self.assertIn("situation", state.skipped)

    def test_interest_cannot_precede_opening(self):
        with self.assertRaises(ValueError):
            choose_card(start_intake(), "interest", "unknown")

    def test_invalid_mode_or_card_rejected(self):
        with self.assertRaises(ValueError):
            start_intake("chat")
        with self.assertRaises(ValueError):
            choose_card(start_intake(), "situation", "unemployed")

    def test_fact_cannot_precede_cards(self):
        with self.assertRaises(ValueError):
            answer_fact(start_intake(), "age", 24)

    def test_updates_leave_original_state_intact(self):
        old = basic_state()
        new = answer_fact(old, "age", 24)
        self.assertIsNone(old.profile.age)
        self.assertEqual(new.profile.age, 24)
        self.assertEqual(new.revision, old.revision + 1)

    def test_unknown_can_be_corrected_and_cleared(self):
        state = answer_fact(basic_state(), "age", None)
        self.assertIn("age", state.skipped)
        state = answer_fact(state, "age", 24)
        self.assertNotIn("age", state.skipped)
        self.assertIn("age", state.answered)
        state = answer_fact(state, "age", None)
        self.assertIsNone(state.profile.age)
        self.assertNotIn("age", state.answered)

    def test_invalid_age_and_unknown_fact_rejected(self):
        for value in (True, -1, 121, "24"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                answer_fact(basic_state(), "age", value)
        with self.assertRaises(ValueError):
            answer_fact(basic_state(), "income", "0")

    def test_bad_region_and_employment_rejected(self):
        for key, value in (("region_code", "서울"), ("region_code", "11"),
                           ("employment_status", "쉬고 있어요")):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                answer_fact(basic_state(), key, value)

    def test_detail_needs_explicit_policy_interest(self):
        with self.assertRaises(ValueError):
            choose_detail(show_results(basic_state()), True, needs_information=True)

    def test_selection_must_come_from_current_candidates(self):
        with self.assertRaises(ValueError):
            select_policy(show_results(basic_state()), "outside", ("TEST-ONLY",))

    def test_declining_detail_preserves_facts(self):
        state = answer_fact(basic_state(), "age", 24)
        state = select_policy(show_results(state), "TEST-ONLY", ("TEST-ONLY",))
        state = choose_detail(state, False, needs_information=True)
        self.assertEqual(state.stage, Stage.RESULTS)
        self.assertEqual(state.profile.age, 24)
        self.assertIsNone(next_question(state, (policy(),), reference_date=TODAY))
        self.assertEqual(prepare(state).stage, Stage.PREPARATION)

    def test_no_detail_when_information_is_sufficient(self):
        state = select_policy(show_results(basic_state()), "TEST-ONLY", ("TEST-ONLY",))
        self.assertEqual(choose_detail(state, True, needs_information=False).stage, Stage.RESULTS)

    def test_pause_resume_keeps_answers_and_skips(self):
        state = answer_fact(detail_state(), "age", 24)
        state = answer_fact(state, "region_code", None)
        paused = pause_detail(state)
        self.assertEqual(paused.stage, Stage.RESULTS)
        self.assertEqual(resume_detail(paused).profile.age, 24)
        self.assertIn("region_code", resume_detail(paused).skipped)

    def test_cannot_resume_declined_detail(self):
        with self.assertRaises(ValueError):
            resume_detail(show_results(basic_state()))

    def test_switching_policy_resets_detail_choice(self):
        paused = pause_detail(detail_state())
        new = select_policy(paused, "TEST-2", ("TEST-ONLY", "TEST-2"))
        self.assertIsNone(new.detail_choice)
        self.assertFalse(new.detail_paused)

    def test_preferences_are_not_profile_facts(self):
        state = answer_preference(detail_state(), "participation_format", "online")
        self.assertEqual(state.profile, UserProfile())
        self.assertEqual(dict(state.preferences)["participation_format"], "online")
        with self.assertRaises(ValueError):
            answer_preference(basic_state(), "participation_format", "online")


class ConditionTests(unittest.TestCase):
    def test_missing_fact_and_missing_policy_are_different(self):
        self.assertEqual(check("age").status, ConditionStatus.INPUT_MISSING)
        self.assertEqual(check("age", policy(age_min=None, age_max=None)).status,
                         ConditionStatus.CHECK_REQUIRED)

    def test_missing_inputs_do_not_become_confirmed(self):
        result = assess_conditions(policy(), UserProfile(), reference_date=TODAY)
        self.assertEqual(result.legacy_status, MatchStatus.UNKNOWN)
        missing = {c.field for c in result.checks if c.status is ConditionStatus.INPUT_MISSING}
        self.assertEqual(missing, {"age", "region_code", "employment_status"})

    def test_age_boundaries_are_inclusive(self):
        for age in (19, 34):
            with self.subTest(age=age):
                self.assertEqual(check("age", profile=UserProfile(age=age)).status, ConditionStatus.CONFIRMED)
        for age in (18, 35):
            with self.subTest(age=age):
                self.assertEqual(check("age", profile=UserProfile(age=age)).status, ConditionStatus.NOT_MET)

    def test_expired_snapshot_open_is_rechecked(self):
        old = policy(application_end=date(2026, 10, 6))
        self.assertEqual(check("application", old).status, ConditionStatus.NOT_MET)

    def test_future_period_and_unknown_period_need_confirmation(self):
        future = policy(application_start=date(2026, 10, 8))
        self.assertEqual(check("application", future).status, ConditionStatus.CHECK_REQUIRED)
        undated = policy(application_start=None, application_end=None)
        self.assertEqual(check("application", undated).status, ConditionStatus.CHECK_REQUIRED)

    def test_period_end_is_inclusive_and_closed_wins(self):
        self.assertEqual(check("application", policy(application_end=TODAY)).status, ConditionStatus.CONFIRMED)
        self.assertEqual(check("application", policy(application_status=ApplicationStatus.CLOSED)).status,
                         ConditionStatus.NOT_MET)

    def test_specific_region_compare_and_broad_region_unknown(self):
        self.assertEqual(check("region_code", profile=UserProfile(region_code="11680")).status,
                         ConditionStatus.CONFIRMED)
        self.assertEqual(check("region_code", profile=UserProfile(region_code="11110")).status,
                         ConditionStatus.NOT_MET)
        for code in (None, "11", "11000", "전국", "11680,broken"):
            with self.subTest(code=code):
                self.assertEqual(check("region_code", policy(region_code=code), UserProfile(region_code="11680")).status,
                                 ConditionStatus.CHECK_REQUIRED)

    def test_multiple_specific_regions(self):
        record = policy(region_code="11110, 11680")
        self.assertEqual(check("region_code", record, UserProfile(region_code="11680")).status,
                         ConditionStatus.CONFIRMED)

    def test_employment_free_text_not_hard_excluded(self):
        record = policy(employment_status="미취업자 또는 근로시간 제한 재직자")
        self.assertEqual(check("employment_status", record, UserProfile(employment_status="재직자")).status,
                         ConditionStatus.CHECK_REQUIRED)

    def test_explicit_employment_mismatch(self):
        self.assertEqual(check("employment_status", profile=UserProfile(employment_status="재직자")).status,
                         ConditionStatus.NOT_MET)

    def test_no_restriction_does_not_request_employment(self):
        self.assertEqual(check("employment_status", policy(employment_status="제한없음")).status,
                         ConditionStatus.CONFIRMED)

    def test_income_education_and_extra_text_are_not_invented(self):
        record = policy(income_condition="가구 중위소득 100%", education_status="대학 졸업",
                        eligibility_text="별도 제한")
        for field in ("income", "education", "eligibility"):
            with self.subTest(field=field):
                self.assertEqual(check(field, record).status, ConditionStatus.CHECK_REQUIRED)

    def test_unrecorded_extra_conditions_do_not_mean_no_conditions(self):
        self.assertEqual(check("eligibility", policy(eligibility_text=None)).status,
                         ConditionStatus.CHECK_REQUIRED)

    def test_clear_mismatch_dominates_uncertainty(self):
        result = assess_conditions(policy(), UserProfile(age=18), reference_date=TODAY)
        self.assertEqual(result.status, ConditionStatus.NOT_MET)
        self.assertEqual(result.legacy_status, MatchStatus.NO_MATCH)


class ServiceTests(unittest.TestCase):
    def test_basic_asks_only_needed_unanswered_facts(self):
        state = basic_state()
        self.assertEqual(next_question(state, (policy(),), reference_date=TODAY).key, "age")
        state = answer_fact(state, "age", 24)
        self.assertEqual(next_question(state, (policy(),), reference_date=TODAY).key, "region_code")
        state = answer_fact(state, "region_code", "11680")
        self.assertIsNone(next_question(state, (policy(),), reference_date=TODAY))

    def test_skipped_fact_not_repeated(self):
        state = answer_fact(basic_state(), "age", None)
        self.assertEqual(next_question(state, (policy(),), reference_date=TODAY).key, "region_code")

    def test_detail_only_asks_selected_candidate_requirements(self):
        state = detail_state()
        state = answer_fact(answer_fact(state, "age", 24), "region_code", "11680")
        selected = policy(employment_status="제한없음")
        other = policy(policy_id="TEST-2")
        self.assertIsNone(next_question(state, (selected, other), reference_date=TODAY))

    def test_correction_recomputes_results(self):
        state = answer_fact(basic_state(), "age", 24)
        self.assertEqual(len(build_guidance((policy(),), state, reference_date=TODAY)), 1)
        state = answer_fact(state, "age", 35)
        self.assertEqual(build_guidance((policy(),), state, reference_date=TODAY), ())

    def test_completed_or_skipped_questions_stop(self):
        state = detail_state()
        for key in ("age", "region_code", "employment_status"):
            state = answer_fact(state, key, None)
        self.assertIsNone(next_question(state, (policy(),), reference_date=TODAY))
        self.assertFalse(detail_is_useful(state, (policy(),), reference_date=TODAY))

    def test_detail_offer_requires_interest_and_missing_info(self):
        state = show_results(basic_state())
        self.assertFalse(detail_is_useful(state, (policy(),), reference_date=TODAY))
        state = select_policy(state, "TEST-ONLY", ("TEST-ONLY",))
        self.assertTrue(detail_is_useful(state, (policy(),), reference_date=TODAY))

    def test_empty_or_all_excluded_data_has_no_questions(self):
        state = basic_state()
        self.assertIsNone(next_question(state, (), reference_date=TODAY))
        closed = policy(application_status=ApplicationStatus.CLOSED)
        self.assertEqual(build_guidance((closed,), state, reference_date=TODAY), ())
        self.assertIsNone(next_question(state, (closed,), reference_date=TODAY))

    def test_guidance_retains_evidence_and_no_final_qualification(self):
        record = policy()
        result = build_guidance((record,), basic_state(), reference_date=TODAY)[0]
        self.assertEqual(result.source_url, record.source_url)
        self.assertEqual(result.last_verified_at, record.last_verified_at)
        self.assertIn("기관", " ".join(result.next_actions))
        self.assertNotIn("신청 가능합니다", " ".join(result.next_actions))

    def test_source_link_must_be_web_url(self):
        for url in (None, "javascript:alert(1)", "file:///secret", "invalid"):
            with self.subTest(url=url):
                result = build_guidance((policy(source_url=url),), basic_state(), reference_date=TODAY)[0]
                self.assertIsNone(result.source_url)

    def test_duplicate_policy_ids_rejected(self):
        with self.assertRaises(ValueError):
            build_guidance((policy(), policy()), basic_state(), reference_date=TODAY)

    def test_preferences_never_change_qualification(self):
        state = detail_state()
        before = build_guidance((policy(),), state, reference_date=TODAY)
        state = answer_preference(state, "participation_format", "online")
        self.assertEqual(before, build_guidance((policy(),), state, reference_date=TODAY))


if __name__ == "__main__":
    unittest.main()
