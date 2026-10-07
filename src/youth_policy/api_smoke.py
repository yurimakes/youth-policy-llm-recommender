"""실행 중인 로컬 Intake API를 합성 답변으로 점검합니다. 상태를 저장하지 않습니다."""

from __future__ import annotations

from dataclasses import dataclass
import ipaddress
import json
import math
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


class SmokeError(RuntimeError):
    """응답 원문이나 진행 상태를 노출하지 않는 점검 오류입니다."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str,
                         headers: Any, newurl: str) -> None:
        return None


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    message: str


class LocalApiClient:
    """loopback HTTP 서버에만 합성 입력을 보내며 프록시·리다이렉트를 사용하지 않습니다."""

    def __init__(self, base_url: str, *, timeout: float = 5.0) -> None:
        parsed = urlsplit(base_url)
        host = parsed.hostname
        try:
            loopback = host == "localhost" or (host is not None and ipaddress.ip_address(host).is_loopback)
            parsed.port
        except ValueError:
            loopback = False
        if (not loopback or parsed.scheme != "http" or parsed.username is not None
                or parsed.password is not None or parsed.path not in {"", "/"}
                or parsed.query or parsed.fragment):
            raise ValueError("base URL must be an http loopback origin")
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be finite and positive")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.opener = build_opener(ProxyHandler({}), _NoRedirect())

    def request(self, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """JSON 응답·HTTP 성공·no-store를 확인하고 오류 원문은 출력하지 않습니다."""
        if path not in {"/health", "/ready", "/openapi.json", "/api/v1/intake/start",
                        "/api/v1/intake/transition"}:
            raise SmokeError("unsupported check endpoint")
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = Request(self.base_url + path, data=data,
                          headers={"Content-Type": "application/json"} if data is not None else {})
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                _require(response.status == 200, f"{path}: expected HTTP 200")
                _require(response.headers.get("Cache-Control") == "no-store",
                         f"{path}: missing no-store header")
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise SmokeError(f"{path}: HTTP {exc.code}; check server and policy data") from None
        except (URLError, OSError, UnicodeError, ValueError) as exc:
            raise SmokeError(f"{path}: connection or JSON response failed") from None
        _require(isinstance(payload, dict), f"{path}: expected JSON object")
        return payload

    def transition(self, response: dict[str, Any], action: dict[str, Any]) -> dict[str, Any]:
        """직전 응답의 상태 전체를 다음 POST에 전달합니다."""
        return self.request("/api/v1/intake/transition", {"state": response["state"], "action": action})


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeError(message)


def _skip_questions(client: LocalApiClient, response: dict[str, Any]) -> dict[str, Any]:
    seen = set()
    for _ in range(8):
        question = response["next_question"]
        if question is None:
            return response
        key = question["key"]
        _require(key not in seen, "a skipped question was repeated")
        seen.add(key)
        _require(question["allow_skip"] is True, "question does not permit skipping")
        _require(key in {"age", "region_code", "employment_status"}, "unexpected fact question")
        response = client.transition(response, {"type": "answer_fact", "key": key, "value": None})
        _require(key in response["state"]["skipped"], "skip history was not retained")
    raise SmokeError("question flow did not terminate")


def _check_candidates(response: dict[str, Any]) -> None:
    _require(response["data_status"] == "ready", "policy data was not loaded")
    _require(bool(response["notice"]), "qualification notice is missing")
    for candidate in response["candidates"]:
        _require(candidate["status"] != "not_met", "excluded policy remained a candidate")
        _require(bool(candidate["checks"]) and bool(candidate["next_actions"]), "guidance is missing")
        _require(bool(candidate["source_name"]) and bool(candidate["last_verified_at"]), "source metadata is missing")
        _require("source_url" in candidate, "source URL field is missing")


def _find_detail_candidate(client: LocalApiClient) -> dict[str, Any] | None:
    """건너뛰기 경로와 별개의 새 진행에서 상세 질문이 필요한 실제 후보를 찾습니다."""
    response = client.request("/api/v1/intake/start", {"start_mode": "goal"})
    response = client.transition(response, {"type": "choose_card", "key": "goal", "value": "unknown"})
    response = client.transition(response, {"type": "show_results"})
    _check_candidates(response)
    for candidate in response["candidates"]:
        selected = client.transition(response, {"type": "select_policy", "policy_id": candidate["policy_id"]})
        if selected["detail_offer_available"]:
            return selected
    return None


def run_smoke(client: LocalApiClient) -> tuple[CheckResult, ...]:
    """서버 점검 결과를 반환하며 데이터 의존 항목의 스킵을 성공과 구분합니다."""
    checks: list[CheckResult] = []
    current = "server_and_data"
    try:
        health = client.request("/health")
        _require(health.get("status") == "ok" and health.get("api_version") == "1", "health/version mismatch")
        ready = client.request("/ready")
        _require(ready.get("status") == "ready" and type(ready.get("policy_count")) is int
                 and ready["policy_count"] > 0, "policy database is empty")
        schema = client.request("/openapi.json")
        _require(all(path in schema.get("paths", {}) for path in
                     ("/health", "/ready", "/api/v1/intake/start", "/api/v1/intake/transition")),
                 "runtime OpenAPI endpoints are missing")
        checks.append(CheckResult(current, "PASS", f"policies={ready['policy_count']}; runtime OpenAPI available"))

        current = "situation_and_skip"
        result = client.request("/api/v1/intake/start", {})
        result = client.transition(result, {"type": "choose_card", "key": "situation", "value": "resting"})
        result = client.transition(result, {"type": "choose_card", "key": "interest", "value": "living_cost"})
        _require(all(v is None for v in result["state"]["profile"].values()), "cards inferred profile facts")
        result = _skip_questions(client, result)
        result = client.transition(result, {"type": "show_results"})
        _require(result["state"]["stage"] == "results", "results stage was not reached")
        _check_candidates(result)
        checks.append(CheckResult(current, "PASS", f"candidates={len(result['candidates'])}; unknown facts retained"))
        if any(not c["source_url"] for c in result["candidates"]):
            checks.append(CheckResult("source_urls", "WARN", "some candidates need an official notice URL"))

        current = "goal_and_correction"
        goal = client.request("/api/v1/intake/start", {"start_mode": "goal"})
        goal = client.transition(goal, {"type": "choose_card", "key": "goal", "value": "housing"})
        goal = client.transition(goal, {"type": "answer_fact", "key": "age", "value": 24})
        _require(goal["state"]["profile"]["age"] == 24, "synthetic answer was not retained")
        goal = client.transition(goal, {"type": "answer_fact", "key": "age", "value": None})
        _require(goal["state"]["profile"]["age"] is None and "age" not in goal["state"]["answered"],
                 "answer correction did not clear the previous fact")
        goal = client.transition(_skip_questions(client, goal), {"type": "show_results"})
        _check_candidates(goal)
        checks.append(CheckResult(current, "PASS", "goal route and answer-to-unknown correction completed"))

        current = "detail_decline"
        if result["candidates"]:
            policy_id = result["candidates"][0]["policy_id"]
            selected = client.transition(result, {"type": "select_policy", "policy_id": policy_id})
            declined = client.transition(selected, {"type": "choose_detail", "accept": False})
            _require(declined["state"]["stage"] == "results" and declined["state"]["detail_choice"] is False,
                     "declining detail did not retain the basic route")
            _require(declined["candidates"] == selected["candidates"], "declining detail changed official guidance")
            checks.append(CheckResult(current, "PASS", "basic route and official guidance retained"))
            current = "detail_pause_resume"
            # A prior explicit skip must stay respected. Use a separate unanswered
            # synthetic route rather than erasing skips or forcing a detail step.
            detail_candidate = _find_detail_candidate(client)
            if detail_candidate is not None:
                detail = client.transition(detail_candidate, {"type": "choose_detail", "accept": True})
                _require(detail["state"]["stage"] == "detail", "accepted detail did not start")
                paused = client.transition(detail, {"type": "pause_detail"})
                resumed = client.transition(paused, {"type": "resume_detail"})
                _require(paused["state"]["detail_paused"] and resumed["state"]["stage"] == "detail",
                         "detail pause/resume failed")
                _require(resumed["state"]["profile"] == detail["state"]["profile"], "resume lost profile answers")
                _check_candidates(resumed)
                checks.append(CheckResult(current, "PASS", "accepted detail paused and resumed"))
            else:
                checks.append(CheckResult(current, "SKIP", "no candidate needs detail in a fresh unanswered route"))
        else:
            checks.extend(CheckResult(name, "SKIP", "no current candidate; review policy dates and data")
                          for name in ("detail_decline", "detail_pause_resume"))

        current = "preparation_stage"
        prepared = client.transition(result, {"type": "prepare"})
        _require(prepared["state"]["stage"] == "preparation", "preparation stage was not reached")
        _check_candidates(prepared)
        checks.append(CheckResult(current, "PASS", "stage transition only; no document generation"))
    except SmokeError as exc:
        checks.append(CheckResult(current, "FAIL", str(exc)))
    except (KeyError, TypeError, IndexError):
        checks.append(CheckResult(current, "FAIL", "response does not match the intake contract"))
    return tuple(checks)
