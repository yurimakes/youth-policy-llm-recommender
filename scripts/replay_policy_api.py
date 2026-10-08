"""Replay the existing example snapshot through SQLite and the real API offline."""

from __future__ import annotations

import argparse
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import platform
import sys
import tempfile
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from youth_policy.data_audit import audit_database
from youth_policy.pipeline import load_ontong_snapshot_to_sqlite
from youth_policy.policy_repository import load_policies_readonly


REFERENCE_DATE = date(2026, 6, 28)
EXPIRED_DATE = date(2026, 10, 8)
POLICY_ID = "20260625005400113245"
FIXTURE = ROOT / "tests/fixtures/ontong_youth_policy_page1.json"


def _source_digest() -> str:
    digest = hashlib.sha256()
    paths = sorted((ROOT / "src/youth_policy").glob("*.py"))
    paths += [Path(__file__), ROOT / "scripts/audit_policy_data.py"]
    for path in paths:
        digest.update(path.relative_to(ROOT).as_posix().encode() + b"\0")
        digest.update(path.read_bytes() + b"\0")
    return digest.hexdigest()


def replay() -> dict[str, Any]:
    """Use a disposable DB and in-process HTTP requests; no model/network calls."""
    from fastapi.testclient import TestClient
    from youth_policy.api_app import create_app
    from youth_policy.api_config import ApiSettings

    checks = []

    def verify(name: str, condition: bool) -> None:
        if not condition:
            raise ValueError(f"Replay check failed: {name}")
        checks.append({"name": name, "passed": True})

    with tempfile.TemporaryDirectory(prefix="policy-replay-") as directory:
        database = Path(directory) / "example.sqlite3"
        loaded = load_ontong_snapshot_to_sqlite(
            FIXTURE, database, verified_at=datetime(2026, 6, 28),
            reference_date=REFERENCE_DATE,
        )
        verify("snapshot_to_sqlite_count", loaded.parsed_count == loaded.stored_count == 10)
        audit = audit_database(database, reference_date=REFERENCE_DATE, snapshot_paths=[FIXTURE])
        verify("normalized_raw_trace", audit["trace_counts"]["matched"] == 10)
        before = hashlib.sha256(database.read_bytes()).hexdigest()
        settings = ApiSettings(database, ())
        with TestClient(create_app(settings=settings, date_provider=lambda: REFERENCE_DATE)) as client:
            ready = client.get("/ready")
            verify("database_readiness", ready.status_code == 200 and ready.json()["policy_count"] == 10)
            payload = client.post("/api/v1/intake/start", json={}).json()

            def transition(action: dict[str, Any]) -> dict[str, Any]:
                nonlocal payload
                response = client.post("/api/v1/intake/transition",
                                       json={"state": payload["state"], "action": action})
                if response.status_code != 200:
                    raise ValueError("Replay transition failed.")
                payload = response.json()
                return payload

            transition({"type": "choose_card", "key": "situation", "value": "resting"})
            transition({"type": "choose_card", "key": "interest", "value": "living_cost"})
            verify("cards_do_not_infer_facts", all(value is None
                   for value in payload["state"]["profile"].values()))
            transition({"type": "answer_fact", "key": "age", "value": 24})
            transition({"type": "answer_fact", "key": "region_code", "value": "11680"})
            transition({"type": "show_results"})
            candidate = next(p for p in payload["candidates"] if p["policy_id"] == POLICY_ID)
            stored = next(p for p in load_policies_readonly(database) if p.policy_id == POLICY_ID)
            verify("candidate_source_preserved", candidate["source_url"] == stored.source_url
                   and candidate["policy_name"] == stored.policy_name)
            states = {c["field"]: c["status"] for c in candidate["checks"]}
            verify("explicit_age_and_region_compared", states["age"] == states["region_code"] == "confirmed")
            verify("unanswered_employment_stays_missing", states["employment_status"] == "input_missing")
            verify("unknown_eligibility_not_confirmed", states["eligibility"] == "check_required"
                   and candidate["status"] != "confirmed")
            transition({"type": "select_policy", "policy_id": POLICY_ID})
            transition({"type": "choose_detail", "accept": True})
            transition({"type": "pause_detail"})
            transition({"type": "resume_detail"})
            verify("detail_resume_reuses_answers", payload["state"]["profile"]["age"] == 24
                   and payload["next_question"]["key"] == "employment_status")
            transition({"type": "answer_fact", "key": "employment_status", "value": "미취업자"})
            transition({"type": "show_results"})
            transition({"type": "prepare"})
            verify("preparation_reached", payload["state"]["stage"] == "preparation")
            transition({"type": "answer_fact", "key": "age", "value": 120})
            verify("age_correction_excludes_candidate", POLICY_ID not in
                   {p["policy_id"] for p in payload["candidates"]})
            state = payload["state"]
        with TestClient(create_app(settings=settings, date_provider=lambda: EXPIRED_DATE)) as client:
            response = client.post("/api/v1/intake/transition", json={
                "state": state, "action": {"type": "answer_fact", "key": "age", "value": 24},
            })
            verify("expired_policy_excluded", response.status_code == 200 and POLICY_ID not in
                   {p["policy_id"] for p in response.json()["candidates"]})
        verify("api_and_audit_leave_db_unchanged", hashlib.sha256(database.read_bytes()).hexdigest() == before)
    return {
        "replay_version": "1", "data_kind": "existing_example_snapshot_not_live_data",
        "reference_date": REFERENCE_DATE.isoformat(), "expired_reference_date": EXPIRED_DATE.isoformat(),
        "python_version": platform.python_version(), "source_sha256": _source_digest(),
        "fixture_sha256": hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
        "policy_count": loaded.stored_count, "checks": checks, "data_audit": audit,
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Run offline reproduction and optionally write an evidence JSON report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.output and args.output.resolve().is_relative_to(ROOT / "tests"):
            raise ValueError("Output must not overwrite fixtures or tests.")
        report = replay()
        content = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(content, encoding="utf-8")
        else:
            print(content, end="")
        print(f"Offline replay passed: {len(report['checks'])} checks, "
              f"{report['policy_count']} example policies.", file=sys.stderr)
        return 0
    except ImportError:
        print("Install requirements-api.txt before running the replay.", file=sys.stderr)
        return 2
    except (OSError, ValueError, KeyError, StopIteration, TypeError):
        print("Offline replay failed; run the regression suite for details.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
