"""test_intake_integration.py

기존 공식 예시 파서·SQLite와 신규 진행 로직을 함께 검증합니다.
"""

from dataclasses import replace
from datetime import date, datetime
from io import StringIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from preview_intake import load_read_only, preview
from youth_policy.intake import answer_fact, choose_card, start_intake
from youth_policy.intake_service import build_guidance
from youth_policy.models import ApplicationStatus
from youth_policy.ontong_parser import parse_policy_page
from youth_policy.sqlite_store import connect_database, initialize_database, upsert_policies


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        payload = json.loads(
            (Path(__file__).parent / "fixtures/ontong_youth_policy_page1.json").read_text(encoding="utf-8")
        )
        self.records = parse_policy_page(payload, verified_at=datetime(2026, 6, 28),
                                         reference_date=date(2026, 6, 28))
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.database = Path(self.temp.name) / "policies.sqlite3"
        connection = connect_database(self.database)
        initialize_database(connection)
        upsert_policies(connection, self.records)
        connection.close()

    def test_existing_fixture_roundtrips_into_new_guidance(self):
        loaded = load_read_only(self.database)
        self.assertEqual(len(loaded), len(self.records))
        state = choose_card(start_intake("goal"), "goal", "unknown")
        expected = {record.policy_id: record for record in loaded}
        results = build_guidance(loaded, state, reference_date=date(2026, 6, 28))
        self.assertGreater(len(results), 0)
        for result in results:
            self.assertEqual(result.policy_name, expected[result.policy_id].policy_name)
            self.assertEqual(result.last_verified_at, expected[result.policy_id].last_verified_at)

    def test_no_user_answers_written_to_existing_database(self):
        original_bytes = self.database.read_bytes()
        loaded = load_read_only(self.database)
        state = choose_card(start_intake("goal"), "goal", "housing")
        state = answer_fact(state, "age", 24)
        build_guidance(loaded, state, reference_date=date(2026, 10, 7))
        self.assertEqual(self.database.read_bytes(), original_bytes)

    def test_missing_database_is_not_created(self):
        missing = Path(self.temp.name) / "missing.sqlite3"
        with self.assertRaises(ValueError):
            load_read_only(missing)
        self.assertFalse(missing.exists())

    def test_cli_decline_detail_keeps_official_guidance(self):
        # Adjust a fixture only inside this test to isolate the flow from old policy periods.
        record = replace(self.records[0], application_start=date.today(), application_end=date.today(),
                         application_status=ApplicationStatus.OPEN, age_min=19, age_max=34,
                         region_code="11680", employment_status="미취업자")
        with patch("builtins.input", side_effect=["3", "1", "24", "11680", "1", ""]), \
             patch("sys.stdout", new_callable=StringIO) as output:
            preview((record,), "situation")
        text = output.getvalue()
        self.assertIn(record.policy_name, text)
        self.assertIn("사용자 입력 부족", text)
        self.assertIn("공식 링크", text)

    def test_cli_detail_answer_can_exclude_previous_candidate(self):
        record = replace(self.records[0], application_start=date.today(), application_end=date.today(),
                         application_status=ApplicationStatus.OPEN, age_min=19, age_max=34,
                         region_code="11680", employment_status="미취업자")
        with patch("builtins.input", side_effect=["3", "1", "24", "11680", "1", "y", "재직자"]), \
             patch("sys.stdout", new_callable=StringIO) as output:
            preview((record,), "situation")
        self.assertIn("명확한 불일치", output.getvalue())


if __name__ == "__main__":
    unittest.main()
