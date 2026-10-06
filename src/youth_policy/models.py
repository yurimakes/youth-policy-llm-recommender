"""models.py

정책 데이터 모델과 기본 유효성 검사를 정의하는 파일입니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum


class ApplicationStatus(str, Enum):
    UPCOMING = "upcoming"
    OPEN = "open"
    CLOSED = "closed"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class PolicyRecord:
    policy_id: str
    policy_name: str
    category: str | None
    summary: str | None
    region_code: str | None
    region_name: str | None
    age_min: int | None
    age_max: int | None
    income_condition: str | None
    employment_status: str | None
    education_status: str | None
    application_start: date | None
    application_end: date | None
    application_status: ApplicationStatus
    eligibility_text: str | None
    benefit_text: str | None
    application_method: str | None
    required_documents: str | None
    contact: str | None
    source_name: str
    source_url: str | None
    last_verified_at: datetime
    embedding_text: str

    def __post_init__(self) -> None:
        self._require_non_blank(self.policy_id, "policy_id")
        self._require_non_blank(self.policy_name, "policy_name")
        self._require_non_blank(self.source_name, "source_name")
        self._validate_age_bounds()
        self._validate_application_dates()

        if not isinstance(self.embedding_text, str):
            raise ValueError("embedding_text must be a string.")

    @staticmethod
    def _require_non_blank(value: str, field_name: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-blank string.")

    def _validate_age_bounds(self) -> None:
        if self.age_min is not None and self.age_min < 0:
            raise ValueError("age_min must be greater than or equal to 0.")
        if self.age_max is not None and self.age_max < 0:
            raise ValueError("age_max must be greater than or equal to 0.")
        if (
            self.age_min is not None
            and self.age_max is not None
            and self.age_min > self.age_max
        ):
            raise ValueError("age_min cannot be greater than age_max.")

    def _validate_application_dates(self) -> None:
        if (
            self.application_start is not None
            and self.application_end is not None
            and self.application_start > self.application_end
        ):
            raise ValueError("application_start cannot be later than application_end.")
