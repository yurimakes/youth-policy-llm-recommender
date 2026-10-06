"""sqlite_store.py

PolicyRecord를 SQLite에 저장하고 조회하는 최소 저장소 함수를 제공합니다.
"""

from __future__ import annotations

import sqlite3
from dataclasses import fields
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

from youth_policy.models import ApplicationStatus, PolicyRecord


POLICY_FIELDS = tuple(field.name for field in fields(PolicyRecord))


def connect_database(db_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS policies (
            policy_id TEXT PRIMARY KEY,
            policy_name TEXT NOT NULL,
            category TEXT,
            summary TEXT,
            region_code TEXT,
            region_name TEXT,
            age_min INTEGER,
            age_max INTEGER,
            income_condition TEXT,
            employment_status TEXT,
            education_status TEXT,
            application_start TEXT,
            application_end TEXT,
            application_status TEXT NOT NULL,
            eligibility_text TEXT,
            benefit_text TEXT,
            application_method TEXT,
            required_documents TEXT,
            contact TEXT,
            source_name TEXT NOT NULL,
            source_url TEXT,
            last_verified_at TEXT NOT NULL,
            embedding_text TEXT NOT NULL
        )
        """
    )
    connection.commit()


def upsert_policies(
    connection: sqlite3.Connection, records: Iterable[PolicyRecord]
) -> int:
    columns = ", ".join(POLICY_FIELDS)
    placeholders = ", ".join(f":{field_name}" for field_name in POLICY_FIELDS)
    update_clause = ", ".join(
        f"{field_name} = excluded.{field_name}"
        for field_name in POLICY_FIELDS
        if field_name != "policy_id"
    )
    sql = (
        f"INSERT INTO policies ({columns}) VALUES ({placeholders}) "
        f"ON CONFLICT(policy_id) DO UPDATE SET {update_clause}"
    )
    values = [_record_to_row(record) for record in records]
    if not values:
        return 0

    try:
        connection.executemany(sql, values)
        connection.commit()
    except Exception:
        connection.rollback()
        raise

    return len(values)


def count_policies(connection: sqlite3.Connection) -> int:
    row = connection.execute("SELECT COUNT(*) AS policy_count FROM policies").fetchone()
    return int(row["policy_count"])


def get_policy_by_id(
    connection: sqlite3.Connection, policy_id: str
) -> PolicyRecord | None:
    row = connection.execute(
        "SELECT * FROM policies WHERE policy_id = ?", (policy_id,)
    ).fetchone()
    if row is None:
        return None
    return _row_to_record(row)


def list_policies(connection: sqlite3.Connection) -> list[PolicyRecord]:
    rows = connection.execute("SELECT * FROM policies ORDER BY policy_id").fetchall()
    return [_row_to_record(row) for row in rows]


def _record_to_row(record: PolicyRecord) -> dict[str, object]:
    row: dict[str, object] = {}
    for field_name in POLICY_FIELDS:
        value = getattr(record, field_name)
        if isinstance(value, ApplicationStatus):
            row[field_name] = value.value
        elif isinstance(value, (date, datetime)):
            row[field_name] = value.isoformat()
        else:
            row[field_name] = value
    return row


def _row_to_record(row: sqlite3.Row) -> PolicyRecord:
    data = {field_name: row[field_name] for field_name in POLICY_FIELDS}
    if data["application_start"] is not None:
        data["application_start"] = date.fromisoformat(data["application_start"])
    if data["application_end"] is not None:
        data["application_end"] = date.fromisoformat(data["application_end"])
    data["application_status"] = ApplicationStatus(data["application_status"])
    data["last_verified_at"] = datetime.fromisoformat(data["last_verified_at"])
    return PolicyRecord(**data)
