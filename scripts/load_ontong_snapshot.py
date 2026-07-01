"""load_ontong_snapshot.py

저장된 온통청년 snapshot을 SQLite DB로 적재하는 명령행 스크립트입니다.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from career_catch.pipeline import load_ontong_snapshot_to_sqlite


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Load a saved Ontong youth policy JSON snapshot into SQLite.",
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to a saved raw Ontong JSON snapshot.",
    )
    parser.add_argument(
        "--db",
        required=True,
        type=Path,
        help="SQLite database path to create or update.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    result = load_ontong_snapshot_to_sqlite(args.input, args.db)
    print(f"input_policies={result.parsed_count}")
    print(f"stored_policies={result.stored_count}")
    print(f"db={result.db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
