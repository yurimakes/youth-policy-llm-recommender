"""policy_repository.py

API가 기존 정책 SQLite를 파일 생성 없이 읽기 전용으로 조회하도록 합니다.
"""

from __future__ import annotations

from pathlib import Path
import sqlite3

from youth_policy.models import PolicyRecord
from youth_policy.sqlite_store import list_policies


class PolicyDataUnavailable(RuntimeError):
    """공식 정책 데이터가 아직 준비되지 않았거나 읽을 수 없습니다."""


def load_policies_readonly(database: Path) -> tuple[PolicyRecord, ...]:
    if not database.is_file():
        raise PolicyDataUnavailable("정책 데이터를 먼저 준비해야 합니다.")
    try:
        connection = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        try:
            return tuple(list_policies(connection))
        finally:
            connection.close()
    except (OSError, sqlite3.Error, ValueError, TypeError) as exc:
        raise PolicyDataUnavailable("정책 데이터 형식과 적재 상태를 확인해야 합니다.") from exc
