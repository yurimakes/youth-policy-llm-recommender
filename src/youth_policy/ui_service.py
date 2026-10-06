"""ui_service.py

Streamlit UI에서 사용할 정책 로딩과 평가 서비스를 제공합니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from youth_policy.matching import PolicyEvaluationBatch, UserProfile, evaluate_policies
from youth_policy.models import PolicyRecord
from youth_policy.sqlite_store import connect_database, list_policies


DEFAULT_POLICY_DB_PATH = Path("data") / "processed" / "policies.sqlite3"


class PolicyServiceError(RuntimeError):
    """정책 UI 서비스에서 복구 가능한 오류가 발생했음을 나타냅니다."""


@dataclass(frozen=True)
class PolicyEvaluationSummary:
    policies: tuple[PolicyRecord, ...]
    batch: PolicyEvaluationBatch

    @property
    def total_count(self) -> int:
        return len(self.policies)


def load_policies_from_sqlite(db_path: str | Path) -> tuple[PolicyRecord, ...]:
    database = Path(db_path)
    if not database.exists():
        raise PolicyServiceError(f"SQLite database not found: {database}")

    try:
        connection = connect_database(database)
        try:
            return tuple(list_policies(connection))
        finally:
            connection.close()
    except OSError as exc:
        raise PolicyServiceError("Could not open SQLite database.") from exc


def evaluate_sqlite_policies(
    *,
    db_path: str | Path,
    age: int | None,
    region_code: str | None,
    employment_status: str | None,
) -> PolicyEvaluationSummary:
    policies = load_policies_from_sqlite(db_path)
    profile = UserProfile(
        age=age,
        region_code=_clean_optional_text(region_code),
        employment_status=_clean_optional_text(employment_status),
    )
    return PolicyEvaluationSummary(
        policies=policies,
        batch=evaluate_policies(policies, profile),
    )


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None
