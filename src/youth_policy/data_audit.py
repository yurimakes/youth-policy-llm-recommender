"""Measure policy completeness and normalized snapshot traceability without writes."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, fields
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

from youth_policy.conditions import assess_conditions
from youth_policy.matching import UserProfile
from youth_policy.models import ApplicationStatus, PolicyRecord
from youth_policy.ontong_parser import parse_policy_page
from youth_policy.policy_repository import load_policies_readonly


AUDIT_VERSION = "1"
# These values depend on the ingest clock/date rather than the source row.
TRACE_FIELDS = tuple(f.name for f in fields(PolicyRecord)
                     if f.name not in {"application_status", "last_verified_at"})


def _json_value(value: object) -> object:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, ApplicationStatus):
        return value.value
    return value


def _digest(data: dict[str, object]) -> str:
    canonical = json.dumps(data, ensure_ascii=False, sort_keys=True,
                           separators=(",", ":"), default=_json_value)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _present(value: object) -> bool:
    return value is not None and (not isinstance(value, str) or bool(value.strip()))


def _usable_url(value: str | None) -> bool:
    if not value or any(char.isspace() for char in value):
        return False
    try:
        parsed = urlparse(value)
        parsed.port
        return bool(parsed.scheme in {"http", "https"} and parsed.hostname
                    and not parsed.username and not parsed.password)
    except ValueError:
        return False


def _trace_value(record: PolicyRecord) -> dict[str, object]:
    return {name: getattr(record, name) for name in TRACE_FIELDS}


def _snapshot_index(paths: Iterable[Path], reference_date: date) -> tuple[dict, list]:
    index: dict[str, list[dict[str, Any]]] = {}
    snapshots = []
    for number, path in enumerate(paths, 1):
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8-sig"))
        records = parse_policy_page(payload, verified_at=datetime(2000, 1, 1),
                                    reference_date=reference_date)
        snapshot_id = f"snapshot_{number}"
        digest = hashlib.sha256(raw).hexdigest()
        snapshots.append({"snapshot_id": snapshot_id, "sha256": digest,
                          "row_count": len(records)})
        for row_index, record in enumerate(records):
            index.setdefault(record.policy_id, []).append({
                "snapshot_id": snapshot_id, "snapshot_sha256": digest,
                "row_index": row_index, "normalized_sha256": _digest(_trace_value(record)),
            })
    return index, snapshots


def audit_records(
    records: Iterable[PolicyRecord], *, reference_date: date,
    snapshot_paths: Iterable[Path] = (),
) -> dict[str, Any]:
    """Return measured coverage, period states and per-row source comparisons.

    Presence is not correctness. Matching a parser output to a supplied raw row
    does not prove that an official notice is current or that use is permitted.
    """
    policies = tuple(sorted(records, key=lambda record: record.policy_id))
    ids = [record.policy_id for record in policies]
    if len(ids) != len(set(ids)):
        raise ValueError("Policy IDs must be unique for a policy-level denominator.")
    index, snapshots = _snapshot_index(snapshot_paths, reference_date)
    total = len(policies)
    coverage = {}
    for field in fields(PolicyRecord):
        present = sum(_present(getattr(record, field.name)) for record in policies)
        coverage[field.name] = {"present": present, "missing": total - present,
                                "ratio": present / total if total else None}
    rows = []
    periods: Counter[str] = Counter()
    categories: Counter[str] = Counter()
    regions: Counter[str] = Counter()
    trace_counts: Counter[str] = Counter()
    unusable_urls = 0
    verified_age_days = []
    condition_states: dict[str, Counter[str]] = {}
    for record in policies:
        valid_url = _usable_url(record.source_url)
        unusable_urls += not valid_url
        if record.application_status is ApplicationStatus.CLOSED or (
            record.application_end is not None and reference_date > record.application_end
        ):
            period = "closed"
        elif record.application_start is not None and reference_date < record.application_start:
            period = "not_started"
        elif record.application_start is not None and record.application_end is not None:
            period = "within_recorded_dates"
        else:
            period = "unverified"
        periods[period] += 1
        categories[(record.category or "").strip() or "unknown"] += 1
        # A policy may appear in multiple code buckets; bucket counts do not sum to total.
        codes = {part.strip() for part in (record.region_code or "").split(",") if part.strip()}
        regions.update(codes or {"unknown"})
        timestamp = record.last_verified_at
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        age_days = (reference_date - timestamp.astimezone(timezone(timedelta(hours=9))).date()).days
        verified_age_days.append(age_days)
        checks = assess_conditions(record, UserProfile(), reference_date=reference_date).checks
        for check in checks:
            condition_states.setdefault(check.field, Counter())[check.status.value] += 1
        digest = _digest(_trace_value(record))
        origins = index.get(record.policy_id, [])
        matches = [origin for origin in origins if origin["normalized_sha256"] == digest]
        trace = ("not_supplied" if not snapshots else "missing" if not origins
                 else "matched" if matches else "mismatch")
        trace_counts[trace] += 1
        rows.append({
            "policy_id": record.policy_id, "source_url": record.source_url,
            "source_url_usable": valid_url, "last_verified_at": record.last_verified_at.isoformat(),
            "processing_age_days": age_days, "period": period,
            "normalized_sha256": digest, "trace_status": trace,
            "source_rows": matches if matches else origins,
            "conditions_without_user_input": {check.field: check.status.value for check in checks},
        })
    blockers = []
    if not total:
        blockers.append("empty_catalogue")
    if unusable_urls:
        blockers.append("unusable_source_url")
    if not snapshots:
        blockers.append("snapshots_not_supplied")
    if trace_counts["missing"]:
        blockers.append("source_row_missing")
    if trace_counts["mismatch"]:
        blockers.append("source_row_mismatch")
    return {
        "audit_version": AUDIT_VERSION, "reference_date": reference_date.isoformat(),
        "policy_count": total, "field_coverage": coverage,
        "category_counts": dict(sorted(categories.items())),
        "region_code_policy_counts": dict(sorted(regions.items())),
        "period_counts": dict(sorted(periods.items())),
        "condition_counts_without_user_input": {
            field: dict(sorted(counts.items())) for field, counts in sorted(condition_states.items())
        },
        "processing_age_days": {
            "min": min(verified_age_days) if total else None,
            "max": max(verified_age_days) if total else None,
            "future_timestamp_count": sum(days < 0 for days in verified_age_days),
        },
        "trace_counts": {status: trace_counts[status] for status in
                         ("matched", "missing", "mismatch", "not_supplied")},
        "trace_compared_fields": list(TRACE_FIELDS), "snapshots": snapshots,
        "catalogue_sha256": _digest({record.policy_id: asdict(record) for record in policies}),
        "evidence_blockers": blockers, "policies": rows,
    }


def audit_database(
    database: Path, *, reference_date: date, snapshot_paths: Iterable[Path] = (),
) -> dict[str, Any]:
    """Read the existing SQLite only; never create or initialize a missing DB."""
    return audit_records(load_policies_readonly(database), reference_date=reference_date,
                         snapshot_paths=snapshot_paths)
