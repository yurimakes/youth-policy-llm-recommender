"""intake.py

카드 진입과 사용자가 선택한 상세 확인의 진행 상태를 관리합니다.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum

from youth_policy.conditions import validate_profile
from youth_policy.matching import UserProfile


class Stage(str, Enum):
    START = "start"
    INTEREST = "interest"
    BASIC = "basic"
    RESULTS = "results"
    DETAIL = "detail"
    PREPARATION = "preparation"


CARD_OPTIONS: dict[str, tuple[tuple[str, str], ...]] = {
    "situation": (("school", "학교에 다녀요"), ("working", "일하고 있어요"),
                  ("resting", "쉬고 있어요"), ("unknown", "답하기 어려워요")),
    "interest": (("living_cost", "생활비 부담 줄이기"), ("low_burden", "부담 적은 활동 찾기"),
                 ("counseling", "사람에게 상담받기"), ("unknown", "잘 모르겠어요")),
    "goal": (("employment", "취업하기"), ("housing", "나만의 공간에서 생활하기"),
             ("learning", "새로운 기술 배우기"), ("unknown", "잘 모르겠어요")),
}
FACT_FIELDS = frozenset({"age", "region_code", "employment_status"})
PREFERENCE_OPTIONS = {
    "participation_format": ("online", "offline", "either"),
    "contact_format": ("phone", "online", "in_person", "either"),
}


@dataclass(frozen=True)
class IntakeState:
    start_mode: str = "situation"
    stage: Stage = Stage.START
    cards: tuple[tuple[str, str], ...] = ()
    profile: UserProfile = field(default_factory=UserProfile)
    preferences: tuple[tuple[str, str], ...] = ()
    answered: tuple[str, ...] = ()
    skipped: tuple[str, ...] = ()
    interested_policy_id: str | None = None
    detail_choice: bool | None = None
    detail_paused: bool = False
    revision: int = 0


def start_intake(start_mode: str = "situation") -> IntakeState:
    if start_mode not in {"situation", "goal"}:
        raise ValueError("unsupported start mode")
    return IntakeState(start_mode=start_mode)


def choose_card(state: IntakeState, key: str, value: str | None) -> IntakeState:
    """카드의 모름/건너뛰기는 사실을 추정하는 입력으로 사용하지 않습니다."""
    allowed_keys = {state.start_mode, "interest"} if state.start_mode == "situation" else {"goal"}
    if key not in allowed_keys or (value is not None and value not in dict(CARD_OPTIONS[key])):
        raise ValueError("unsupported card selection")
    if state.stage is Stage.START and key != state.start_mode:
        raise ValueError("answer the opening card first")
    if state.stage is Stage.INTEREST and key != "interest":
        # Correcting the opening answer is allowed, but it does not complete the interest step.
        target = Stage.INTEREST
    elif key == "situation" and state.stage is Stage.START:
        target = Stage.INTEREST
    else:
        target = Stage.BASIC
    cards = dict(state.cards)
    if value is None:
        cards.pop(key, None)
    else:
        cards[key] = value
    return _advance(state, stage=target, cards=tuple(cards.items()),
                    **_history(state, key, value in {None, "unknown"}))


def answer_fact(state: IntakeState, key: str, value: int | str | None) -> IntakeState:
    if key not in FACT_FIELDS or state.stage in {Stage.START, Stage.INTEREST}:
        raise ValueError("fact is not available at this stage")
    profile = replace(state.profile, **{key: value})
    validate_profile(profile)
    return _advance(state, profile=profile, **_history(state, key, value is None))


def answer_preference(state: IntakeState, key: str, value: str | None) -> IntakeState:
    if state.stage is not Stage.DETAIL or key not in PREFERENCE_OPTIONS:
        raise ValueError("preferences belong to the optional detail stage")
    if value is not None and value not in PREFERENCE_OPTIONS[key]:
        raise ValueError("unsupported preference")
    preferences = dict(state.preferences)
    if value is None:
        preferences.pop(key, None)
    else:
        preferences[key] = value
    return _advance(state, preferences=tuple(preferences.items()),
                    **_history(state, key, value is None))


def show_results(state: IntakeState) -> IntakeState:
    if state.stage not in {Stage.BASIC, Stage.DETAIL, Stage.RESULTS, Stage.PREPARATION}:
        raise ValueError("finish the opening cards first")
    return _advance(state, stage=Stage.RESULTS, detail_paused=False)


def select_policy(state: IntakeState, policy_id: str, candidate_ids: tuple[str, ...]) -> IntakeState:
    if state.stage is not Stage.RESULTS or policy_id not in candidate_ids:
        raise ValueError("select a policy from the current results")
    if state.interested_policy_id == policy_id:
        return state
    return _advance(state, interested_policy_id=policy_id, detail_choice=None, detail_paused=False)


def choose_detail(state: IntakeState, accept: bool, *, needs_information: bool) -> IntakeState:
    if state.stage is not Stage.RESULTS or state.interested_policy_id is None:
        raise ValueError("an explicit policy interest action must precede detail choice")
    if type(accept) is not bool or type(needs_information) is not bool:
        raise ValueError("detail choice must be boolean")
    return _advance(state, detail_choice=accept, detail_paused=False,
                    stage=Stage.DETAIL if accept and needs_information else Stage.RESULTS)


def pause_detail(state: IntakeState) -> IntakeState:
    if state.stage is not Stage.DETAIL:
        raise ValueError("only an active detail stage can be paused")
    return _advance(state, stage=Stage.RESULTS, detail_paused=True)


def resume_detail(state: IntakeState) -> IntakeState:
    if state.stage is not Stage.RESULTS or not state.detail_paused or state.detail_choice is not True:
        raise ValueError("no accepted paused detail stage to resume")
    return _advance(state, stage=Stage.DETAIL, detail_paused=False)


def prepare(state: IntakeState) -> IntakeState:
    if state.stage is not Stage.RESULTS:
        raise ValueError("preparation follows results")
    return _advance(state, stage=Stage.PREPARATION)


def _history(state: IntakeState, key: str, skipped: bool) -> dict[str, tuple[str, ...]]:
    return {
        "answered": tuple(x for x in state.answered if x != key) + (() if skipped else (key,)),
        "skipped": tuple(x for x in state.skipped if x != key) + ((key,) if skipped else ()),
    }


def _advance(state: IntakeState, **changes: object) -> IntakeState:
    return replace(state, revision=state.revision + 1, **changes)
