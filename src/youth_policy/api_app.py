"""api_app.py

진행 상태·정책 조건 로직을 UI 데모와 연결하는 stateless FastAPI를 제공합니다.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from youth_policy.api_config import ApiSettings, korea_today, load_api_settings
from youth_policy.api_schemas import IntakeResponse, StartRequest, TransitionRequest
from youth_policy.intake import Stage, start_intake
from youth_policy.intake_contract import (
    PayloadError, TransitionConflict, apply_action, response_payload, state_from_payload,
)
from youth_policy.models import PolicyRecord
from youth_policy.policy_repository import PolicyDataUnavailable, load_policies_readonly


def create_app(
    *, settings: ApiSettings | None = None,
    policy_provider: Callable[[], tuple[PolicyRecord, ...]] | None = None,
    date_provider: Callable[[], date] = korea_today,
) -> FastAPI:
    """개발 서버를 만들며 사용자 상태를 서버에 저장하지 않습니다."""
    config = settings or load_api_settings()
    provider = policy_provider or (lambda: load_policies_readonly(config.policy_db_path))
    app = FastAPI(title="청년정책 AI 에이전트 — Intake API", version="0.2.0")
    demo_directory = Path(__file__).resolve().parents[2] / "demo"
    demo_assets = {"style.css": "text/css", "app.mjs": "text/javascript",
                   "client.mjs": "text/javascript"}

    @app.get("/demo/assets/{asset_name}", include_in_schema=False)
    def demo_asset(asset_name: str) -> FileResponse:
        """허용한 파일만 OS의 MIME 추측 없이 올바른 타입으로 제공합니다."""
        if asset_name not in demo_assets:
            raise HTTPException(status_code=404, detail="Not Found")
        return FileResponse(demo_directory / asset_name, media_type=demo_assets[asset_name])

    @app.get("/demo", include_in_schema=False)
    @app.get("/demo/", include_in_schema=False)
    def demo() -> FileResponse:
        """같은 origin의 API를 사용하는 제출용 데모 화면을 반환합니다."""
        return FileResponse(demo_directory / "index.html", media_type="text/html")

    app.add_middleware(
        CORSMiddleware, allow_origins=list(config.cors_origins), allow_credentials=False,
        allow_methods=["GET", "POST"], allow_headers=["Content-Type"],
    )

    @app.middleware("http")
    async def disable_caching(request: Request, call_next: Any) -> Any:
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Do not echo raw submitted values in validation errors.
        return _error(422, "invalid_payload", "입력 필드와 값의 형식을 확인해 주세요.")

    @app.exception_handler(PayloadError)
    async def invalid_payload(request: Request, exc: PayloadError) -> JSONResponse:
        return _error(422, "invalid_state_or_answer", "진행 상태와 답변 형식을 확인해 주세요.")

    @app.exception_handler(TransitionConflict)
    async def invalid_transition(request: Request, exc: TransitionConflict) -> JSONResponse:
        return _error(409, "transition_conflict", "현재 단계나 정책 후보에서 할 수 없는 동작입니다.")

    @app.exception_handler(PolicyDataUnavailable)
    async def unavailable_data(request: Request, exc: PolicyDataUnavailable) -> JSONResponse:
        return _error(503, "policy_data_unavailable", "정책 데이터가 준비되지 않았습니다.")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "api_version": "1"}

    @app.get("/ready")
    def ready() -> Any:
        records = provider()
        if not records:
            return _error(503, "policy_data_empty", "정책 데이터가 비어 있습니다.")
        return {"status": "ready", "policy_count": len(records)}

    @app.post("/api/v1/intake/start", response_model=IntakeResponse)
    def start(body: StartRequest) -> dict[str, Any]:
        return response_payload(start_intake(body.start_mode), (), reference_date=date_provider(),
                                data_status="not_loaded")

    @app.post("/api/v1/intake/transition", response_model=IntakeResponse)
    def transition(body: TransitionRequest) -> dict[str, Any]:
        state = state_from_payload(body.state.model_dump(mode="json"))
        action = body.action.model_dump(mode="json")
        today = date_provider()
        if action["type"] == "choose_card":
            updated = apply_action(state, action, (), reference_date=today)
            records = () if updated.stage in {Stage.START, Stage.INTEREST} else provider()
        else:
            records = provider()
            updated = apply_action(state, action, records, reference_date=today)
        # Validate emitted state too, so UI clients can send it back unchanged.
        payload = response_payload(updated, records, reference_date=today,
                                   data_status="not_loaded" if updated.stage in {Stage.START, Stage.INTEREST}
                                   else ("ready" if records else "empty"))
        state_from_payload(payload["state"])
        return payload

    return app


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})
