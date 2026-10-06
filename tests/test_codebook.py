"""test_codebook.py

온통청년 API 코드북 조회와 변환 동작을 테스트합니다.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from youth_policy.codebook import CODEBOOKS, decode_code, get_codebook


def test_decode_job_code():
    assert decode_code("jobCd", "0013003") == "미취업자"


def test_decode_school_code():
    assert decode_code("schoolCd", "0049005") == "대학 재학"


def test_decode_earn_condition_code():
    assert decode_code("earnCndSeCd", "0043001") == "무관"


def test_decode_special_business_code():
    assert decode_code("sbizCd", "0014008") == "지역인재"


def test_decode_special_business_code_alias():
    assert decode_code("sBizCd", "0014008") == "지역인재"


def test_decode_strips_whitespace():
    assert decode_code(" jobCd ", " 0013003 ") == "미취업자"


def test_decode_none_and_empty_code_return_none():
    assert decode_code("jobCd", None) is None
    assert decode_code("jobCd", "") is None
    assert decode_code("jobCd", "   ") is None


def test_decode_unknown_field_and_code_return_none():
    assert decode_code("unknownField", "0013003") is None
    assert decode_code("jobCd", "9999999") is None


def test_get_codebook_returns_copy():
    codebook = get_codebook("jobCd")
    codebook["0013003"] = "changed"

    assert CODEBOOKS["jobCd"]["0013003"] == "미취업자"
    assert get_codebook("jobCd")["0013003"] == "미취업자"


def test_exact_field_names_exist():
    assert "bizPrdSeCd" in CODEBOOKS
    assert "sbizCd" in CODEBOOKS


def test_incorrect_field_names_do_not_exist():
    assert "bizPrdSecd" not in CODEBOOKS
    assert "sBizCd" not in CODEBOOKS
