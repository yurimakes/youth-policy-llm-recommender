"""intake_contract.py

UI 비종속 JSON 계약을 검증하고 기존 진행 로직으로 상태 전환을 수행합니다.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from typing import Any

from youth_policy.codebook import REGION_CODE_TO_NAME
from youth_policy.conditions import EMPLOYMENT_VALUES, STATUS_LABELS, validate_profile
from youth_policy.intake import (
    CARD_OPTIONS, FACT_FIELDS, PREFERENCE_OPTIONS, IntakeState, Stage,
    answer_fact, answer_preference, choose_card, choose_detail, pause_detail,
    prepare, resume_detail, select_policy, show_results, start_intake,
)
from youth_policy.intake_service import build_guidance, detail_is_useful, next_question
from youth_policy.matching import UserProfile
from youth_policy.models import PolicyRecord


class PayloadError(ValueError):
    """구조화된 입력 또는 진행 상태가 계약과 맞지 않습니다."""


class TransitionConflict(ValueError):
    """현재 단계 또는 정책 후보에서 해당 동작을 수행할 수 없습니다."""


STATE_KEYS = frozenset({
    "start_mode", "stage", "cards", "profile", "preferences", "answered", "skipped",
    "interested_policy_id", "detail_choice", "detail_paused", "revision",
})


def state_to_payload(state: IntakeState) -> dict[str, Any]:
    return {
        "start_mode": state.start_mode, "stage": state.stage.value,
        "cards": dict(state.cards),
        "profile": {"age": state.profile.age, "region_code": state.profile.region_code,
                    "employment_status": state.profile.employment_status},
        "preferences": dict(state.preferences), "answered": list(state.answered),
        "skipped": list(state.skipped), "interested_policy_id": state.interested_policy_id,
        "detail_choice": state.detail_choice, "detail_paused": state.detail_paused,
        "revision": state.revision,
    }


def state_from_payload(payload: dict[str, Any]) -> IntakeState:
    """클라이언트 상태를 검증하며 후보·판정 결과는 입력으로 받지 않습니다."""
    if not isinstance(payload, dict) or set(payload) != STATE_KEYS:
        raise PayloadError("state fields do not match the contract")
    if not isinstance(payload["start_mode"], str) or payload["start_mode"] not in {"situation", "goal"}:
        raise PayloadError("invalid start mode")
    try:
        stage = Stage(payload["stage"])
    except (ValueError, TypeError) as exc:
        raise PayloadError("invalid stage") from exc
    cards, preferences, profile = payload["cards"], payload["preferences"], payload["profile"]
    allowed_cards = {payload["start_mode"], "interest"} if payload["start_mode"] == "situation" else {"goal"}
    if not isinstance(cards, dict) or not set(cards) <= allowed_cards:
        raise PayloadError("invalid card fields")
    if any(not isinstance(v, str) or v not in dict(CARD_OPTIONS[k]) for k, v in cards.items()):
        raise PayloadError("invalid card values")
    if not isinstance(preferences, dict) or not set(preferences) <= set(PREFERENCE_OPTIONS):
        raise PayloadError("invalid preference fields")
    if any(not isinstance(v, str) or v not in PREFERENCE_OPTIONS[k] for k, v in preferences.items()):
        raise PayloadError("invalid preference values")
    if not isinstance(profile, dict) or set(profile) != FACT_FIELDS:
        raise PayloadError("invalid profile fields")
    try:
        user = UserProfile(**profile)
        validate_profile(user)
    except (ValueError, TypeError) as exc:
        raise PayloadError("invalid profile values") from exc
    allowed_history = allowed_cards | FACT_FIELDS | set(PREFERENCE_OPTIONS)
    answered, skipped = payload["answered"], payload["skipped"]
    for history in (answered, skipped):
        if (not isinstance(history, list) or any(not isinstance(k, str) for k in history)
                or len(history) != len(set(history)) or not set(history) <= allowed_history):
            raise PayloadError("invalid answer history")
    if set(answered) & set(skipped):
        raise PayloadError("answered and skipped fields overlap")
    for key in allowed_history:
        value = cards.get(key) if key in allowed_cards else (
            profile.get(key) if key in FACT_FIELDS else preferences.get(key)
        )
        has_answer = value is not None and not (key in allowed_cards and value == "unknown")
        if (key in answered) != has_answer:
            raise PayloadError("answers and history are inconsistent")
        if key in cards and cards[key] == "unknown" and key not in skipped:
            raise PayloadError("unknown card requires a skipped history item")
    policy_id = payload["interested_policy_id"]
    if policy_id is not None and (not isinstance(policy_id, str) or not policy_id.strip() or len(policy_id) > 128):
        raise PayloadError("invalid interested policy ID")
    choice, paused, revision = payload["detail_choice"], payload["detail_paused"], payload["revision"]
    if choice is not None and type(choice) is not bool:
        raise PayloadError("detail choice must be boolean or null")
    if type(paused) is not bool or type(revision) is not int or revision < 0:
        raise PayloadError("invalid pause or revision value")
    completed = set(answered) | set(skipped)
    opening_done = payload["start_mode"] in completed
    interest_done = "interest" in completed
    if stage is Stage.START:
        if completed or cards or preferences or any(v is not None for v in profile.values()) or policy_id or choice is not None or paused:
            raise PayloadError("start state contains later-stage information")
    elif stage is Stage.INTEREST:
        if payload["start_mode"] != "situation" or not opening_done or interest_done:
            raise PayloadError("interest stage requires only the opening card")
        if (set(completed) - {"situation"}) or preferences or policy_id or choice is not None or paused:
            raise PayloadError("interest state contains later-stage information")
    elif not opening_done or (payload["start_mode"] == "situation" and not interest_done):
        raise PayloadError("opening cards are incomplete")
    if stage is Stage.DETAIL and (choice is not True or policy_id is None or paused):
        raise PayloadError("detail stage requires an explicit accepted choice")
    if paused and (stage is not Stage.RESULTS or choice is not True or policy_id is None):
        raise PayloadError("invalid paused detail state")
    if choice is not None and policy_id is None:
        raise PayloadError("detail choice requires a selected policy")
    return IntakeState(payload["start_mode"], stage, tuple(cards.items()), user,
                       tuple(preferences.items()), tuple(answered), tuple(skipped),
                       policy_id, choice, paused, revision)


def apply_action(
    state: IntakeState, action: dict[str, Any], policies: tuple[PolicyRecord, ...], *, reference_date: date
) -> IntakeState:
    if not isinstance(action, dict) or not isinstance(action.get("type"), str):
        raise PayloadError("an action type is required")
    kind = action["type"]
    shape = {
        "choose_card": {"type", "key", "value"}, "answer_fact": {"type", "key", "value"},
        "answer_preference": {"type", "key", "value"}, "select_policy": {"type", "policy_id"},
        "choose_detail": {"type", "accept"}, "show_results": {"type"},
        "pause_detail": {"type"}, "resume_detail": {"type"}, "prepare": {"type"},
    }
    if kind not in shape or set(action) != shape[kind]:
        raise PayloadError("action fields do not match the contract")
    for key in ("key", "policy_id"):
        if key in action and (not isinstance(action[key], str) or not action[key].strip() or len(action[key]) > 128):
            raise PayloadError("action identifier is invalid")
    if "value" in action and action["value"] is not None and type(action["value"]) not in {str, int}:
        raise PayloadError("answer must be a structured selection, integer or null")
    if kind == "answer_fact":
        if action["key"] not in FACT_FIELDS:
            raise PayloadError("unsupported fact")
        try:
            validate_profile(replace(state.profile, **{action["key"]: action["value"]}))
        except (ValueError, TypeError) as exc:
            raise PayloadError("invalid fact answer") from exc
    if kind == "choose_detail" and type(action["accept"]) is not bool:
        raise PayloadError("accept must be boolean")
    try:
        if kind == "choose_card":
            value = action["value"]
            if value is not None and not isinstance(value, str):
                raise PayloadError("card value must be a string or null")
            updated = choose_card(state, action["key"], value)
            return replace(updated, interested_policy_id=None, detail_choice=None, detail_paused=False)
        if kind == "answer_fact":
            return answer_fact(state, action["key"], action["value"])
        if kind == "answer_preference":
            return answer_preference(state, action["key"], action["value"])
        if kind == "show_results":
            return show_results(state)
        if kind == "select_policy":
            candidates = build_guidance(policies, state, reference_date=reference_date)
            return select_policy(state, action["policy_id"], tuple(p.policy_id for p in candidates))
        if kind == "choose_detail":
            candidates = build_guidance(policies, state, reference_date=reference_date)
            if state.interested_policy_id not in {p.policy_id for p in candidates}:
                raise TransitionConflict("selected policy is no longer a current candidate")
            return choose_detail(state, action["accept"], needs_information=detail_is_useful(
                state, policies, reference_date=reference_date))
        if kind == "pause_detail":
            return pause_detail(state)
        if kind == "resume_detail":
            candidates = build_guidance(policies, state, reference_date=reference_date)
            if state.interested_policy_id not in {p.policy_id for p in candidates}:
                raise TransitionConflict("selected policy is no longer a current candidate")
            return resume_detail(state)
        return prepare(state)
    except PayloadError:
        raise
    except (ValueError, TypeError) as exc:
        raise TransitionConflict("action is not valid for the current stage or candidate") from exc


def response_payload(
    state: IntakeState, policies: tuple[PolicyRecord, ...], *, reference_date: date,
    data_status: str = "ready",
) -> dict[str, Any]:
    question = _question(state, policies, reference_date)
    guidances = () if state.stage in {Stage.START, Stage.INTEREST} else build_guidance(
        policies, state, reference_date=reference_date)
    catalog = {p.policy_id: p for p in policies}
    candidates = [{
        "policy_id": p.policy_id, "policy_name": p.policy_name,
        "summary": catalog[p.policy_id].summary, "benefit_text": catalog[p.policy_id].benefit_text,
        "status": p.assessment.status.value, "status_label": STATUS_LABELS[p.assessment.status],
        "checks": [{"field": c.field, "status": c.status.value,
                    "status_label": STATUS_LABELS[c.status], "reason": c.reason} for c in p.assessment.checks],
        "next_actions": list(p.next_actions), "source_name": catalog[p.policy_id].source_name,
        "source_url": p.source_url, "last_verified_at": p.last_verified_at.isoformat(),
    } for p in guidances]
    excluded = state.interested_policy_id is not None and state.interested_policy_id not in {p.policy_id for p in guidances}
    offer = state.stage is Stage.RESULTS and state.detail_choice is None and detail_is_useful(
        state, policies, reference_date=reference_date)
    return {
        "api_version": "1", "state": state_to_payload(state), "next_question": question,
        "candidates": candidates, "data_status": data_status,
        "detail_offer_available": offer, "selected_policy_excluded": excluded,
        "can_show_results": state.stage in {Stage.BASIC, Stage.DETAIL, Stage.RESULTS, Stage.PREPARATION},
        "notice": "확인된 개별 조건은 전체 신청 자격 확정이 아닙니다. 최종 자격은 공식 공고와 담당 기관에서 확인하세요.",
    }


def _question(state: IntakeState, policies: tuple[PolicyRecord, ...], today: date) -> dict[str, Any] | None:
    if state.stage in {Stage.START, Stage.INTEREST}:
        key = state.start_mode if state.stage is Stage.START else "interest"
        prompts = {"situation": "요즘 어떻게 지내고 있나요?", "goal": "지금 가장 이루고 싶은 것은 무엇인가요?",
                   "interest": "어떤 도움이 먼저 필요할까요?"}
        return {"key": key, "prompt": prompts[key], "purpose": "상황이나 관심을 선택해 시작해요. 모르면 건너뛸 수 있어요.",
                "input_type": "card", "options": [{"value": k, "label": v} for k, v in CARD_OPTIONS[key]], "allow_skip": True}
    question = next_question(state, policies, reference_date=today)
    if question is None:
        return None
    options = []
    input_type = "integer" if question.key == "age" else "selection"
    if question.key == "employment_status":
        options = [{"value": v, "label": v} for v in sorted(EMPLOYMENT_VALUES)]
    elif question.key == "region_code":
        input_type = "region_code"
        options = [{"value": code, "label": name} for code, name in REGION_CODE_TO_NAME.items()]
    return {"key": question.key, "prompt": question.prompt, "purpose": question.purpose,
            "input_type": input_type, "options": options, "allow_skip": True}
