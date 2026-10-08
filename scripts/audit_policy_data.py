"""Read-only policy coverage and snapshot provenance audit CLI."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import sys
from typing import Sequence

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from youth_policy.api_config import korea_today
from youth_policy.data_audit import audit_database
from youth_policy.policy_repository import PolicyDataUnavailable


def main(argv: Sequence[str] | None = None) -> int:
    """Return 0 for a measured audit, 2 for invalid input, 3 for strict blockers."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, action="append", default=[])
    parser.add_argument("--reference-date", type=date.fromisoformat, default=korea_today())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--strict", action="store_true",
                        help="Fail on empty data, unusable URLs or missing/mismatched raw traces.")
    args = parser.parse_args(argv)
    try:
        if args.output and args.output.resolve() in {
            args.db.resolve(), *(path.resolve() for path in args.snapshot)
        }:
            raise ValueError("Output must not overwrite the database or a source snapshot.")
        report = audit_database(args.db, reference_date=args.reference_date,
                                snapshot_paths=args.snapshot)
        content = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(content, encoding="utf-8")
        else:
            print(content, end="")
        return 3 if args.strict and report["evidence_blockers"] else 0
    except (OSError, ValueError, TypeError, AttributeError, PolicyDataUnavailable):
        print("Audit failed: check the database, snapshot schema and output path.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
