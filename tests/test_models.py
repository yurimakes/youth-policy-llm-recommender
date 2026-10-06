"""test_models.py

PolicyRecord 생성 및 검증 동작을 테스트하는 파일입니다.
"""

from datetime import date, datetime
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from youth_policy.models import ApplicationStatus, PolicyRecord


def make_policy_record(**overrides):
    values = {
        "policy_id": "policy-001",
        "policy_name": "Youth Support Policy",
        "category": "employment",
        "summary": "Short official summary",
        "region_code": "11",
        "region_name": "Seoul",
        "age_min": 19,
        "age_max": 34,
        "income_condition": "Official income condition",
        "employment_status": "unemployed",
        "education_status": "any",
        "application_start": date(2026, 1, 1),
        "application_end": date(2026, 12, 31),
        "application_status": ApplicationStatus.OPEN,
        "eligibility_text": "Official eligibility text",
        "benefit_text": "Official benefit text",
        "application_method": "Online",
        "required_documents": "Application form",
        "contact": "Official contact",
        "source_name": "Ontong Youth",
        "source_url": "https://www.youthcenter.go.kr",
        "last_verified_at": datetime(2026, 6, 28, 12, 0, 0),
        "embedding_text": "Youth Support Policy employment official text",
    }
    values.update(overrides)
    return PolicyRecord(**values)


def test_create_valid_policy_record():
    record = make_policy_record()

    assert record.policy_id == "policy-001"
    assert record.application_status is ApplicationStatus.OPEN


def test_application_status_values():
    assert ApplicationStatus.UPCOMING.value == "upcoming"
    assert ApplicationStatus.OPEN.value == "open"
    assert ApplicationStatus.CLOSED.value == "closed"
    assert ApplicationStatus.UNKNOWN.value == "unknown"


def test_reject_blank_policy_id():
    with pytest.raises(ValueError, match="policy_id"):
        make_policy_record(policy_id=" ")


def test_reject_blank_policy_name():
    with pytest.raises(ValueError, match="policy_name"):
        make_policy_record(policy_name="")


def test_reject_negative_age():
    with pytest.raises(ValueError, match="age_min"):
        make_policy_record(age_min=-1)

    with pytest.raises(ValueError, match="age_max"):
        make_policy_record(age_max=-1)


def test_reject_age_min_greater_than_age_max():
    with pytest.raises(ValueError, match="age_min"):
        make_policy_record(age_min=35, age_max=34)


def test_reject_application_start_after_application_end():
    with pytest.raises(ValueError, match="application_start"):
        make_policy_record(
            application_start=date(2026, 12, 31),
            application_end=date(2026, 1, 1),
        )


def test_optional_fields_can_be_none():
    record = make_policy_record(
        category=None,
        summary=None,
        region_code=None,
        region_name=None,
        age_min=None,
        age_max=None,
        income_condition=None,
        employment_status=None,
        education_status=None,
        application_start=None,
        application_end=None,
        eligibility_text=None,
        benefit_text=None,
        application_method=None,
        required_documents=None,
        contact=None,
        source_url=None,
    )

    assert record.category is None
    assert record.source_url is None
