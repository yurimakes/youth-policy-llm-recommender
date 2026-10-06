"""app.py

Streamlit 진입점과 정책 추천 UI 화면을 구성합니다.
"""

from __future__ import annotations

import html
import inspect
import os
import sys
from base64 import b64encode
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Callable

import streamlit as st

SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from youth_policy import codebook, llm_service, retrieval, ui_service


ASSET_DIR = Path("assets")
BANNER_IMAGE = ASSET_DIR / "banner.png"
LOGO_IMAGE = ASSET_DIR / "logo.png"
MASCOT_IMAGE = ASSET_DIR / "mascot.png"
CHAT_MASCOT_IMAGE = ASSET_DIR / "chat_mascot.png"


def apply_page_style() -> None:
    """밝은 흰색·파란색 데모 스타일을 적용합니다."""
    st.set_page_config(
        page_title="청년 맞춤 정책 추천",
        page_icon=str(LOGO_IMAGE),
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(
        """
        <style>
        :root {
            --career-blue: #2563eb;
            --career-blue-dark: #1d4ed8;
            --career-blue-soft: #eaf2ff;
            --career-border: #dbeafe;
            --career-text: #172554;
            --career-muted: #64748b;
            --career-bg: #f6f9ff;
        }

        .stApp {
            background: var(--career-bg);
            color: var(--career-text);
        }

        [data-testid="stSidebar"] {
            display: none;
        }

        .block-container {
            max-width: 1120px;
            padding-top: 1.2rem;
            padding-bottom: 3rem;
        }

        .topbar {
            display: flex;
            align-items: center;
            gap: 14px;
            padding: 10px 2px 16px;
        }

        .topbar img {
            width: 44px;
            height: 44px;
            object-fit: contain;
        }

        .service-title {
            margin: 0;
            color: #0f2f78;
            font-size: 1.55rem;
            font-weight: 800;
            letter-spacing: 0;
        }

        .hero-copy {
            margin: 12px 0 0;
            color: #33507f;
            font-size: 1rem;
            line-height: 1.65;
        }

        .input-card,
        .notice-card,
        .policy-card,
        .summary-panel,
        .ai-card {
            background: #ffffff;
            border: 1px solid var(--career-border);
            border-radius: 8px;
            box-shadow: 0 10px 28px rgba(37, 99, 235, 0.08);
        }

        .input-card {
            padding: 24px 26px 18px;
            margin: 22px 0 18px;
        }

        .section-title {
            margin: 0 0 6px;
            color: #0f2f78;
            font-size: 1.22rem;
            font-weight: 800;
        }

        .section-subtitle {
            margin: 0 0 18px;
            color: var(--career-muted);
            font-size: 0.95rem;
        }

        div.stButton > button:first-child {
            width: 100%;
            min-height: 48px;
            border: 0;
            border-radius: 8px;
            background: var(--career-blue);
            color: #ffffff;
            font-weight: 800;
            font-size: 1rem;
            box-shadow: 0 10px 18px rgba(37, 99, 235, 0.24);
        }

        div.stButton > button:first-child:hover {
            background: var(--career-blue-dark);
            color: #ffffff;
            border: 0;
        }

        .notice-card {
            margin-top: 18px;
            padding: 16px 18px;
            color: #1e3a8a;
            background: #eef6ff;
            font-weight: 700;
        }

        .summary-panel {
            display: flex;
            align-items: center;
            gap: 20px;
            padding: 18px;
            margin: 24px 0 16px;
        }

        .summary-panel img {
            width: 96px;
            max-width: 22vw;
            object-fit: contain;
        }

        .summary-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
            flex: 1;
        }

        .status-card {
            min-height: 92px;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid var(--career-border);
            background: #f8fbff;
        }

        .status-label {
            color: var(--career-muted);
            font-size: 0.78rem;
            font-weight: 800;
        }

        .status-count {
            margin-top: 6px;
            color: var(--career-blue);
            font-size: 2rem;
            font-weight: 900;
            line-height: 1;
        }

        .status-help {
            margin-top: 8px;
            color: #557096;
            font-size: 0.82rem;
        }

        .policy-card {
            padding: 20px 22px;
            margin: 14px 0;
        }

        .policy-status {
            display: inline-flex;
            align-items: center;
            height: 28px;
            padding: 0 10px;
            border-radius: 999px;
            background: var(--career-blue-soft);
            color: var(--career-blue-dark);
            font-size: 0.78rem;
            font-weight: 900;
        }

        .policy-title {
            margin: 12px 0 8px;
            color: #102a65;
            font-size: 1.12rem;
            font-weight: 900;
        }

        .policy-meta {
            margin: 8px 0;
            color: #334155;
            line-height: 1.65;
        }

        .reason-list {
            margin: 8px 0 0 18px;
            color: #475569;
            line-height: 1.55;
        }

        .source-link a {
            color: var(--career-blue-dark);
            font-weight: 800;
            text-decoration: none;
        }

        .ai-card {
            display: flex;
            align-items: center;
            gap: 14px;
            padding: 16px 18px;
            margin: 18px 0;
            background: #ffffff;
        }

        .ai-card img {
            width: 54px;
            height: 54px;
            object-fit: contain;
        }

        .ai-title {
            margin: 0 0 4px;
            color: #0f2f78;
            font-weight: 900;
        }

        .ai-copy {
            margin: 0;
            color: var(--career-muted);
            line-height: 1.55;
        }

        @media (max-width: 760px) {
            .summary-panel {
                align-items: flex-start;
                flex-direction: column;
            }

            .summary-grid {
                width: 100%;
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def object_to_dict(value: Any) -> dict[str, Any]:
    """dataclass, dict, 일반 객체를 화면 표시용 dict로 변환합니다."""
    if value is None:
        return {}
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return value
    return {
        name: getattr(value, name)
        for name in dir(value)
        if not name.startswith("_") and not callable(getattr(value, name))
    }


def first_value(source: dict[str, Any], *keys: str, default: Any = "") -> Any:
    """여러 후보 키 중 첫 번째 유효 값을 반환합니다."""
    for key in keys:
        value = source.get(key)
        if value not in (None, ""):
            return value
    return default


def split_region_values(value: Any) -> list[str]:
    """쉼표로 연결된 지역 이름 또는 코드를 순서대로 분리합니다."""
    if value in (None, ""):
        return []
    return [item.strip() for item in str(value).split(",") if item.strip()]


def split_full_region_name(region_name: str) -> tuple[str, str]:
    """전체 지역명을 시·도와 시·군·구 표시명으로 분리합니다."""
    parts = region_name.split()
    if len(parts) < 2:
        return region_name, region_name
    return parts[0], " ".join(parts[1:])


def build_region_options(policies: Any) -> dict[str, dict[str, str]]:
    """정책 데이터의 region_code와 코드북으로 2단계 지역 선택 목록을 만듭니다."""
    region_options: dict[str, dict[str, str]] = {}
    code_to_name = getattr(codebook, "REGION_CODE_TO_NAME", {})

    for policy in policies or []:
        policy_dict = object_to_dict(policy)
        codes = split_region_values(first_value(policy_dict, "region_code", default=""))

        for code in codes:
            region_name = code_to_name.get(code)
            if not region_name:
                continue
            sido_name, district_name = split_full_region_name(region_name)
            region_options.setdefault(sido_name, {})
            region_options[sido_name].setdefault(district_name, code)

    if not region_options:
        return {"지역 정보 없음": {"지역 정보 없음": ""}}

    return {
        sido_name: dict(sorted(districts.items()))
        for sido_name, districts in sorted(region_options.items())
    }


def image_data_uri(path: Path) -> str:
    """로컬 이미지 파일을 HTML 표시용 data URI로 변환합니다."""
    suffix = path.suffix.lower().lstrip(".") or "png"
    mime = "jpeg" if suffix in {"jpg", "jpeg"} else suffix
    encoded = b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/{mime};base64,{encoded}"


def call_with_supported_args(func: Callable[..., Any], **kwargs: Any) -> Any:
    """함수 시그니처에 맞는 인자만 전달해 기존 서비스 함수를 호출합니다."""
    signature = inspect.signature(func)
    params = signature.parameters
    if any(param.kind == inspect.Parameter.VAR_KEYWORD for param in params.values()):
        return func(**kwargs)
    supported = {key: value for key, value in kwargs.items() if key in params}
    return func(**supported)


def load_policies_from_existing_service() -> Any:
    """ui_service의 기존 SQLite 로딩 함수를 찾아 호출합니다."""
    loader_names = (
        "load_policies",
        "load_policy_records",
        "load_policies_from_sqlite",
        "load_policies_from_db",
        "load_sqlite_policies",
        "get_policies",
    )
    sqlite_paths = (
        Path("data/processed/policies.sqlite3"),
        Path("data/processed/policies.db"),
        Path("data/policies.sqlite3"),
        Path("data/policies.db"),
    )
    for name in loader_names:
        loader = getattr(ui_service, name, None)
        if loader is None:
            continue

        signature = inspect.signature(loader)
        required_params = [
            param
            for param in signature.parameters.values()
            if param.default is inspect.Parameter.empty
            and param.kind
            in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        ]
        if not required_params:
            return loader()

        if len(required_params) == 1:
            for sqlite_path in sqlite_paths:
                if sqlite_path.exists():
                    return loader(sqlite_path)
            return loader(sqlite_paths[0])

    raise RuntimeError("ui_service에서 기존 SQLite 정책 로딩 함수를 찾을 수 없습니다.")


def build_user_profile(age: int, region_code: str, employment_status: str) -> Any:
    """기존 평가 함수가 받을 사용자 조건 객체 또는 dict를 구성합니다."""
    profile_data = {
        "age": age,
        "region_code": region_code.strip(),
        "employment_status": employment_status.strip(),
    }
    for class_name in ("UserProfile", "PolicyUserProfile", "RecommendationInput", "PolicyQuery"):
        profile_class = getattr(ui_service, class_name, None)
        if profile_class is None:
            continue
        try:
            return call_with_supported_args(profile_class, **profile_data)
        except TypeError:
            continue
    return profile_data


def evaluate_existing_policies(policies: Any, profile: Any) -> list[Any]:
    """기존 evaluate_policies() 호출은 유지하되 시그니처 차이를 흡수합니다."""
    evaluator = getattr(ui_service, "evaluate_policies")
    profile_dict = object_to_dict(profile)
    signature = inspect.signature(evaluator)
    names = set(signature.parameters)

    if {"policies", "profile"}.issubset(names):
        result = evaluator(policies=policies, profile=profile)
    elif {"policies", "user_profile"}.issubset(names):
        result = evaluator(policies=policies, user_profile=profile)
    elif {"policy_records", "profile"}.issubset(names):
        result = evaluator(policy_records=policies, profile=profile)
    elif {"age", "region_code", "employment_status"}.issubset(names):
        result = call_with_supported_args(
            evaluator,
            policies=policies,
            policy_records=policies,
            age=profile_dict.get("age"),
            region_code=profile_dict.get("region_code"),
            employment_status=profile_dict.get("employment_status"),
        )
    else:
        result = evaluator(policies, profile)

    if result is None:
        return []
    if all(hasattr(result, name) for name in ("matched", "unknown", "no_match")):
        return [
            *list(getattr(result, "matched") or []),
            *list(getattr(result, "unknown") or []),
            *list(getattr(result, "no_match") or []),
        ]
    if isinstance(result, list):
        return result
    if isinstance(result, tuple):
        return list(result)
    return [result]


def normalize_result(result: Any) -> dict[str, Any]:
    """평가 결과 객체를 정책 카드 표시용 구조로 정규화합니다."""
    result_dict = object_to_dict(result)
    policy = first_value(result_dict, "policy", "policy_record", "record", default={})
    evaluation = first_value(result_dict, "result", "evaluation", "match_result", default={})
    policy_dict = object_to_dict(policy)
    evaluation_dict = object_to_dict(evaluation)
    merged = {**policy_dict, **evaluation_dict, **result_dict}

    status = str(
        first_value(merged, "status", "result", "match_status", "decision", default="UNKNOWN")
    ).upper()
    if status not in {"MATCH", "UNKNOWN", "NO_MATCH"}:
        if "NO_MATCH" in status or "UNMATCH" in status:
            status = "NO_MATCH"
        elif "MATCH" in status:
            status = "MATCH"
        else:
            status = "UNKNOWN"

    reasons = first_value(
        merged,
        "reasons",
        "matched_reasons",
        "reason",
        "decision_reasons",
        "match_reasons",
        default=[],
    )
    if isinstance(reasons, str):
        reasons = [reasons]
    elif reasons is None:
        reasons = []
    else:
        reasons = [str(reason) for reason in reasons]

    return {
        "status": status,
        "raw_result": result,
        "policy_id": first_value(merged, "policy_id", "id", default=""),
        "policy_name": first_value(merged, "policy_name", "name", "title", default="정책명 미확인"),
        "category": first_value(merged, "category", default=""),
        "summary": first_value(merged, "summary", "description", "support_content", default="요약 정보가 없습니다."),
        "eligibility_text": first_value(merged, "eligibility_text", "eligibility", "condition_text", default=""),
        "benefit_text": first_value(merged, "benefit_text", "benefit", "support_detail", default=""),
        "application_start": first_value(merged, "application_start", "apply_start", default=""),
        "application_end": first_value(merged, "application_end", "apply_end", default=""),
        "application_method": first_value(merged, "application_method", "apply_method", default=""),
        "last_verified_at": first_value(merged, "last_verified_at", default=""),
        "embedding_text": first_value(merged, "embedding_text", default=""),
        "source_url": first_value(merged, "source_url", "url", "official_url", default=""),
        "reasons": reasons,
    }


def render_header() -> None:
    """상단 로고, 서비스명, 배너를 표시합니다."""
    logo_html = ""
    if LOGO_IMAGE.exists():
        logo_html = f'<img src="{image_data_uri(LOGO_IMAGE)}" alt="서비스 로고">'

    st.markdown(
        f'<div class="topbar">{logo_html}<h1 class="service-title">청년 맞춤 정책 추천</h1></div>',
        unsafe_allow_html=True,
    )
    if BANNER_IMAGE.exists():
        st.image(str(BANNER_IMAGE), use_container_width=True)
    st.markdown(
        '<p class="hero-copy">나이, 지역, 취업 상태를 기준으로 현재 저장된 공식 정책 데이터를 검토합니다.</p>',
        unsafe_allow_html=True,
    )


def render_input_card(region_options: dict[str, dict[str, str]]) -> tuple[int, str, str, str, bool]:
    """메인 화면 카드형 조건 입력 영역을 표시합니다."""
    with st.container(border=True):
        st.markdown("### 맞춤 조건 입력")
        st.caption("입력한 조건은 정책 필터링에만 사용되며, 최종 자격 판단은 공식 공고문 확인이 필요합니다.")
        col_age, col_region, col_employment = st.columns([1, 1, 1.2])
        with col_age:
            age = st.number_input("나이", min_value=0, max_value=120, value=24, step=1)
        with col_region:
            selected_sido = st.selectbox("시·도", list(region_options))
            districts = region_options.get(selected_sido, {"지역 정보 없음": ""})
            selected_district = st.selectbox("시·군·구", list(districts))
            region_code = districts.get(selected_district, "")
        with col_employment:
            employment_status = st.text_input("취업 상태", value="미취업자", placeholder="예: 미취업자")
        user_interest = st.text_area(
            "관심 정책 또는 필요한 지원",
            placeholder="예: 자격증 시험 비용과 월세 지원이 필요해요.",
            height=88,
        )
        submitted = st.button("맞춤 정책 추천받기", type="primary")
    return int(age), region_code, employment_status, user_interest, submitted


def render_notice() -> None:
    """정책 추천 안전 안내를 표시합니다."""
    st.markdown(
        """
        <div class="notice-card">
            지원 가능성이 높은 정책입니다. 최종 신청 자격과 세부 조건은 반드시 공식 공고문에서 확인해야 합니다.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_summary_cards(results: list[dict[str, Any]]) -> None:
    """MATCH / UNKNOWN / NO_MATCH 개수 요약을 표시합니다."""
    counts = {
        "MATCH": sum(1 for result in results if result["status"] == "MATCH"),
        "UNKNOWN": sum(1 for result in results if result["status"] == "UNKNOWN"),
        "NO_MATCH": sum(1 for result in results if result["status"] == "NO_MATCH"),
    }
    mascot_html = ""
    if MASCOT_IMAGE.exists():
        mascot_html = f'<img src="{image_data_uri(MASCOT_IMAGE)}" alt="결과 마스코트">'

    st.markdown(
        f"""
        <div class="summary-panel">
            {mascot_html}
            <div class="summary-grid">
                <div class="status-card">
                    <div class="status-label">MATCH</div>
                    <div class="status-count">{counts["MATCH"]}</div>
                    <div class="status-help">조건과 명확히 맞는 정책</div>
                </div>
                <div class="status-card">
                    <div class="status-label">UNKNOWN</div>
                    <div class="status-count">{counts["UNKNOWN"]}</div>
                    <div class="status-help">확인이 필요한 조건 포함</div>
                </div>
                <div class="status-card">
                    <div class="status-label">NO_MATCH</div>
                    <div class="status-count">{counts["NO_MATCH"]}</div>
                    <div class="status-help">조건과 명확히 다른 정책</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_ai_placeholder() -> None:
    """AI 설명 입력 전 안내를 표시합니다."""
    with st.container(border=True):
        image_col, text_col = st.columns([0.12, 0.88])
        with image_col:
            if CHAT_MASCOT_IMAGE.exists():
                st.image(str(CHAT_MASCOT_IMAGE), width=54)
        with text_col:
            st.markdown("**AI 추천 설명**")
            st.caption(
                "관심 정책 또는 필요한 지원을 입력하면 MATCH와 UNKNOWN 정책 중 관련도가 높은 Top-5를 검색해 설명합니다."
            )


def get_setting(name: str, default: str = "") -> str:
    """Streamlit secrets와 환경 변수에서 설정값을 읽습니다."""
    env_value = os.getenv(name, "")
    if env_value:
        return env_value

    value = ""
    try:
        value = str(st.secrets.get(name, "") or "")
    except Exception:
        value = ""
    return value or default


def create_openai_client() -> Any:
    """OpenAI 클라이언트를 생성합니다."""
    api_key = get_setting("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다.")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("OpenAI 패키지를 불러올 수 없습니다.") from exc

    return OpenAI(api_key=api_key)


def render_ai_explanation(
    *,
    ranked_policies: list[retrieval.RankedPolicy],
    explanation: str | None,
    error_message: str | None,
) -> None:
    """FAISS 검색 결과와 AI 설명을 표시합니다."""
    with st.container(border=True):
        image_col, text_col = st.columns([0.12, 0.88])
        with image_col:
            if CHAT_MASCOT_IMAGE.exists():
                st.image(str(CHAT_MASCOT_IMAGE), width=54)
        with text_col:
            st.markdown("**AI 추천 설명**")
            if error_message:
                st.warning("AI 설명 생성에 실패했습니다. 아래 Top-5 정책 결과는 유지됩니다.")
                st.caption(error_message)
            elif explanation:
                st.markdown(explanation)
            else:
                st.caption("관심사를 입력하면 MATCH와 UNKNOWN 정책 중 관련도가 높은 Top-5를 검색해 설명합니다.")

    if ranked_policies:
        st.markdown("### 관심사 기반 Top-5 정책")
        for ranked_policy in ranked_policies:
            render_policy_card(ranked_policy.policy)


def render_policy_card(result: dict[str, Any]) -> None:
    """정책 결과 카드를 표시합니다."""
    start = result["application_start"] or "미확인"
    end = result["application_end"] or "미확인"
    source_url = result["source_url"]
    reasons = result["reasons"] or ["판정 이유가 제공되지 않았습니다."]
    reason_items = "".join(f"<li>{html.escape(str(reason))}</li>" for reason in reasons)
    if source_url:
        escaped_url = html.escape(str(source_url), quote=True)
        source_html = f'<a href="{escaped_url}" target="_blank" rel="noopener noreferrer">공식 출처 확인</a>'
    else:
        source_html = "공식 출처 미확인"

    st.markdown(
        f"""
        <div class="policy-card">
            <span class="policy-status">{html.escape(result["status"])}</span>
            <h3 class="policy-title">{html.escape(str(result["policy_name"]))}</h3>
            <p class="policy-meta"><strong>요약</strong><br>{html.escape(str(result["summary"]))}</p>
            <p class="policy-meta"><strong>신청 기간</strong><br>{html.escape(str(start))} ~ {html.escape(str(end))}</p>
            <p class="policy-meta"><strong>판정 이유</strong></p>
            <ul class="reason-list">{reason_items}</ul>
            <p class="policy-meta source-link"><strong>공식 출처</strong><br>{source_html}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Streamlit 앱을 실행합니다."""
    apply_page_style()
    render_header()
    render_notice()

    try:
        policies = load_policies_from_existing_service()
    except Exception as exc:
        st.error(f"정책 데이터를 불러오는 중 오류가 발생했습니다: {exc}")
        render_ai_placeholder()
        return

    region_options = build_region_options(policies)
    age, region_code, employment_status, user_interest, submitted = render_input_card(region_options)

    if not submitted:
        render_ai_placeholder()
        return

    try:
        profile = build_user_profile(age, region_code, employment_status)
        evaluated_results = evaluate_existing_policies(policies, profile)
    except Exception as exc:
        st.error(f"정책 데이터를 불러오거나 평가하는 중 오류가 발생했습니다: {exc}")
        render_ai_placeholder()
        return

    normalized_results = [normalize_result(result) for result in evaluated_results]
    normalized_results.sort(
        key=lambda result: {"MATCH": 0, "UNKNOWN": 1, "NO_MATCH": 2}.get(result["status"], 3)
    )

    render_summary_cards(normalized_results)

    ranked_policies: list[retrieval.RankedPolicy] = []
    explanation: str | None = None
    ai_error: str | None = None
    if user_interest.strip():
        candidate_results = [
            result
            for result in normalized_results
            if result["status"] in {"MATCH", "UNKNOWN"}
        ]
        try:
            client = create_openai_client()
            embedding_model = get_setting("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
            chat_model = get_setting("OPENAI_CHAT_MODEL", "gpt-4o-mini")
            ranked_policies = retrieval.rank_policies(
                candidates=candidate_results,
                query=user_interest,
                client=client,
                embedding_model=embedding_model,
                top_k=5,
            )
            explanation = llm_service.generate_explanation(
                client=client,
                chat_model=chat_model,
                user_interest=user_interest,
                user_profile={
                    "age": age,
                    "region_code": region_code,
                    "employment_status": employment_status,
                },
                policies=[ranked_policy.policy for ranked_policy in ranked_policies],
            )
        except Exception as exc:
            ai_error = str(exc)

        render_ai_explanation(
            ranked_policies=ranked_policies,
            explanation=explanation,
            error_message=ai_error,
        )
    else:
        render_ai_placeholder()

    if not normalized_results:
        st.info("조건에 대해 표시할 정책 평가 결과가 없습니다.")
        return

    for result in normalized_results:
        render_policy_card(result)


if __name__ == "__main__":
    main()
