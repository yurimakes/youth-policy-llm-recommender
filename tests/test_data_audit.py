"""Check audit denominators, raw-source matching and read-only failure behavior."""

from dataclasses import replace
from datetime import date, datetime
import importlib.util
from io import StringIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from audit_policy_data import main
from youth_policy.data_audit import audit_database, audit_records
from youth_policy.models import ApplicationStatus
from youth_policy.ontong_parser import parse_policy_page
from youth_policy.policy_repository import PolicyDataUnavailable
from youth_policy.sqlite_store import connect_database, initialize_database, upsert_policies


FIXTURE = ROOT / "tests/fixtures/ontong_youth_policy_page1.json"
DAY = date(2026, 6, 28)


class DataAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.records = parse_policy_page(json.loads(FIXTURE.read_text(encoding="utf-8")),
                                         verified_at=datetime(2026, 6, 28), reference_date=DAY)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "policies.sqlite3"
        with connect_database(self.db) as connection:
            initialize_database(connection)
            upsert_policies(connection, self.records)
        connection.close()

    def test_existing_raw_rows_match_with_hashes_and_zero_based_positions(self) -> None:
        report = audit_database(self.db, reference_date=DAY, snapshot_paths=[FIXTURE])
        self.assertEqual(report["policy_count"], 10)
        self.assertEqual(report["trace_counts"]["matched"], 10)
        row = next(p for p in report["policies"] if p["policy_id"] == self.records[0].policy_id)
        self.assertEqual(row["source_rows"][0]["row_index"], 0)
        self.assertEqual(len(row["source_rows"][0]["snapshot_sha256"]), 64)

    def test_readonly_audit_does_not_modify_database(self) -> None:
        before = self.db.read_bytes()
        audit_database(self.db, reference_date=DAY, snapshot_paths=[FIXTURE])
        self.assertEqual(self.db.read_bytes(), before)

    def test_missing_db_is_not_created(self) -> None:
        missing = Path(self.temp.name) / "missing.sqlite3"
        with self.assertRaises(PolicyDataUnavailable):
            audit_database(missing, reference_date=DAY)
        self.assertFalse(missing.exists())

    def test_empty_catalogue_has_no_fake_full_coverage(self) -> None:
        report = audit_records((), reference_date=DAY)
        self.assertIsNone(report["field_coverage"]["age_min"]["ratio"])
        self.assertIn("empty_catalogue", report["evidence_blockers"])

    def test_whitespace_is_missing_but_zero_age_is_present(self) -> None:
        record = replace(self.records[0], summary="  ", age_min=0)
        report = audit_records([record], reference_date=DAY)
        self.assertEqual(report["field_coverage"]["summary"]["missing"], 1)
        self.assertEqual(report["field_coverage"]["age_min"]["present"], 1)

    def test_changed_normalized_value_is_not_a_verified_trace(self) -> None:
        changed = replace(self.records[0], age_min=20)
        report = audit_records([changed], reference_date=DAY, snapshot_paths=[FIXTURE])
        self.assertEqual(report["trace_counts"]["mismatch"], 1)
        self.assertIn("source_row_mismatch", report["evidence_blockers"])

    def test_missing_raw_id_and_no_raw_input_are_distinct(self) -> None:
        record = replace(self.records[0], policy_id="not-in-snapshot")
        with_raw = audit_records([record], reference_date=DAY, snapshot_paths=[FIXTURE])
        no_raw = audit_records([record], reference_date=DAY)
        self.assertEqual(with_raw["trace_counts"]["missing"], 1)
        self.assertEqual(no_raw["trace_counts"]["not_supplied"], 1)

    def test_multiple_raw_occurrences_do_not_inflate_policy_denominator(self) -> None:
        report = audit_records(self.records, reference_date=DAY, snapshot_paths=[FIXTURE, FIXTURE])
        self.assertEqual(report["policy_count"], 10)
        self.assertEqual(report["trace_counts"]["matched"], 10)
        self.assertEqual(len(report["policies"][0]["source_rows"]), 2)

    def test_duplicate_policy_ids_reject_ambiguous_denominator(self) -> None:
        with self.assertRaises(ValueError):
            audit_records([self.records[0], self.records[0]], reference_date=DAY)

    def test_malformed_snapshot_cannot_silently_skip_a_page(self) -> None:
        malformed = Path(self.temp.name) / "invalid.json"
        malformed.write_text('{"resultCode":200,"result":{}}', encoding="utf-8")
        with self.assertRaises(ValueError):
            audit_database(self.db, reference_date=DAY, snapshot_paths=[FIXTURE, malformed])

    def test_url_presence_is_not_url_usability_or_official_authenticity(self) -> None:
        for value in ("javascript:alert(1)", "https://user:secret@example.org", "https://example.org:bad", " "):
            with self.subTest(value=value):
                report = audit_records([replace(self.records[0], source_url=value)], reference_date=DAY)
                self.assertIn("unusable_source_url", report["evidence_blockers"])
        report = audit_records([replace(self.records[0], source_url="https://example.org/notice")],
                               reference_date=DAY)
        self.assertTrue(report["policies"][0]["source_url_usable"])

    def test_expired_dates_override_open_snapshot(self) -> None:
        record = replace(self.records[0], application_status=ApplicationStatus.OPEN)
        report = audit_records([record], reference_date=date(2026, 10, 8))
        self.assertEqual(report["period_counts"], {"closed": 1})
        self.assertEqual(report["policies"][0]["conditions_without_user_input"]["application"], "not_met")

    def test_future_dates_and_missing_period_are_not_open(self) -> None:
        future = replace(self.records[0], application_start=date(2026, 7, 1))
        unknown = replace(self.records[1], application_start=None, application_end=None,
                          application_status=ApplicationStatus.OPEN)
        report = audit_records([future, unknown], reference_date=DAY)
        self.assertEqual(report["period_counts"], {"not_started": 1, "unverified": 1})

    def test_input_order_does_not_change_report_or_catalogue_hash(self) -> None:
        left = audit_records(self.records, reference_date=DAY, snapshot_paths=[FIXTURE])
        right = audit_records(reversed(self.records), reference_date=DAY, snapshot_paths=[FIXTURE])
        self.assertEqual(left, right)

    def test_cli_strict_blockers_are_reported_and_return_nonzero(self) -> None:
        output = Path(self.temp.name) / "report.json"
        code = main(["--db", str(self.db), "--reference-date", DAY.isoformat(),
                     "--output", str(output), "--strict"])
        self.assertEqual(code, 3)
        self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["trace_counts"]["not_supplied"], 10)

    def test_cli_cannot_overwrite_database_or_raw_snapshot(self) -> None:
        before = self.db.read_bytes()
        with patch("sys.stderr", new_callable=StringIO):
            self.assertEqual(main(["--db", str(self.db), "--output", str(self.db)]), 2)
            self.assertEqual(main(["--db", str(self.db), "--snapshot", str(FIXTURE),
                                   "--output", str(FIXTURE)]), 2)
        self.assertEqual(self.db.read_bytes(), before)


@unittest.skipUnless(all(importlib.util.find_spec(name) for name in ("fastapi", "httpx")),
                     "Replay HTTP dependencies unavailable")
class OfflineReplayTests(unittest.TestCase):
    def test_example_pipeline_and_real_http_contract_are_reproducible(self) -> None:
        from replay_policy_api import replay
        original = FIXTURE.read_bytes()
        report = replay()
        self.assertEqual(report["data_kind"], "existing_example_snapshot_not_live_data")
        self.assertEqual(report["data_audit"]["trace_counts"]["matched"], 10)
        self.assertTrue(all(check["passed"] for check in report["checks"]))
        self.assertEqual(FIXTURE.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
