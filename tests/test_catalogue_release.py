"""실패한 수집·변조·부분 교체가 운영 DB를 손상하지 않는지 합성 데이터로 검사합니다."""

from datetime import date, datetime
import json
import sqlite3
from pathlib import Path
import sys
from unittest.mock import patch
from contextlib import nullcontext

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from test_collection import FakePageFetcher, make_payload, make_policy_item
from test_intake import policy
from release_policy_catalogue import main
from youth_policy.api_app import create_app
from youth_policy.api_config import ApiSettings
from youth_policy.catalogue_release import (
    CatalogueReleaseError, file_sha256, prepare_catalogue, publish_catalogue, restore_database,
)
from youth_policy.policy_repository import load_policies_readonly
from youth_policy.sqlite_store import connect_database, initialize_database, upsert_policies

TODAY = date(2026, 10, 13)
CLOCK = datetime(2026, 10, 13)


def snapshot(directory, name="source.json", ids=("TEST-ONLY",), **overrides):
    path = directory / name
    path.write_text(json.dumps(make_payload(page_num=1, total_count=len(ids), items=[make_policy_item(
        policy_id, **{"aplyUrlAddr":"https://example.test/official", **overrides}) for policy_id in ids])), encoding="utf-8")
    return path


def current_database(path):
    connection = connect_database(path)
    try:
        initialize_database(connection)
        upsert_policies(connection, (policy(),))
    finally:
        connection.close()
    return file_sha256(path)


def prepared(tmp_path, **overrides):
    source = snapshot(tmp_path, **overrides)
    result = prepare_catalogue(tmp_path / "staging", snapshots=[source], reference_date=TODAY, verified_at=CLOCK)
    return Path(result["directory"]), result["database_sha256"]


def publish(directory, digest, destination, current, **kwargs):
    return publish_catalogue(directory, destination, expected_candidate_sha256=digest,
                             expected_current_sha256=current, reference_date=TODAY, **kwargs)


def test_prepare_multiple_snapshots_keeps_active_db_and_originals_untouched(tmp_path):
    destination = tmp_path / "active.sqlite3"
    previous = current_database(destination)
    sources = [snapshot(tmp_path, "one.json", ("ONE",)), snapshot(tmp_path, "two.json", ("TWO",))]
    original = [source.read_bytes() for source in sources]
    result = prepare_catalogue(tmp_path / "staging", snapshots=sources, minimum_policies=2,
                               reference_date=TODAY, verified_at=CLOCK)
    directory = Path(result["directory"])
    audit = json.loads((directory / "audit.json").read_text(encoding="utf-8"))
    assert audit["trace_counts"]["matched"] == 2 and not audit["evidence_blockers"]
    assert result["policy_count"] == 2 and result["source"]["input_rows"] == 2
    assert [source.read_bytes() for source in sources] == original and file_sha256(destination) == previous


@pytest.mark.parametrize("failure", ["network", "malformed", "duplicate", "empty", "missing_url", "too_small"])
def test_failed_prepare_never_touches_active_db_or_emits_release_receipt(tmp_path, failure):
    destination = tmp_path / "active.sqlite3"; previous = current_database(destination)
    source = snapshot(tmp_path)
    options = {"snapshots": [source]}
    if failure == "malformed": source.write_text("PRIVATE-MALFORMED", encoding="utf-8")
    if failure == "duplicate": options["snapshots"] = [source, source]
    if failure == "empty": source = snapshot(tmp_path, ids=()); options["snapshots"] = [source]
    if failure == "missing_url": source = snapshot(tmp_path, aplyUrlAddr=""); options["snapshots"] = [source]
    if failure == "too_small": options["minimum_policies"] = 2
    if failure == "network":
        fetcher = FakePageFetcher({1:make_payload(page_num=1)}, fail_on_page=2)
        options = {"api_key":"PRIVATE-KEY", "fetch_page":fetcher}
    with pytest.raises(CatalogueReleaseError) as caught:
        prepare_catalogue(tmp_path / "staging", reference_date=TODAY, verified_at=CLOCK, **options)
    assert "PRIVATE" not in str(caught.value)
    assert file_sha256(destination) == previous
    assert not list((tmp_path / "staging").glob("*/release.json"))


def test_complete_mock_collection_has_page_scope_and_no_secret_in_receipt(tmp_path):
    fetcher = FakePageFetcher({page:make_payload(page_num=page,items=[make_policy_item(f"ID-{page}-{n}",
              aplyUrlAddr="https://example.test/official") for n in range(10)]) for page in (1,2)})
    result = prepare_catalogue(tmp_path / "staging", api_key="PRIVATE-KEY", fetch_page=fetcher,
                               minimum_policies=20, reference_date=TODAY, verified_at=CLOCK)
    assert result["policy_count"] == 20 and result["source"]["pages"] == [1,2]
    assert "PRIVATE-KEY" not in (Path(result["directory"])/"release.json").read_text(encoding="utf-8")


def test_publish_backup_restore_and_actual_api_reloads_the_replaced_db(tmp_path):
    destination = tmp_path / "active.sqlite3"; previous = current_database(destination)
    directory, digest = prepared(tmp_path)
    with TestClient(create_app(settings=ApiSettings(destination), date_provider=lambda:TODAY)) as client:
        def api_name():
            result = client.post("/api/v1/intake/start", json={"start_mode":"goal"}).json()
            for action in ({"type":"choose_card","key":"goal","value":"housing"}, {"type":"show_results"}):
                response = client.post("/api/v1/intake/transition", json={"state":result["state"],"action":action})
                assert response.status_code == 200
                result = response.json()
            return result["candidates"][0]["policy_name"]
        assert api_name() == policy().policy_name
        assert client.get("/ready").json()["policy_count"] == 1
        before = client.post("/api/v1/intake/start", json={}).json()
        card = {"type":"choose_card","key":"situation","value":"resting"}
        client.post("/api/v1/intake/transition", json={"state":before["state"],"action":card})
        result = publish(directory, digest, destination, previous)
        assert file_sha256(destination) == digest and file_sha256(Path(result["backup"])) == previous
        assert load_policies_readonly(destination)[0].policy_name == "Policy TEST-ONLY"
        assert api_name() == "Policy TEST-ONLY"
        assert client.get("/ready").status_code == 200
        restored = restore_database(Path(result["backup"]), destination, expected_backup_sha256=previous,
                                     expected_current_sha256=digest)
        assert file_sha256(destination) == previous
        assert file_sha256(Path(restored["backup"])) == digest
        assert load_policies_readonly(destination)[0].policy_name == policy().policy_name
        assert api_name() == policy().policy_name


@pytest.mark.parametrize("failure", ["changed_current", "changed_candidate", "changed_snapshot", "path_escape",
                                     "missing_receipt", "replace_error", "lock", "sidecar", "candidate_sidecar"])
def test_publish_rejection_preserves_current_database(tmp_path, failure):
    destination = tmp_path / "active.sqlite3"; previous = current_database(destination)
    directory, digest = prepared(tmp_path)
    expected_current = previous
    if failure == "changed_current": expected_current = "0"*64
    if failure == "changed_candidate": (directory/"candidate.sqlite3").write_bytes(b"tampered")
    if failure == "changed_snapshot": (directory/"raw/snapshot-1.json").write_text("{}", encoding="utf-8")
    if failure == "path_escape":
        manifest = json.loads((directory/"release.json").read_text(encoding="utf-8"))
        manifest["snapshots"][0]["path"] = "../../source.json"
        (directory/"release.json").write_text(json.dumps(manifest), encoding="utf-8")
    if failure == "missing_receipt": (directory/"release.json").unlink()
    if failure == "lock": Path(str(destination)+".release-lock").touch()
    if failure == "sidecar": Path(str(destination)+"-wal").touch()
    if failure == "candidate_sidecar": (directory/"candidate.sqlite3-wal").touch()
    with patch("youth_policy.catalogue_release.os.replace", side_effect=PermissionError("PRIVATE-ERROR")) if failure == "replace_error" else nullcontext():
        with pytest.raises(CatalogueReleaseError) as caught:
            publish(directory, digest, destination, expected_current)
    assert "PRIVATE" not in str(caught.value) and file_sha256(destination) == previous
    assert not list(tmp_path.glob("catalogue-install-*"))


def test_partial_catalogue_removal_requires_explicit_choice(tmp_path):
    destination = tmp_path / "active.sqlite3"; previous = current_database(destination)
    directory, digest = prepared(tmp_path, ids=("DIFFERENT",))
    with pytest.raises(CatalogueReleaseError, match="policy_removals"):
        publish(directory, digest, destination, previous)
    assert file_sha256(destination) == previous
    result = publish(directory, digest, destination, previous, allow_removals=True)
    assert result["previous_sha256"] == previous and file_sha256(destination) == digest


def test_first_install_requires_missing_and_restore_requires_matching_hash(tmp_path):
    directory, digest = prepared(tmp_path); destination = tmp_path / "active.sqlite3"
    with pytest.raises(CatalogueReleaseError): publish(directory, digest, destination, "0"*64)
    assert not destination.exists()
    result = publish(directory, digest, destination, "missing")
    assert result["backup"] is None and result["previous_sha256"] == "missing"
    with pytest.raises(CatalogueReleaseError):
        restore_database(directory/"candidate.sqlite3", destination, expected_backup_sha256="0"*64,
                         expected_current_sha256=digest)
    assert file_sha256(destination) == digest


def test_cli_does_not_echo_invalid_source_or_private_provider_error(tmp_path, capsys):
    invalid = tmp_path / "PRIVATE-PATH.json"; invalid.write_text("PRIVATE-KEY", encoding="utf-8")
    assert main(["prepare","--snapshot",str(invalid),"--workspace",str(tmp_path/"staging")]) == 2
    output = capsys.readouterr()
    assert not output.out and "PRIVATE" not in output.err
    with patch("release_policy_catalogue.get_ontong_api_key",return_value="PRIVATE-KEY"), \
         patch("release_policy_catalogue.prepare_catalogue",side_effect=RuntimeError("PRIVATE-KEY")):
        assert main(["prepare","--collect","--workspace",str(tmp_path/"staging")]) == 2
    assert "PRIVATE" not in capsys.readouterr().err


def test_cli_inspect_missing_does_not_create_database(tmp_path, capsys):
    path=tmp_path/"missing.sqlite3"
    assert main(["inspect","--db",str(path)]) == 0
    assert json.loads(capsys.readouterr().out)["database_sha256"] == "missing"
    assert not path.exists()


def test_recomputed_db_hash_does_not_bypass_original_row_comparison(tmp_path):
    destination=tmp_path/"active.sqlite3";previous=current_database(destination)
    directory,digest=prepared(tmp_path)
    with sqlite3.connect(directory/"candidate.sqlite3") as connection:
        connection.execute("UPDATE policies SET required_documents = 'INVENTED DOCUMENT'")
    updated=file_sha256(directory/"candidate.sqlite3")
    manifest=json.loads((directory/"release.json").read_text(encoding="utf-8"))
    manifest["database_sha256"]=updated
    (directory/"release.json").write_text(json.dumps(manifest),encoding="utf-8")
    with pytest.raises(CatalogueReleaseError,match="audit_rejected"):
        publish(directory,updated,destination,previous)
    assert file_sha256(destination)==previous


def test_future_processing_clock_is_not_publishable(tmp_path):
    source=snapshot(tmp_path)
    with pytest.raises(CatalogueReleaseError,match="future_processing_timestamp"):
        prepare_catalogue(tmp_path/"staging",snapshots=[source],reference_date=TODAY,
                           verified_at=datetime(2026,10,14))
    assert not list((tmp_path/"staging").glob("*/release.json"))


def test_lock_cleanup_warning_does_not_misreport_committed_publication(tmp_path):
    destination=tmp_path/"active.sqlite3";previous=current_database(destination)
    directory,digest=prepared(tmp_path)
    unlink=Path.unlink
    def fail_lock_cleanup(path, *args, **kwargs):
        if path.name.endswith(".release-lock"):
            raise PermissionError("PRIVATE-ERROR")
        return unlink(path,*args,**kwargs)
    with patch.object(Path,"unlink",fail_lock_cleanup):
        result=publish(directory,digest,destination,previous)
    assert file_sha256(destination)==digest
    assert result["warnings"]==["release_lock_retained"]
