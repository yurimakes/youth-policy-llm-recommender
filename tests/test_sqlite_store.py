"""test_sqlite_store.py

SQLite 저장소의 PolicyRecord 저장과 조회 동작을 테스트합니다.
"""

from dataclasses import replace
from datetime import date, datetime
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from youth_policy.models import ApplicationStatus
from youth_policy.ontong_parser import parse_policy_page
from youth_policy.sqlite_store import (
    connect_database,
    count_policies,
    get_policy_by_id,
    initialize_database,
    list_policies,
    upsert_policies,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "ontong_youth_policy_page1.json"
VERIFIED_AT = datetime(2026, 6, 29, 0, 0, 0)
REFERENCE_DATE = date(2026, 6, 29)


def load_fixture() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def parse_fixture():
    return parse_policy_page(
        load_fixture(),
        verified_at=VERIFIED_AT,
        reference_date=REFERENCE_DATE,
    )


def test_sqlite_store_round_trips_policy_records(tmp_path):
    db_path = tmp_path / "policies.sqlite3"
    records = parse_fixture()
    first_record = records[0]

    connection = connect_database(db_path)
    try:
        initialize_database(connection)

        foreign_keys = connection.execute("PRAGMA foreign_keys").fetchone()[0]
        assert foreign_keys == 1
        assert len(records) == 10

        assert upsert_policies(connection, records) == 10
        assert count_policies(connection) == 10

        assert upsert_policies(connection, records) == 10
        assert count_policies(connection) == 10

        stored_first = get_policy_by_id(connection, first_record.policy_id)
        assert stored_first == first_record
        assert isinstance(stored_first.application_start, date)
        assert isinstance(stored_first.application_end, date)
        assert isinstance(stored_first.last_verified_at, datetime)
        assert isinstance(stored_first.application_status, ApplicationStatus)

        listed_records = list_policies(connection)
        assert len(listed_records) == 10
        assert [record.policy_id for record in listed_records] == sorted(
            record.policy_id for record in records
        )

        updated_summary = "Updated summary for SQLite upsert test."
        updated_first = replace(first_record, summary=updated_summary)
        assert upsert_policies(connection, [updated_first]) == 1
        assert count_policies(connection) == 10
        assert get_policy_by_id(connection, first_record.policy_id).summary == (
            updated_summary
        )

        assert get_policy_by_id(connection, "missing-policy-id") is None
        assert upsert_policies(connection, []) == 0
    finally:
        connection.close()
