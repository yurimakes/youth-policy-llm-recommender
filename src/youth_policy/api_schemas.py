"""api_schemas.py

FastAPI의 구조화된 입력·응답과 OpenAPI 계약을 정의합니다.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StringConstraints

from youth_policy.conditions import ConditionStatus
from youth_policy.intake import Stage


ShortString = Annotated[str, StringConstraints(strict=True, max_length=128)]


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProfileSchema(ContractModel):
    age: Annotated[StrictInt, Field(ge=0, le=120)] | None = None
    region_code: Annotated[str, StringConstraints(strict=True, pattern=r"^[0-9]{5}$")] | None = None
    employment_status: ShortString | None = None


class StateSchema(ContractModel):
    start_mode: Literal["situation", "goal"]
    stage: Stage
    cards: dict[ShortString, ShortString] = Field(max_length=2)
    profile: ProfileSchema
    preferences: dict[ShortString, ShortString] = Field(max_length=2)
    answered: list[ShortString] = Field(max_length=7)
    skipped: list[ShortString] = Field(max_length=7)
    interested_policy_id: ShortString | None
    detail_choice: StrictBool | None
    detail_paused: StrictBool
    revision: Annotated[StrictInt, Field(ge=0)]


class StartRequest(ContractModel):
    start_mode: Literal["situation", "goal"] = "situation"


class CardAction(ContractModel):
    type: Literal["choose_card"]
    key: Literal["situation", "interest", "goal"]
    value: ShortString | None


class FactAction(ContractModel):
    type: Literal["answer_fact"]
    key: Literal["age", "region_code", "employment_status"]
    value: StrictInt | ShortString | None


class PreferenceAction(ContractModel):
    type: Literal["answer_preference"]
    key: Literal["participation_format", "contact_format"]
    value: ShortString | None


class SelectPolicyAction(ContractModel):
    type: Literal["select_policy"]
    policy_id: ShortString


class DetailAction(ContractModel):
    type: Literal["choose_detail"]
    accept: StrictBool


class SimpleAction(ContractModel):
    type: Literal["show_results", "pause_detail", "resume_detail", "prepare"]


ActionSchema = Annotated[
    CardAction | FactAction | PreferenceAction | SelectPolicyAction | DetailAction | SimpleAction,
    Field(discriminator="type"),
]


class TransitionRequest(ContractModel):
    state: StateSchema
    action: ActionSchema


class ChoiceSchema(ContractModel):
    value: str
    label: str


class QuestionSchema(ContractModel):
    key: str
    prompt: str
    purpose: str
    input_type: Literal["card", "integer", "selection", "region_code"]
    options: list[ChoiceSchema]
    allow_skip: bool


class CheckSchema(ContractModel):
    field: str
    status: ConditionStatus
    status_label: str
    reason: str


class CandidateSchema(ContractModel):
    policy_id: str
    policy_name: str
    summary: str | None
    benefit_text: str | None
    status: ConditionStatus
    status_label: str
    checks: list[CheckSchema]
    next_actions: list[str]
    source_name: str
    source_url: str | None
    last_verified_at: datetime


class IntakeResponse(ContractModel):
    api_version: Literal["1"]
    state: StateSchema
    next_question: QuestionSchema | None
    candidates: list[CandidateSchema]
    data_status: Literal["ready", "empty", "not_loaded"]
    detail_offer_available: bool
    selected_policy_excluded: bool
    can_show_results: bool
    notice: str
