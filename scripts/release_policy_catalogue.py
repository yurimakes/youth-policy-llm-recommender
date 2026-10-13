"""정책 DB 준비·검사·배포·복구 CLI입니다. 실제 사용자 입력은 사용하지 않습니다."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from youth_policy.catalogue_release import (
    CatalogueReleaseError, file_sha256, prepare_catalogue, publish_catalogue, restore_database,
)
from youth_policy.config import ConfigurationError, get_ontong_api_key


def main(argv: Sequence[str] | None = None) -> int:
    """성공 시 메타데이터만 출력합니다. 외부 오류나 키는 stderr에 출력하지 않습니다."""
    parser = argparse.ArgumentParser(description="Prepare, inspect and safely publish a policy SQLite catalogue.")
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    inputs = prepare.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--snapshot", action="append", type=Path)
    inputs.add_argument("--collect", action="store_true")
    prepare.add_argument("--workspace", type=Path, default=Path(".policy-evidence/catalogues"))
    prepare.add_argument("--minimum-policies", type=int, default=1)
    prepare.add_argument("--page-size", type=int, default=10)
    prepare.add_argument("--max-pages", type=int, default=2)
    prepare.add_argument("--timeout", type=float, default=10)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("--db", required=True, type=Path)
    publish = commands.add_parser("publish")
    publish.add_argument("--directory", required=True, type=Path)
    publish.add_argument("--allow-removals", action="store_true")
    publish.add_argument("--expected-candidate-sha256", required=True)
    restore = commands.add_parser("restore")
    restore.add_argument("--backup", required=True, type=Path)
    restore.add_argument("--expected-backup-sha256", required=True)
    for command in (publish, restore):
        command.add_argument("--db", required=True, type=Path)
        command.add_argument("--expected-current-sha256", required=True,
                             help="Reviewed current DB SHA-256, or missing for an initial installation.")
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            key = get_ontong_api_key(secrets_path=ROOT / ".streamlit/secrets.toml") if args.collect else None
            result = prepare_catalogue(args.workspace, snapshots=args.snapshot or (), api_key=key,
                                       minimum_policies=args.minimum_policies, page_size=args.page_size,
                                       max_pages=args.max_pages, timeout=args.timeout)
        elif args.command == "inspect":
            from youth_policy.api_config import korea_today
            from youth_policy.data_audit import audit_database
            if not args.db.exists():
                result = {"database_sha256": "missing"}
            else:
                audit = audit_database(args.db, reference_date=korea_today())
                result = {"database_sha256": file_sha256(args.db), "policy_count": audit["policy_count"],
                          "period_counts": audit["period_counts"], "processing_age_days": audit["processing_age_days"]}
        elif args.command == "publish":
            result = publish_catalogue(args.directory, args.db, expected_candidate_sha256=args.expected_candidate_sha256,
                                       expected_current_sha256=args.expected_current_sha256, allow_removals=args.allow_removals)
        else:
            result = restore_database(args.backup, args.db, expected_backup_sha256=args.expected_backup_sha256,
                                      expected_current_sha256=args.expected_current_sha256)
    except CatalogueReleaseError as exc:
        print(f"Catalogue operation failed: {exc}", file=sys.stderr)
        return 2
    except ConfigurationError:
        print("Catalogue operation failed: collection_key_unavailable", file=sys.stderr)
        return 2
    except Exception:
        print("Catalogue operation failed: invalid_input_or_io", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
