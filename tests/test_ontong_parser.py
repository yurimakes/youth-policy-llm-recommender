"""test_ontong_parser.py

온통청년 예시 JSON 파싱과 PolicyRecord 변환을 테스트합니다.
"""

from datetime import date, datetime
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from career_catch.models import ApplicationStatus
from career_catch.ontong_parser import parse_policy_item, parse_policy_page


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "ontong_youth_policy_page1.json"
VERIFIED_AT = datetime(2026, 6, 29, 0, 0, 0)
REFERENCE_DATE = date(2026, 6, 29)


def load_fixture() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def parse_fixture():
    return parse_policy_page(
        load_fixture(),
        verified_at=VERIFIED_AT,
        reference_date=REFERENCE_DATE,
    )


def test_fixture_shape_matches_official_sample():
    payload = load_fixture()
    result = payload["result"]

    assert payload["resultCode"] == 200
    assert result["pagging"]["pageSize"] == 10
    assert len(result["youthPolicyList"]) == 10


def test_parse_policy_page_returns_ten_records():
    records = parse_fixture()

    assert len(records) == 10


def test_first_policy_maps_core_fields():
    payload = load_fixture()
    first_item = payload["result"]["youthPolicyList"][0]
    first_record = parse_fixture()[0]

    assert first_record.policy_id == first_item["plcyNo"]
    assert first_record.policy_name == first_item["plcyNm"]
    assert first_record.category == "일자리 > 취업"
    assert first_record.age_min == 19
    assert first_record.age_max == 39
    assert first_record.employment_status == "미취업자"
    assert first_record.education_status == "제한없음"
    assert first_record.application_start == date(2026, 6, 1)
    assert first_record.application_end == date(2026, 9, 30)
    assert first_record.application_status is ApplicationStatus.OPEN


def test_application_status_uses_period_code_and_dates_not_approval_status():
    records = parse_fixture()

    assert records[0].application_status is ApplicationStatus.OPEN
    assert records[1].application_status is ApplicationStatus.CLOSED
    assert records[2].application_status is ApplicationStatus.UPCOMING
    assert records[1].application_status is not ApplicationStatus.OPEN


def test_always_open_policy_with_blank_period_has_open_status_and_no_dates():
    payload = load_fixture()
    records = parse_fixture()
    items = payload["result"]["youthPolicyList"]

    record = next(
        record
        for record, item in zip(records, items)
        if item["aplyPrdSeCd"] == "0057002" and item["aplyYmd"].strip() == ""
    )

    assert record.application_status is ApplicationStatus.OPEN
    assert record.application_start is None
    assert record.application_end is None


def test_region_code_preserves_comma_joined_codes():
    payload = load_fixture()
    first_item = payload["result"]["youthPolicyList"][0]
    first_record = parse_fixture()[0]

    assert first_record.region_code == first_item["zipCd"].strip()
    assert "," in first_record.region_code


def test_sbiz_code_is_included_in_embedding_text():
    first_record = parse_fixture()[0]

    assert "제한없음" in first_record.embedding_text
    assert first_record.embedding_text.count("제한없음") >= 2


def test_eligibility_text_uses_blank_line_between_sections():
    record = parse_policy_item(
        {
            "plcyNo": "policy-eligibility",
            "plcyNm": "Eligibility Policy",
            "addAplyQlfcCndCn": "조건 내용",
            "ptcpPrpTrgtCn": "제한 내용",
        },
        verified_at=VERIFIED_AT,
        reference_date=REFERENCE_DATE,
    )

    assert record.eligibility_text == "추가 신청 자격: 조건 내용\n\n참여 제한 대상: 제한 내용"


def test_always_open_period_code_overrides_rejected_approval_status():
    record = parse_policy_item(
        {
            "plcyNo": "policy-always-open",
            "plcyNm": "Always Open Policy",
            "aplyPrdSeCd": "0057002",
            "plcyAprvSttsCd": "0044003",
        },
        verified_at=VERIFIED_AT,
        reference_date=REFERENCE_DATE,
    )

    assert record.application_status is ApplicationStatus.OPEN


def test_malformed_payloads_raise_value_error():
    valid_payload = load_fixture()

    with pytest.raises(ValueError, match="resultCode"):
        parse_policy_page(
            {**valid_payload, "resultCode": 500},
            verified_at=VERIFIED_AT,
            reference_date=REFERENCE_DATE,
        )

    with pytest.raises(ValueError, match="result"):
        parse_policy_page(
            {**valid_payload, "result": []},
            verified_at=VERIFIED_AT,
            reference_date=REFERENCE_DATE,
        )

    with pytest.raises(ValueError, match="youthPolicyList"):
        parse_policy_page(
            {**valid_payload, "result": {"youthPolicyList": {}}},
            verified_at=VERIFIED_AT,
            reference_date=REFERENCE_DATE,
        )

    with pytest.raises(ValueError, match="items"):
        parse_policy_page(
            {**valid_payload, "result": {"youthPolicyList": ["not-a-dict"]}},
            verified_at=VERIFIED_AT,
            reference_date=REFERENCE_DATE,
        )
