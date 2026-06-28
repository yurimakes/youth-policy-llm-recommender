"""ontong_parser.py

온통청년 공식 예시 JSON을 PolicyRecord 목록으로 변환합니다.
"""

from __future__ import annotations

from datetime import date, datetime

from career_catch.codebook import decode_code
from career_catch.models import ApplicationStatus, PolicyRecord


def _clean_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None

    cleaned = value.strip()
    if not cleaned:
        return None

    return cleaned


def _parse_compact_date(value: object) -> date | None:
    cleaned = _clean_text(value)
    if cleaned is None or len(cleaned) != 8 or not cleaned.isdigit():
        return None

    try:
        return date(
            int(cleaned[:4]),
            int(cleaned[4:6]),
            int(cleaned[6:8]),
        )
    except ValueError:
        return None


def _parse_application_period(value: object) -> tuple[date | None, date | None]:
    cleaned = _clean_text(value)
    if cleaned is None or "~" not in cleaned:
        return (None, None)

    start_text, separator, end_text = cleaned.partition("~")
    if not separator:
        return (None, None)

    start = _parse_compact_date(start_text)
    end = _parse_compact_date(end_text)
    if start is None or end is None:
        return (None, None)

    return (start, end)


def _parse_non_negative_int(value: object) -> int | None:
    cleaned = _clean_text(value)
    if cleaned is None or not cleaned.isdigit():
        return None

    parsed = int(cleaned)
    if parsed < 0:
        return None

    return parsed


def determine_application_status(
    period_code: str | None,
    application_start: date | None,
    application_end: date | None,
    reference_date: date,
) -> ApplicationStatus:
    if period_code == "0057003":
        return ApplicationStatus.CLOSED
    if period_code == "0057002":
        return ApplicationStatus.OPEN

    if application_start is not None and application_end is not None:
        if reference_date < application_start:
            return ApplicationStatus.UPCOMING
        if reference_date <= application_end:
            return ApplicationStatus.OPEN
        return ApplicationStatus.CLOSED

    return ApplicationStatus.UNKNOWN


def parse_policy_item(
    item: dict[str, object],
    *,
    verified_at: datetime,
    reference_date: date,
) -> PolicyRecord:
    category = _join_non_blank(
        [
            _clean_text(item.get("lclsfNm")),
            _clean_text(item.get("mclsfNm")),
        ],
        " > ",
    )
    application_start, application_end = _parse_application_period(item.get("aplyYmd"))
    employment_status = decode_code("jobCd", _clean_text(item.get("jobCd")))
    education_status = decode_code("schoolCd", _clean_text(item.get("schoolCd")))
    income_condition = _build_income_condition(item)
    eligibility_text = _build_eligibility_text(item)
    benefit_text = _clean_text(item.get("plcySprtCn"))
    application_method = _clean_text(item.get("plcyAplyMthdCn"))
    required_documents = _clean_text(item.get("sbmsnDcmntCn"))
    policy_name = _clean_text(item.get("plcyNm")) or ""

    return PolicyRecord(
        policy_id=_clean_text(item.get("plcyNo")) or "",
        policy_name=policy_name,
        category=category,
        summary=_clean_text(item.get("plcyExplnCn")),
        region_code=_clean_text(item.get("zipCd")),
        region_name=None,
        age_min=_parse_non_negative_int(item.get("sprtTrgtMinAge")),
        age_max=_parse_non_negative_int(item.get("sprtTrgtMaxAge")),
        income_condition=income_condition,
        employment_status=employment_status,
        education_status=education_status,
        application_start=application_start,
        application_end=application_end,
        application_status=determine_application_status(
            _clean_text(item.get("aplyPrdSeCd")),
            application_start,
            application_end,
            reference_date,
        ),
        eligibility_text=eligibility_text,
        benefit_text=benefit_text,
        application_method=application_method,
        required_documents=required_documents,
        contact=_build_contact(item),
        source_name="온통청년",
        source_url=_first_clean_text(
            item.get("refUrlAddr1"),
            item.get("refUrlAddr2"),
            item.get("aplyUrlAddr"),
        ),
        last_verified_at=verified_at,
        embedding_text=_build_embedding_text(
            policy_name=policy_name,
            category=category,
            summary=_clean_text(item.get("plcyExplnCn")),
            benefit_text=benefit_text,
            eligibility_text=eligibility_text,
            application_method=application_method,
            required_documents=required_documents,
            income_condition=income_condition,
            employment_status=employment_status,
            education_status=education_status,
            major=decode_code("plcyMajorCd", _clean_text(item.get("plcyMajorCd"))),
            special_business=decode_code("sbizCd", _clean_text(item.get("sbizCd"))),
        ),
    )


def parse_policy_page(
    payload: dict[str, object],
    *,
    verified_at: datetime,
    reference_date: date,
) -> list[PolicyRecord]:
    if payload.get("resultCode") != 200:
        raise ValueError("resultCode must be 200.")

    result = payload.get("result")
    if not isinstance(result, dict):
        raise ValueError("result must be a dictionary.")

    items = result.get("youthPolicyList")
    if not isinstance(items, list):
        raise ValueError("result.youthPolicyList must be a list.")

    records = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("youthPolicyList items must be dictionaries.")
        records.append(
            parse_policy_item(
                item,
                verified_at=verified_at,
                reference_date=reference_date,
            )
        )

    return records


def _build_income_condition(item: dict[str, object]) -> str | None:
    parts: list[str] = []
    decoded = decode_code("earnCndSeCd", _clean_text(item.get("earnCndSeCd")))
    if decoded is not None:
        parts.append(decoded)

    min_amount = _clean_text(item.get("earnMinAmt"))
    if min_amount is not None and min_amount != "0":
        parts.append(f"최소 {min_amount}")

    max_amount = _clean_text(item.get("earnMaxAmt"))
    if max_amount is not None and max_amount != "0":
        parts.append(f"최대 {max_amount}")

    extra = _clean_text(item.get("earnEtcCn"))
    if extra is not None:
        parts.append(extra)

    return _join_non_blank(parts, " / ")


def _build_eligibility_text(item: dict[str, object]) -> str | None:
    parts: list[str] = []
    additional_condition = _clean_text(item.get("addAplyQlfcCndCn"))
    if additional_condition is not None:
        parts.append(f"추가 신청 자격: {additional_condition}")

    restricted_target = _clean_text(item.get("ptcpPrpTrgtCn"))
    if restricted_target is not None:
        parts.append(f"참여 제한 대상: {restricted_target}")

    return _join_non_blank(parts, "\n\n")


def _build_contact(item: dict[str, object]) -> str | None:
    return _join_non_blank(
        [
            _clean_text(item.get("sprvsnInstCdNm")),
            _clean_text(item.get("sprvsnInstPicNm")),
        ],
        " / ",
    )


def _build_embedding_text(
    *,
    policy_name: str | None,
    category: str | None,
    summary: str | None,
    benefit_text: str | None,
    eligibility_text: str | None,
    application_method: str | None,
    required_documents: str | None,
    income_condition: str | None,
    employment_status: str | None,
    education_status: str | None,
    major: str | None,
    special_business: str | None,
) -> str:
    return _join_non_blank(
        [
            policy_name,
            category,
            summary,
            benefit_text,
            eligibility_text,
            application_method,
            required_documents,
            income_condition,
            employment_status,
            education_status,
            major,
            special_business,
        ],
        "\n",
    ) or ""


def _first_clean_text(*values: object) -> str | None:
    for value in values:
        cleaned = _clean_text(value)
        if cleaned is not None:
            return cleaned
    return None


def _join_non_blank(parts: list[str | None], separator: str) -> str | None:
    cleaned_parts = [part for part in parts if part is not None]
    if not cleaned_parts:
        return None

    return separator.join(cleaned_parts)
