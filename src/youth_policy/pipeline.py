"""pipeline.py

저장된 온통청년 snapshot을 SQLite 저장소에 적재하는 파이프라인을 제공합니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
import json
from json import JSONDecodeError
from pathlib import Path

from youth_policy.models import PolicyRecord
from youth_policy.ontong_parser import parse_policy_page
from youth_policy.sqlite_store import (
    connect_database,
    count_policies,
    initialize_database,
    list_policies,
    upsert_policies,
)


class SnapshotPipelineError(ValueError):
    """Snapshot 적재 과정에서 복구 가능한 입력 오류가 발생했음을 나타냅니다."""


@dataclass(frozen=True)
class SnapshotLoadResult:
    snapshot_path: Path
    db_path: Path
    parsed_count: int
    stored_count: int
    parsed_policies: tuple[PolicyRecord, ...]
    stored_policies: tuple[PolicyRecord, ...]


def load_ontong_snapshot_to_sqlite(
    snapshot_path: str | Path,
    db_path: str | Path,
    *,
    verified_at: datetime | None = None,
    reference_date: date | None = None,
) -> SnapshotLoadResult:
    snapshot = Path(snapshot_path)
    database = Path(db_path)
    effective_verified_at = verified_at or _utc_now_naive()
    effective_reference_date = reference_date or effective_verified_at.date()

    payload = _read_snapshot_json(snapshot)
    parsed_policies = tuple(
        parse_policy_page(
            payload,
            verified_at=effective_verified_at,
            reference_date=effective_reference_date,
        )
    )
    if not parsed_policies:
        raise SnapshotPipelineError("Snapshot contains no policies.")

    database.parent.mkdir(parents=True, exist_ok=True)
    connection = connect_database(database)
    try:
        initialize_database(connection)
        upsert_policies(connection, parsed_policies)
        stored_count = count_policies(connection)
        stored_policies = tuple(list_policies(connection))
    finally:
        connection.close()

    if len(parsed_policies) != len(stored_policies):
        raise SnapshotPipelineError(
            "Stored policy count does not match parsed policy count."
        )
    if stored_count != len(stored_policies):
        raise SnapshotPipelineError(
            "SQLite policy count does not match reloaded policy count."
        )

    return SnapshotLoadResult(
        snapshot_path=snapshot,
        db_path=database,
        parsed_count=len(parsed_policies),
        stored_count=stored_count,
        parsed_policies=parsed_policies,
        stored_policies=stored_policies,
    )


def _read_snapshot_json(snapshot_path: Path) -> dict[str, object]:
    if not snapshot_path.exists():
        raise FileNotFoundError(f"Snapshot file not found: {snapshot_path}")

    try:
        payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except JSONDecodeError as exc:
        raise SnapshotPipelineError("Snapshot file is not valid JSON.") from exc

    if not isinstance(payload, dict):
        raise SnapshotPipelineError("Snapshot JSON root must be an object.")

    return payload


def _utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)
