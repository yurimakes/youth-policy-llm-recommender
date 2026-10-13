"""격리된 정책 DB를 감사하고, 해시 확인·백업 후 원자적으로 배포합니다."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any, Iterable, Iterator

from youth_policy.api_config import korea_today
from youth_policy.collection import FetchPage, collect_ontong_policy_pages
from youth_policy.data_audit import audit_database
from youth_policy.ontong_client import fetch_ontong_policies
from youth_policy.ontong_parser import parse_policy_page
from youth_policy.policy_repository import load_policies_readonly
from youth_policy.sqlite_store import connect_database, initialize_database, upsert_policies


class CatalogueReleaseError(RuntimeError):
    """고정 오류 코드만 제공하며 원문·키·외부 오류 메시지를 노출하지 않습니다."""


def file_sha256(path: Path) -> str:
    """파일을 스트리밍으로 해시하며 없는 파일은 생성하지 않습니다."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _check_audit(audit: dict[str, Any], minimum_policies: int) -> None:
    if audit["evidence_blockers"] or audit["policy_count"] < minimum_policies:
        raise CatalogueReleaseError("audit_rejected")
    if audit["processing_age_days"]["future_timestamp_count"]:
        raise CatalogueReleaseError("future_processing_timestamp")
    if sum(row["row_count"] for row in audit["snapshots"]) != audit["policy_count"]:
        raise CatalogueReleaseError("duplicate_policy_id")


def prepare_catalogue(
    workspace: Path, *, snapshots: Iterable[Path] = (), api_key: str | None = None,
    minimum_policies: int = 1, page_size: int = 10, max_pages: int = 2,
    timeout: float = 10.0, fetch_page: FetchPage = fetch_ontong_policies,
    reference_date: date | None = None, verified_at: datetime | None = None,
) -> dict[str, Any]:
    """새 세대 디렉터리에서만 적재합니다. 실패한 세대에는 release.json이 없습니다."""
    inputs = tuple(Path(path) for path in snapshots)
    if bool(inputs) == (api_key is not None) or type(minimum_policies) is not int or minimum_policies < 1:
        raise CatalogueReleaseError("invalid_preparation_options")
    today = reference_date or korea_today()
    clock = verified_at or datetime.now(timezone.utc).replace(tzinfo=None)
    workspace.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="catalogue-", dir=workspace.resolve()))
    raw = directory / "raw"
    raw.mkdir()
    database = directory / "candidate.sqlite3"
    try:
        if inputs:
            paths = []
            records = []
            for number, snapshot in enumerate(inputs, 1):
                copied = raw / f"snapshot-{number}.json"
                shutil.copyfile(snapshot, copied)
                payload = json.loads(copied.read_text(encoding="utf-8-sig"))
                if not isinstance(payload, dict) or payload.get("resultCode") != 200:
                    raise CatalogueReleaseError("invalid_snapshot")
                parsed = tuple(parse_policy_page(payload, verified_at=clock, reference_date=today))
                if not parsed:
                    raise CatalogueReleaseError("empty_snapshot")
                paths.append(copied)
                records.extend(parsed)
            if len({p.policy_id for p in records}) != len(records):
                raise CatalogueReleaseError("duplicate_policy_id")
            connection = connect_database(database)
            try:
                initialize_database(connection)
                upsert_policies(connection, records)
            finally:
                connection.close()
            source = {"mode": "snapshots", "input_rows": len(records)}
        else:
            collected = collect_ontong_policy_pages(
                api_key=api_key, db_path=database, output_dir=raw, page_size=page_size,
                max_pages=max_pages, timeout=timeout, fetch_page=fetch_page,
                reference_date=today, verified_at=clock)
            paths = [p.raw_path for p in collected.page_summaries]
            source = {"mode": "collection", "pages": list(collected.fetched_pages),
                      "input_rows": collected.fetched_policies, "total_available": collected.total_available}
        audit = audit_database(database, reference_date=today, snapshot_paths=paths)
        _write_json(directory / "audit.json", audit)
        _check_audit(audit, minimum_policies)
        manifest = {"release_version": "1", "database_sha256": file_sha256(database),
                    "policy_count": audit["policy_count"], "minimum_policies": minimum_policies,
                    "prepared_at": clock.isoformat(), "reference_date": today.isoformat(), "source": source,
                    "snapshots": [{"path": str(path.relative_to(directory)).replace("\\", "/"),
                                   "sha256": file_sha256(path)} for path in paths],
                    "notice": "원본·정규화 연결 검사이며 공식 공고 최신성·이용허락·G2 통과를 보장하지 않습니다."}
        _write_json(directory / "release.json", manifest)
        return {"directory": str(directory), **manifest}
    except CatalogueReleaseError:
        raise
    except Exception as exc:
        raise CatalogueReleaseError("preparation_failed") from exc


def _hash_value(value: str, *, allow_missing: bool = False) -> None:
    if not isinstance(value, str) or (not re.fullmatch(r"[0-9a-f]{64}", value)
                                   and not (allow_missing and value == "missing")):
        raise CatalogueReleaseError("invalid_expected_hash")


def _current_hash(destination: Path) -> str:
    if destination.is_symlink():
        raise CatalogueReleaseError("symlink_destination")
    for suffix in ("-wal", "-shm", "-journal"):
        if Path(str(destination) + suffix).exists():
            raise CatalogueReleaseError("active_sqlite_sidecar")
    return file_sha256(destination) if destination.exists() else "missing"


@contextmanager
def _release_lock(destination: Path) -> Iterator[list[str]]:
    lock = destination.with_name(destination.name + ".release-lock")
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise CatalogueReleaseError("release_locked") from exc
    warnings: list[str] = []
    try:
        os.close(descriptor)
        yield warnings
    finally:
        try:
            lock.unlink()
        except OSError:
            # A cleanup failure after os.replace must not misreport an already
            # committed replacement as a failed publication.
            warnings.append("release_lock_retained")


def _install_database(source: Path, destination: Path, *, expected_source_sha256: str,
                      expected_current_sha256: str) -> dict[str, Any]:
    _hash_value(expected_source_sha256)
    _hash_value(expected_current_sha256, allow_missing=True)
    if source.resolve() == destination.resolve():
        raise CatalogueReleaseError("same_database")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with _release_lock(destination) as warnings:
        current = _current_hash(destination)
        if current != expected_current_sha256:
            raise CatalogueReleaseError("current_database_changed")
        if _current_hash(source) != expected_source_sha256:
            raise CatalogueReleaseError("candidate_database_changed")
        if not load_policies_readonly(source):
            raise CatalogueReleaseError("empty_database")
        backup = None
        permissions = destination.stat() if current != "missing" else source.stat()
        if current != "missing":
            backup_directory = Path(tempfile.mkdtemp(prefix="catalogue-backup-", dir=destination.parent))
            backup = backup_directory / "previous.sqlite3"
            shutil.copyfile(destination, backup)
            if file_sha256(backup) != current:
                raise CatalogueReleaseError("current_database_changed")
        descriptor, name = tempfile.mkstemp(prefix="catalogue-install-", suffix=".sqlite3", dir=destination.parent)
        staged = Path(name)
        try:
            with os.fdopen(descriptor, "wb") as target, source.open("rb") as candidate:
                shutil.copyfileobj(candidate, target)
                target.flush()
                os.fsync(target.fileno())
            os.chmod(staged, permissions.st_mode & 0o777)
            if os.name == "posix" and current != "missing":
                os.chown(staged, permissions.st_uid, permissions.st_gid)
            if file_sha256(staged) != expected_source_sha256:
                raise CatalogueReleaseError("candidate_database_changed")
            if _current_hash(destination) != current:
                raise CatalogueReleaseError("current_database_changed")
            os.replace(staged, destination)
        finally:
            try:
                staged.unlink(missing_ok=True)
            except PermissionError:
                try:
                    os.chmod(staged, 0o600)
                    staged.unlink(missing_ok=True)
                except OSError:
                    warnings.append("install_temp_retained")
            except OSError:
                warnings.append("install_temp_retained")
        return {"database_sha256": expected_source_sha256, "previous_sha256": current,
                "backup": str(backup) if backup else None, "warnings": warnings}


def publish_catalogue(directory: Path, destination: Path, *, expected_candidate_sha256: str,
                      expected_current_sha256: str, allow_removals: bool = False,
                      reference_date: date | None = None) -> dict[str, Any]:
    """해시·원본 행·최소 건수를 다시 검사하고 삭제 정책은 명시적 옵션으로만 허용합니다."""
    try:
        _hash_value(expected_candidate_sha256)
        root = directory.resolve()
        manifest = json.loads((root / "release.json").read_text(encoding="utf-8"))
        if manifest["release_version"] != "1" or manifest["database_sha256"] != expected_candidate_sha256:
            raise CatalogueReleaseError("candidate_database_changed")
        minimum = manifest["minimum_policies"]
        if type(minimum) is not int or minimum < 1:
            raise CatalogueReleaseError("invalid_manifest")
        snapshots = []
        for entry in manifest["snapshots"]:
            path = (root / entry["path"]).resolve()
            if root not in path.parents or not path.is_file() or file_sha256(path) != entry["sha256"]:
                raise CatalogueReleaseError("snapshot_changed")
            snapshots.append(path)
        database = root / "candidate.sqlite3"
        if _current_hash(database) != expected_candidate_sha256:
            raise CatalogueReleaseError("candidate_database_changed")
        audit = audit_database(database, reference_date=reference_date or korea_today(), snapshot_paths=snapshots)
        _check_audit(audit, minimum)
        if destination.exists() and not allow_removals:
            previous_ids = {p.policy_id for p in load_policies_readonly(destination)}
            next_ids = {p["policy_id"] for p in audit["policies"]}
            if previous_ids - next_ids:
                raise CatalogueReleaseError("policy_removals_require_explicit_option")
        return _install_database(database, destination, expected_source_sha256=expected_candidate_sha256,
                                 expected_current_sha256=expected_current_sha256)
    except CatalogueReleaseError:
        raise
    except Exception as exc:
        raise CatalogueReleaseError("publication_failed") from exc


def restore_database(backup: Path, destination: Path, *, expected_backup_sha256: str,
                     expected_current_sha256: str) -> dict[str, Any]:
    """기록한 백업 해시와 현재 해시가 일치할 때 이전 DB를 복구하며 현재 DB도 백업합니다."""
    try:
        return _install_database(backup, destination, expected_source_sha256=expected_backup_sha256,
                                 expected_current_sha256=expected_current_sha256)
    except CatalogueReleaseError:
        raise
    except Exception as exc:
        raise CatalogueReleaseError("restore_failed") from exc
